"""Main entry point for Gateway Application"""
import sys
import logging
import platform
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from supabase_client import SupabaseClient
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from config import APP_NAME

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def get_app_icon():
    """
    Get the application icon, platform-aware.
    - macOS: Prefers .icns format (proper macOS icon with rounded corners)
    - Windows: Uses .ico or .jpeg/.png directly
    - Linux: Uses .png or .jpeg
    """
    assets_dir = Path(__file__).parent / "assets"
    system = platform.system()
    
    # macOS: prefer .icns format for proper app icon
    if system == "Darwin":
        icns_path = assets_dir / "jungholm-logo.icns"
        if icns_path.exists():
            logger.info("Using macOS .icns icon")
            return QIcon(str(icns_path))
        # Fallback to source image
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            logger.info("Using JPEG icon (consider running create_macos_icon.py to generate .icns)")
            return QIcon(str(jpeg_path))
    
    # Windows: use .ico if available, otherwise JPEG/PNG
    elif system == "Windows":
        ico_path = assets_dir / "jungholm-logo.ico"
        if ico_path.exists():
            logger.info("Using Windows .ico icon")
            return QIcon(str(ico_path))
        # Fallback to JPEG
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            logger.info("Using JPEG icon")
            return QIcon(str(jpeg_path))
    
    # Linux and others: use JPEG or PNG
    else:
        jpeg_path = assets_dir / "jungholm-logo.jpeg"
        if jpeg_path.exists():
            return QIcon(str(jpeg_path))
        png_path = assets_dir / "jungholm-logo.png"
        if png_path.exists():
            return QIcon(str(png_path))
    
    logger.warning("No icon file found")
    return QIcon()  # Return empty icon if file not found


class GatewayApp:
    """Main application controller"""
    
    def __init__(self):
        # QApplication MUST be created first before any QIcon/QPixmap operations
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        
        # Now we can safely load and set the icon (QIcon requires QApplication to exist)
        app_icon = get_app_icon()
        self.app.setWindowIcon(app_icon)
        
        # macOS-specific: Ensure icons are shown in menus
        if platform.system() == "Darwin":
            self.app.setAttribute(Qt.ApplicationAttribute.AA_DontShowIconsInMenus, False)
        
        try:
            self.supabase_client = SupabaseClient()
        except ValueError as e:
            # Ensure the app is fully initialized before showing error
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("Configuration Error")
            error_msg.setText(f"Missing configuration: {e}\n\nPlease set SUPABASE_URL and SUPABASE_KEY environment variables.")
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()
            sys.exit(1)
        except Exception as e:
            # Ensure the app is fully initialized before showing error
            error_msg = QMessageBox()
            error_msg.setIcon(QMessageBox.Icon.Critical)
            error_msg.setWindowTitle("Initialization Error")
            error_msg.setText(f"Failed to initialize Supabase client: {e}")
            error_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            error_msg.exec()
            sys.exit(1)
        
        self.login_window = None
        self.main_window = None
        self.show_login()
    
    def show_login(self):
        """Show login window"""
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        self.login_window = LoginWindow(self.supabase_client)
        self.login_window.login_successful.connect(self.on_login_success)
        self.login_window.show()
    
    def on_login_success(self):
        """Handle successful login"""
        if self.login_window:
            self.login_window.close()
            self.login_window = None
        
        self.main_window = MainWindow(self.supabase_client)
        self.main_window.logout_requested.connect(self.show_login)
        self.main_window.show()
    
    def run(self):
        """Run the application"""
        sys.exit(self.app.exec())


if __name__ == "__main__":
    app = GatewayApp()
    app.run()
