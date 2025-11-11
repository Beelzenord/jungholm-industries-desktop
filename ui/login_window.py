"""Login window for authentication"""
import logging
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFormLayout
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QIcon
from config import APP_NAME

logger = logging.getLogger(__name__)


def get_app_icon():
    """
    Get the application icon, platform-aware.
    - macOS: Prefers .icns format (proper macOS icon with rounded corners)
    - Windows: Uses .ico or .jpeg/.png directly
    - Linux: Uses .png or .jpeg
    """
    import platform
    assets_dir = Path(__file__).parent.parent / "assets"
    system = platform.system()
    
    # macOS: prefer .icns format for proper app icon
    if system == "Darwin":
        icns_path = assets_dir / "jungholm-logo.icns"
        if icns_path.exists():
            return QIcon(str(icns_path))
        # Fallback to source image
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            return QIcon(str(jpeg_path))
    
    # Windows: use .ico if available, otherwise JPEG/PNG
    elif system == "Windows":
        ico_path = assets_dir / "jungholm-logo.ico"
        if ico_path.exists():
            return QIcon(str(ico_path))
        # Fallback to JPEG
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            return QIcon(str(jpeg_path))
    
    # Linux and others: use JPEG or PNG
    else:
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            return QIcon(str(jpeg_path))
        png_path = assets_dir / "jungholm-logo.png"
        if png_path.exists():
            return QIcon(str(png_path))
    
    return QIcon()  # Return empty icon if file not found


def create_styled_message_box(parent, icon_type, title, message):
    """Create a styled QMessageBox with clear, readable text and good contrast"""
    msg_box = QMessageBox(parent)
    msg_box.setIcon(icon_type)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    
    # Apply clear, high-contrast styling
    msg_box.setStyleSheet("""
        QMessageBox {
            background-color: #ffffff;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }
        QMessageBox QLabel {
            color: #212529;
            font-size: 14px;
            font-weight: 500;
            min-width: 300px;
            padding: 10px;
        }
        QMessageBox QPushButton {
            background-color: #007bff;
            color: #ffffff;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-size: 13px;
            font-weight: 600;
            min-width: 80px;
        }
        QMessageBox QPushButton:hover {
            background-color: #0056b3;
        }
        QMessageBox QPushButton:pressed {
            background-color: #004085;
        }
    """)
    
    return msg_box


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
        self.setFixedSize(450, 500)
        
        # Set window icon
        self.setWindowIcon(get_app_icon())
        
        # Apply modern styling to the window
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            }
        """)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(30)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Branding section with improved styling
        title_label = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_font.setWeight(QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #212529;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Gateway Application")
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(30)
        
        # Form layout with improved styling and alignment
        form_layout = QFormLayout()
        form_layout.setSpacing(20)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        
        # Email field with modern styling
        email_label = QLabel("Email:")
        email_label.setMinimumWidth(80)  # Fixed width for consistent alignment
        email_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 13px;
                padding-right: 10px;
            }
        """)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter your email address")
        self.email_input.setMinimumHeight(45)
        self.email_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                color: #212529;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border: 2px solid #adb5bd;
            }
        """)
        form_layout.addRow(email_label, self.email_input)
        
        # Password field with modern styling
        password_label = QLabel("Password:")
        password_label.setMinimumWidth(80)  # Same width as email label for alignment
        password_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: 500;
                font-size: 13px;
                padding-right: 10px;
            }
        """)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 2px solid #dee2e6;
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                color: #212529;
            }
            QLineEdit:focus {
                border: 2px solid #007bff;
                background-color: #ffffff;
            }
            QLineEdit:hover {
                border: 2px solid #adb5bd;
            }
        """)
        form_layout.addRow(password_label, self.password_input)
        
        layout.addLayout(form_layout)
        
        layout.addSpacing(10)
        
        # Login button with improved styling
        self.login_button = QPushButton("Login")
        self.login_button.setMinimumHeight(50)
        login_font = QFont()
        login_font.setPointSize(14)
        login_font.setBold(True)
        self.login_button.setFont(login_font)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: bold;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #ffffff;
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
            msg_box = create_styled_message_box(
                self, QMessageBox.Icon.Warning, 
                "Validation Error", 
                "Please enter both email and password."
            )
            msg_box.exec()
            return
        
        # Disable button during login
        self.login_button.setEnabled(False)
        self.login_button.setText("Logging in...")
        
        # Attempt login
        success, error_msg = self.supabase_client.login(email, password)
        
        if success:
            msg_box = create_styled_message_box(
                self, QMessageBox.Icon.Information,
                "Success",
                "Login successful! Welcome to the Gateway Application."
            )
            msg_box.exec()
            self.login_successful.emit()
        else:
            msg_box = create_styled_message_box(
                self, QMessageBox.Icon.Critical,
                "Login Failed",
                f"Login failed: {error_msg or 'Unknown error'}\n\nPlease check your credentials and try again."
            )
            msg_box.exec()
            self.login_button.setEnabled(True)
            self.login_button.setText("Login")
            self.password_input.clear()

