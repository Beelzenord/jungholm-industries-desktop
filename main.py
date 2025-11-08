"""Main entry point for Gateway Application"""
import sys
import logging
from PySide6.QtWidgets import QApplication, QMessageBox
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


class GatewayApp:
    """Main application controller"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName(APP_NAME)
        
        try:
            self.supabase_client = SupabaseClient()
        except ValueError as e:
            QMessageBox.critical(
                None, "Configuration Error",
                f"Missing configuration: {e}\n\n"
                "Please set SUPABASE_URL and SUPABASE_KEY environment variables."
            )
            sys.exit(1)
        except Exception as e:
            QMessageBox.critical(
                None, "Initialization Error",
                f"Failed to initialize Supabase client: {e}"
            )
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
