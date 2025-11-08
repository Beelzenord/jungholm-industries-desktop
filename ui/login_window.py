"""Login window for authentication"""
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from config import APP_NAME

logger = logging.getLogger(__name__)


class LoginWindow(QWidget):
    """Login window with email and password fields"""
    
    login_successful = Signal()
    
    def __init__(self, supabase_client):
        super().__init__()
        self.supabase_client = supabase_client
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"{APP_NAME} - Login")
        self.setFixedSize(400, 300)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Branding
        title_label = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Gateway Application")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # Form layout
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        # Email field
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email")
        self.email_input.setMinimumHeight(35)
        form_layout.addRow("Email:", self.email_input)
        
        # Password field
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(35)
        form_layout.addRow("Password:", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(40)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        layout.addWidget(self.login_button)
        
        # Enter key support
        self.password_input.returnPressed.connect(self.handle_login)
        self.email_input.returnPressed.connect(lambda: self.password_input.setFocus())
        
        layout.addStretch()
        
        self.setLayout(layout)
    
    def handle_login(self):
        """Handle login button click"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        if not email or not password:
            QMessageBox.warning(self, "Validation Error", "Please enter both email and password.")
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        
        # Attempt login
        success, error_msg = self.supabase_client.login(email, password)
        
        if success:
            QMessageBox.information(self, "Success", "Login successful!")
            self.login_successful.emit()
        else:
            QMessageBox.critical(self, "Login Failed", f"Login failed: {error_msg or 'Unknown error'}")
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
            self.password_input.clear()

