# Auto Email Script GUI

import sys
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QRadioButton, \
                             QLabel, QTextEdit, QHBoxLayout, QFrame, QFormLayout, QFileDialog)
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QPixmap
from LoginFunction import LoginFunction
from PermanentHeader import permanentHeader
from NextButton import NextButton

class AutoEmailGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PK's Auto Email Sender") # Title of app in header bar
        
        # Open app in the center of the screen & set size
        screen = QApplication.primaryScreen() # Scrape the correct screen to open on
        screen_geometry = screen.geometry() # Determine the primary screen's geometry
        window_width = 800 # Width of the app
        window_height = 600 # Height of the app
        x = (screen_geometry.width() - window_width) // 2 # Calculate the halfway width
        y = (screen_geometry.height() - window_height) // 2 # Calculate the halfway height
        self.setGeometry(x, y, window_width, window_height) # Set the app's opening location and size

        # Set the icon
        script_dir = os.path.dirname(os.path.abspath(__file__)) # Get the file path for this code
        icon_path = os.path.join(script_dir, 'PK_logo.png') # Add the icon's file name to the path
        self.setWindowIcon(QIcon(icon_path)) # Add the icon to the app's header bar

        # Initialize the main layout for the entire window
        self.main_app_layout = QVBoxLayout()
        self.setLayout(self.main_app_layout)

        # --- Permanent Top Section ---
        header_layout, separator = permanentHeader("Automatic Email Sender",'email.png')
        self.main_app_layout.addLayout(header_layout)
        self.main_app_layout.addWidget(separator)

        # --- Dynamic Content Area ---
        # This is the layout that will be cleared and repopulated
        self.dynamic_content_layout = QVBoxLayout()
        self.main_app_layout.addLayout(self.dynamic_content_layout) # Add it to the main layout

        # Add a stretch to push content to the top
        self.main_app_layout.addStretch()

        self.Login()

    def Login(self):
        form_layout = QFormLayout()

        self.basic = QRadioButton("Basic")
        self.basic.setChecked(True)
        
        radio_button_layout = QHBoxLayout()
        radio_button_layout.addWidget(self.basic)
        radio_button_layout.addStretch()

        form_layout.addRow("Select Jama Connect Login Method:", radio_button_layout)

        self.submit_button = NextButton("Submit",True)

        self.dynamic_content_layout.addLayout(form_layout)
        self.dynamic_content_layout.addWidget(self.submit_button)
        self.dynamic_content_layout.addStretch()

        self.basic_oauth = 'basic' if self.basic.isChecked() else 'oauth'

        self.submit_button.clicked.connect(self.CheckLoginMethod)

    def CheckLoginMethod(self):
        self.basic_oauth = 'basic' if self.basic.isChecked() else 'oauth'

        self.clearLayout(self.dynamic_content_layout) # Clear only the dynamic content layout
        
        if self.basic_oauth == 'basic':
            self.LoginForm("Username","Password")
        else:
            self.LoginForm("Client ID","Client Secret")

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
        self.form_layout = QFormLayout()

        self.Jama_label = QLabel("Jama Connect API Login Information")
        self.form_layout.addRow(self.Jama_label)
        
        self.URL_label = QLabel("Jama Connect URL: ")
        self.URL_input = QLineEdit()
        self.URL_input.setPlaceholderText("Enter your Jama Connect instance's URL")
        self.form_layout.addRow(self.URL_label, self.URL_input)

        self.username_label = QLabel(UN + ": ")
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your " + UN)
        self.form_layout.addRow(self.username_label, self.username_input)

        self.password_label = QLabel(PW + ": ")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your " + PW)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.form_layout.addRow(self.password_label, self.password_input)

        self.login_button = QPushButton("Login")
        self.form_layout.addRow(self.login_button)

        self.login_button.clicked.connect(self.LoginButton)

        self.dynamic_content_layout.addLayout(self.form_layout)
        self.dynamic_content_layout.addStretch()

    def LoginButton(self):
        LoginFunction(self.basic_oauth,self.username_input.text(),self.password_input.text(),self.URL_input.text())
        self.clearLayout(self.dynamic_content_layout)
        self.SelectEmailType()

    def SelectEmailType(self):
        self.form_layout = QFormLayout()

        self.check_in = QRadioButton("Check-In")
        self.survey = QRadioButton("Survey")
        self.check_in.setChecked(True)
        radio_button_layout = QHBoxLayout()
        radio_button_layout.addWidget(self.check_in)
        radio_button_layout.addWidget(self.survey)
        radio_button_layout.addStretch()
        self.form_layout.addRow("Select Email Type", radio_button_layout)

        self.preview_button = NextButton("Preview",True)
        self.send_button = NextButton("Send",True)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.preview_button)
        self.button_layout.addWidget(self.send_button)

        self.dynamic_content_layout.addLayout(self.form_layout)
        self.dynamic_content_layout.addLayout(self.button_layout)
        self.dynamic_content_layout.addStretch()

    def PreviewEmail(self):
        # TODO add functionality to display a preview email
        x=0

    def SendEmail(self):
        # TODO add functionality to send emails
        x=0

if __name__ == "__main__":
    # Run the app when running this file
    app = QApplication(sys.argv)
    window = AutoEmailGUI()
    window.show()
    sys.exit(app.exec())