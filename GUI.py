import sys
import os
import requests
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QRadioButton,
                             QLabel, QTextEdit, QHBoxLayout, QFrame, QFormLayout, QFileDialog, QComboBox)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap
from LoginFunction import LoginFunction
from PermanentHeader import permanentHeader
from NextButton import NextButton

# This Stream class redirects sys.stdout to a PyQt signal.
# This allows us to capture print() statements and display them in the GUI.
class Stream(QObject):
    # Define a signal that will carry the log message
    newText = pyqtSignal(str)

    def write(self, text):
        # Emit the text received, but first strip any leading/trailing whitespace
        # to ensure there are no blank lines
        clean_text = text.strip()
        if clean_text:
            self.newText.emit(clean_text)

    def flush(self):
        # This method is required for the stream redirection
        pass

# --- NEW: A worker class to run the blocking login function in a separate thread. ---
# It inherits from QObject so it can use signals.
class LoginWorker(QObject):
    # Signal to report the result of the login attempt (True for success, False for failure)
    login_finished = pyqtSignal(bool, object, object)

    def __init__(self, basic_oauth, username, password, url):
        super().__init__()
        self.basic_oauth = basic_oauth
        self.username = username
        self.password = password
        self.url = url
        self.session = None
        self.csrf_token = None

    def run_login(self):
        """
        This method will be executed in the separate thread.
        It calls the potentially blocking LoginFunction.
        """
        print("Starting login process in a background thread...")
        try:
            self.session, self.csrf_token = LoginFunction(self.basic_oauth, self.username, self.password, self.url)
            login_successful = self.session is not None
            # Emit the result back to the main thread
            self.login_finished.emit(login_successful, self.session, self.csrf_token)
        except Exception as e:
            print(f"An error occurred during login: {e}")
            self.login_finished.emit(False, None, None)

# --- NEW: A worker class to fetch categories in a separate thread. ---
class FetchCategoriesWorker(QObject):
    categories_finished = pyqtSignal(list)

    def __init__(self, session, csrf_token, project_id):
        super().__init__()
        self.session = session
        self.csrf_token = csrf_token
        self.project_id = project_id

    def run_fetch(self):
        print(f"Fetching categories for project {self.project_id}...")
        try:
            categories = self.get_categories(self.session, self.csrf_token, self.project_id)
            self.categories_finished.emit(categories)
        except Exception as e:
            print(f"An error occurred while fetching categories: {e}")
            self.categories_finished.emit([])

    def get_categories(self, session, csrf_token, project_id):
        """Fetches categories from a Jama Connect project using the specified endpoint."""
        url = "https://pknowles.jamacloud.com/rest/v1/categories"
        params = {'projectId': project_id, 'startAt': 0, 'maxResults': 50}
        headers = {'accept': 'application/json', 'jama-csrf-token': csrf_token}

        try:
            print(f"Making GET request to: {url} with parameters: {params}")
            print(f"Using CSRF Token: {csrf_token}")
            response = session.get(url, params=params, headers=headers)
            
            response.raise_for_status()
            
            data = response.json().get('data', [])
            
            if not isinstance(data, list):
                print("Unexpected data format in API response.")
                return []
            
            print(f"Successfully retrieved Categories from {project_id}")
            
            # Change: Return a list of lists with category details
            categories_data = []
            for category in data:
                if 'path' in category and 'categoryName' in category and 'categoryPathId' in category:
                    categories_data.append([
                        category['path'],
                        category['categoryName'],
                        category['categoryPathId']
                    ])
            return categories_data
            
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error occurred: {e}")
            print("This could be due to a login failure, incorrect URL, invalid CSRF token, or a non-existent project.")
            return []
        except requests.exceptions.RequestException as e:
            print(f"An error occurred during the API request: {e}")
            return []
        except Exception as e:
            print(f"An unexpected error occurred while processing the response: {e}")
            return []

class AutoEmailGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PK's Auto Email Sender")
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        window_width = 800
        window_height = 600
        x = (screen_geometry.width() - window_width) // 2
        y = (screen_geometry.height() - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, 'PK_logo.png')
        self.setWindowIcon(QIcon(icon_path))

        self.main_app_layout = QVBoxLayout()
        self.setLayout(self.main_app_layout)

        header_layout, separator = permanentHeader("Auto Email Sender", 'email.png')
        self.main_app_layout.addLayout(header_layout)
        self.main_app_layout.addWidget(separator)

        self.dynamic_content_layout = QVBoxLayout()
        self.main_app_layout.addLayout(self.dynamic_content_layout)
        self.main_app_layout.addStretch()
        
        self.log_text_edit = None
        self.thread = None
        self.worker = None
        self.session = None
        self.csrf_token = None
        self.categories_data = [] # New list to store all category info

        self.Login()

    def setup_logging_section(self):
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setPlaceholderText("Logs will appear here...")
        self.log_text_edit.setStyleSheet("background-color: #333; color: #fff;")
        self.main_app_layout.addWidget(self.log_text_edit)

        sys.stdout = Stream()
        sys.stdout.newText.connect(self.append_log)
    
    def append_log(self, text):
        self.log_text_edit.append(text)

    def Login(self):
        print("Initializing login screen...")
        form_layout = QFormLayout()

        self.basic = QRadioButton("Basic")
        self.basic.setChecked(True)

        radio_button_layout = QHBoxLayout()
        radio_button_layout.addWidget(self.basic)
        radio_button_layout.addStretch()

        form_layout.addRow("Select Jama Connect Login Method:", radio_button_layout)

        self.submit_button = NextButton("Submit", True)

        self.dynamic_content_layout.addLayout(form_layout)
        self.dynamic_content_layout.addWidget(self.submit_button)
        self.dynamic_content_layout.addStretch()

        self.basic_oauth = 'basic' if self.basic.isChecked() else 'oauth'

        self.submit_button.clicked.connect(self.CheckLoginMethod)

    def CheckLoginMethod(self):
        print("Checking login method...")
        self.basic_oauth = 'basic' if self.basic.isChecked() else 'oauth'
        print(f"Selected login method: {self.basic_oauth}")

        self.clearLayout(self.dynamic_content_layout)
        self.setup_logging_section()

        if self.basic_oauth == 'basic':
            self.LoginForm("Username", "Password")
        else:
            self.LoginForm("Client ID", "Client Secret")

    def clearLayout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.clearLayout(item.layout())

    def LoginForm(self, UN, PW):
        print("Displaying login form...")
        self.form_layout = QFormLayout()

        self.Jama_label = QLabel("Jama Connect API Login Information")
        self.form_layout.addRow(self.Jama_label)

        self.username_label = QLabel(UN + ": ")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your " + UN)
        self.form_layout.addRow(self.username_label, self.username_input)

        self.password_label = QLabel(PW + ": ")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your " + PW)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(self.password_label, self.password_input)

        self.login_button = NextButton("Login", True)
        self.form_layout.addRow(self.login_button)

        self.login_button.clicked.connect(self.start_login_thread)

        self.dynamic_content_layout.addLayout(self.form_layout)
        self.dynamic_content_layout.addStretch()

    def start_login_thread(self):
        print("Initiating login...")
        self.login_button.setEnabled(False)
        
        username = self.username_input.text()
        password = self.password_input.text()
        url = "https://pknowles.jamacloud.com/rest/v1/"

        self.login_thread = QThread()
        self.login_worker = LoginWorker(self.basic_oauth, username, password, url)
        
        self.login_worker.moveToThread(self.login_thread)

        self.login_thread.started.connect(self.login_worker.run_login)
        self.login_worker.login_finished.connect(self.handle_login_result)
        self.login_worker.login_finished.connect(self.login_worker.deleteLater)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        self.login_thread.start()

    def handle_login_result(self, login_successful, session, csrf_token):
        self.login_button.setEnabled(True)
        self.login_thread.quit()
        self.login_thread.wait()

        if login_successful:
            self.session = session
            self.csrf_token = csrf_token
            
            print("Login successful!")
            self.clearLayout(self.dynamic_content_layout)
            project_id = 51
            
            self.start_fetch_categories_thread(project_id)
        else:
            print("Login failed. Please check your credentials and try again.")
            
    def start_fetch_categories_thread(self, project_id):
        self.fetch_thread = QThread()
        self.fetch_worker = FetchCategoriesWorker(self.session, self.csrf_token, project_id)

        self.fetch_worker.moveToThread(self.fetch_thread)

        self.fetch_thread.started.connect(self.fetch_worker.run_fetch)
        self.fetch_worker.categories_finished.connect(self.handle_categories_result)
        self.fetch_worker.categories_finished.connect(self.fetch_worker.deleteLater)
        self.fetch_thread.finished.connect(self.fetch_thread.deleteLater)
        
        self.fetch_thread.start()

    def handle_categories_result(self, categories_data):
        self.fetch_thread.quit()
        self.fetch_thread.wait()
        
        if categories_data:
            print("Categories fetched successfully!")
            self.categories_data = categories_data
            
            # Sort the categories alphabetically by path first, then by categoryName
            self.categories_data.sort(key=lambda x: (x[0], x[1]))
            
            display_categories = [f"{path} / {name} / {cat_id}" for path, name, cat_id in self.categories_data]
            self.SelectEmailType(display_categories)
        else:
            print("Failed to fetch categories.")
            self.categories_data = []
            self.SelectEmailType([])

    def SelectEmailType(self, categories):
        print("Displaying email type selection...")
        self.form_layout = QFormLayout()

        self.check_in = QRadioButton("Check-In")
        self.survey = QRadioButton("Survey")
        self.check_in.setChecked(True)
        radio_button_layout = QHBoxLayout()
        radio_button_layout.addWidget(self.check_in)
        radio_button_layout.addWidget(self.survey)
        radio_button_layout.addStretch()
        self.form_layout.addRow("Select Email Type", radio_button_layout)

        self.email_group_label = QLabel("What category would you like to send emails to? ")
        self.email_group_selection = QComboBox()
        self.email_group_selection.addItems(categories)
        self.form_layout.addRow(self.email_group_label, self.email_group_selection)

        self.preview_button = NextButton("Preview", True)
        self.send_button = NextButton("Send", True)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.preview_button)
        self.button_layout.addWidget(self.send_button)

        self.dynamic_content_layout.addLayout(self.form_layout)
        self.dynamic_content_layout.addLayout(self.button_layout)
        self.dynamic_content_layout.addStretch()

        email_template_api = 10474 if self.check_in.isChecked() else 10489

        self.preview_button.clicked.connect(self.PreviewEmail)
        self.send_button.clicked.connect(self.SendEmail)

    def PreviewEmail(self):
        print("Generating email preview...")
        pass

    def SendEmail(self):
        print("Sending emails...")
        pass

    def GenerateEmail(self):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AutoEmailGUI()
    window.show()
    sys.exit(app.exec())