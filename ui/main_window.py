"""Main window for instrument selection and session management"""
import logging
from datetime import datetime
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from config import APP_NAME

logger = logging.getLogger(__name__)


class MainWindow(QWidget):
    """Main window for instrument selection and session management"""
    
    logout_requested = Signal()
    
    def __init__(self, supabase_client):
        super().__init__()
        self.supabase_client = supabase_client
        self.instruments = []
        self.current_session_id: Optional[str] = None
        self.session_start_time: Optional[datetime] = None
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self.update_timer_display)
        self.init_ui()
        self.load_instruments()
        self.setup_offline_queue_timer()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle(f"{APP_NAME} - Gateway")
        self.setMinimumSize(600, 500)
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel(APP_NAME)
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # User info
        user = self.supabase_client.get_current_user()
        if user:
            user_email = user.user.email or "Unknown"
            user_label = QLabel(f"User: {user_email}")
            header_layout.addWidget(user_label)
        
        # Logout button
        logout_button = QPushButton("Logout")
        logout_button.clicked.connect(self.handle_logout)
        header_layout.addWidget(logout_button)
        
        layout.addLayout(header_layout)
        
        # Instrument selection group
        instrument_group = QGroupBox("Select Instrument")
        instrument_layout = QVBoxLayout()
        
        self.instrument_combo = QComboBox()
        self.instrument_combo.setMinimumHeight(35)
        self.instrument_combo.setEnabled(True)
        instrument_layout.addWidget(QLabel("Instrument:"))
        instrument_layout.addWidget(self.instrument_combo)
        
        instrument_group.setLayout(instrument_layout)
        layout.addWidget(instrument_group)
        
        # Session control group
        session_group = QGroupBox("Session Control")
        session_layout = QVBoxLayout()
        
        # Timer display
        self.timer_label = QLabel("00:00:00")
        timer_font = QFont()
        timer_font.setPointSize(32)
        timer_font.setBold(True)
        self.timer_label.setFont(timer_font)
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("color: #007bff;")
        session_layout.addWidget(self.timer_label)
        
        # Status label
        self.status_label = QLabel("Ready to start session")
        self.status_label.setAlignment(Qt.AlignCenter)
        session_layout.addWidget(self.status_label)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.activate_button = QPushButton("Activate")
        self.activate_button.setMinimumHeight(45)
        self.activate_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.activate_button.clicked.connect(self.handle_activate)
        button_layout.addWidget(self.activate_button)
        
        self.stop_button = QPushButton("Stop")
        self.stop_button.setMinimumHeight(45)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self.stop_button.clicked.connect(self.handle_stop)
        button_layout.addWidget(self.stop_button)
        
        session_layout.addLayout(button_layout)
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        # Status/log area
        log_group = QGroupBox("Status")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("background-color: #f8f9fa;")
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
    
    def log_message(self, message: str):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
        logger.info(message)
    
    def load_instruments(self):
        """Load instruments from Supabase"""
        self.log_message("Loading instruments...")
        self.instruments = self.supabase_client.get_instruments()
        
        self.instrument_combo.clear()
        if self.instruments:
            for instrument in self.instruments:
                name = instrument.get("name", f"Instrument {instrument.get('id', 'Unknown')}")
                self.instrument_combo.addItem(name, instrument.get("id"))
            self.log_message(f"Loaded {len(self.instruments)} instrument(s)")
        else:
            self.instrument_combo.addItem("No instruments available", None)
            self.log_message("No instruments found")
    
    def handle_activate(self):
        """Handle activate button click"""
        instrument_id = self.instrument_combo.currentData()
        
        if not instrument_id:
            QMessageBox.warning(self, "Error", "Please select an instrument.")
            return
        
        self.activate_button.setEnabled(False)
        self.activate_button.setText("Activating...")
        
        success, session_id, error_msg = self.supabase_client.start_session(instrument_id)
        
        if success and session_id:
            self.current_session_id = session_id
            self.activate_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.instrument_combo.setEnabled(False)
            self.status_label.setText("Session Active")
            self.session_start_time = datetime.now()
            self.session_timer.start(1000)  # Update every second
            instrument_name = self.instrument_combo.currentText()
            self.log_message(f"Session started for {instrument_name}")
        else:
            QMessageBox.critical(self, "Error", f"Failed to start session: {error_msg or 'Unknown error'}")
            self.activate_button.setEnabled(True)
            self.activate_button.setText("Activate")
            if error_msg:
                self.log_message(f"Failed to start session: {error_msg}")
    
    def handle_stop(self):
        """Handle stop button click"""
        if not self.current_session_id:
            return
        
        self.stop_button.setEnabled(False)
        self.stop_button.setText("Stopping...")
        
        success, error_msg = self.supabase_client.stop_session(self.current_session_id)
        
        if success:
            self.session_timer.stop()
            self.session_start_time = None
            self.current_session_id = None
            self.activate_button.setEnabled(True)
            self.activate_button.setText("Activate")
            self.stop_button.setEnabled(False)
            self.stop_button.setText("Stop")
            self.instrument_combo.setEnabled(True)
            self.status_label.setText("Session Stopped")
            self.timer_label.setText("00:00:00")
            self.log_message("Session stopped successfully")
        else:
            QMessageBox.critical(self, "Error", f"Failed to stop session: {error_msg or 'Unknown error'}")
            self.stop_button.setEnabled(True)
            self.stop_button.setText("Stop")
            if error_msg:
                self.log_message(f"Failed to stop session: {error_msg}")
    
    def update_timer_display(self):
        """Update the timer display"""
        if self.session_start_time:
            elapsed = datetime.now() - self.session_start_time
            hours, remainder = divmod(elapsed.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            time_str = f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
            self.timer_label.setText(time_str)
    
    def handle_logout(self):
        """Handle logout"""
        reply = QMessageBox.question(
            self, "Logout",
            "Are you sure you want to logout?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.current_session_id:
                # Stop session before logout
                self.supabase_client.stop_session(self.current_session_id)
            self.session_timer.stop()
            self.session_start_time = None
            self.supabase_client.logout()
            self.logout_requested.emit()
    
    def setup_offline_queue_timer(self):
        """Setup timer to process offline queue periodically"""
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_offline_queue)
        self.queue_timer.start(30000)  # Process every 30 seconds
    
    def process_offline_queue(self):
        """Process offline queue"""
        if self.supabase_client.is_authenticated():
            processed = self.supabase_client.process_offline_queue()
            if processed > 0:
                self.log_message(f"Processed {processed} queued event(s)")
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.current_session_id:
            reply = QMessageBox.question(
                self, "Active Session",
                "You have an active session. Stop it before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Cancel:
                event.ignore()
                return
            elif reply == QMessageBox.Yes:
                self.handle_stop()
        
        self.session_timer.stop()
        self.session_start_time = None
        event.accept()

