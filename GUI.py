import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QRadioButton,
                             QLabel, QTextEdit, QHBoxLayout, QFrame, QFormLayout, QFileDialog)
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
    login_finished = pyqtSignal(bool)

    def __init__(self, basic_oauth, username, password, url):
        super().__init__()
        self.basic_oauth = basic_oauth
        self.username = username
        self.password = password
        self.url = url

    def run_login(self):
        """
        This method will be executed in the separate thread.
        It calls the potentially blocking LoginFunction.
        """
        print("Starting login process in a background thread...")
        try:
            login_successful = LoginFunction(self.basic_oauth, self.username, self.password, self.url)
            # Emit the result back to the main thread
            self.login_finished.emit(login_successful)
        except Exception as e:
            print(f"An error occurred during login: {e}")
            self.login_finished.emit(False)


class AutoEmailGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PK's Auto Email Sender")  # Title of app in header bar

        # Open app in the center of the screen & set size
        screen = QApplication.primaryScreen()  # Scrape the correct screen to open on
        screen_geometry = screen.geometry()  # Determine the primary screen's geometry
        window_width = 800  # Width of the app
        window_height = 600  # Height of the app
        x = (screen_geometry.width() - window_width) // 2  # Calculate the halfway width
        y = (screen_geometry.height() - window_height) // 2  # Calculate the halfway height
        self.setGeometry(x, y, window_width, window_height)  # Set the app's opening location and size

        # Set the icon
        script_dir = os.path.dirname(os.path.abspath(__file__))  # Get the file path for this code
        icon_path = os.path.join(script_dir, 'PK_logo.png')  # Add the icon's file name to the path
        self.setWindowIcon(QIcon(icon_path))  # Add the icon to the app's header bar

        # Initialize the main layout for the entire window
        self.main_app_layout = QVBoxLayout()
        self.setLayout(self.main_app_layout)

        # --- Permanent Top Section ---
        header_layout, separator = permanentHeader("Automatic Email Sender", 'email.png')
        self.main_app_layout.addLayout(header_layout)
        self.main_app_layout.addWidget(separator)

        # --- Dynamic Content Area ---
        # This is the layout that will be cleared and repopulated
        self.dynamic_content_layout = QVBoxLayout()
        self.main_app_layout.addLayout(self.dynamic_content_layout)  # Add it to the main layout

        # Add a stretch to push content to the top
        self.main_app_layout.addStretch()
        
        # Initialize log components to None
        self.log_text_edit = None
        self.thread = None
        self.worker = None

        self.Login()

    def setup_logging_section(self):
        """Initializes and sets up the logging UI and worker thread."""
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)  # Make the log text edit read-only
        self.log_text_edit.setPlaceholderText("Logs will appear here...")
        self.log_text_edit.setStyleSheet("background-color: #333; color: #fff;")  # Dark theme for logs
        self.main_app_layout.addWidget(self.log_text_edit)

        # Redirect stdout to our custom stream and connect the signal
        sys.stdout = Stream()
        sys.stdout.newText.connect(self.append_log)
    
    def append_log(self, text):
        """Appends text to the log QTextEdit."""
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

        self.clearLayout(self.dynamic_content_layout)  # Clear only the dynamic content layout
        self.setup_logging_section() # Moved the logging section setup here

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
        self.login_button.setEnabled(False) # Disable the button to prevent double-clicks
        
        # Get the login credentials from the input fields
        username = self.username_input.text()
        password = self.password_input.text()
        url = "https://pknowles.jamacloud.com/rest/v2/"

        # Create a new thread and a new worker for the login task
        self.login_thread = QThread()
        self.login_worker = LoginWorker(self.basic_oauth, username, password, url)
        
        # Move the worker to the thread
        self.login_worker.moveToThread(self.login_thread)

        # Connect signals and slots
        # When the thread starts, execute the worker's run_login method
        self.login_thread.started.connect(self.login_worker.run_login)
        # When the worker finishes, call the method to handle the result
        self.login_worker.login_finished.connect(self.handle_login_result)
        # Clean up the thread and worker when the work is done
        self.login_worker.login_finished.connect(self.login_worker.deleteLater)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        # Start the thread
        self.login_thread.start()

    def handle_login_result(self, login_successful):
        self.login_button.setEnabled(True) # Re-enable the button
        self.login_thread.quit()
        self.login_thread.wait() # Wait for the thread to terminate

        if login_successful:
            print("Login successful!")
            self.clearLayout(self.dynamic_content_layout)
            project_api = 51
            # REQUEST A LIST OF ALL CATEGORIES IN THE PROJECT AND GENERATE A LIST FOR USE IN A QCOMBOBOX
            self.SelectEmailType()
        else:
            print("Login failed. Please check your credentials and try again.")
            
    def SelectEmailType(self):
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
        # Add QComboBox self.email_group_selection
        self.form_layout.addRow(self.email_group_label)

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
        # TODO add functionality to display a preview email
        pass

    def SendEmail(self):
        print("Sending emails...")
        # TODO add functionality to send emails
        pass

if __name__ == "__main__":
    # Run the app when running this file
    app = QApplication(sys.argv)
    window = AutoEmailGUI()
    window.show()
    sys.exit(app.exec())
