"""
Main window module for the Spring Test App.
Contains the main window class and initialization.
"""
import sys
import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QMessageBox, QApplication, QTabWidget)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

from utils.constants import APP_TITLE, APP_VERSION, APP_WINDOW_SIZE
from models.data_models import TestSequence

# These will be implemented in separate files
from ui.chat_results_container import ChatResultsContainer
from ui.specifications_panel import SpecificationsPanel


class MainWindow(QMainWindow):
    """Main window for the Spring Test App."""
    
    def __init__(self, settings_service, sequence_generator, chat_service, export_service):
        """Initialize the main window.
        
        Args:
            settings_service: Settings service.
            sequence_generator: Sequence generator service.
            chat_service: Chat service.
            export_service: Export service.
        """
        super().__init__()
        
        # Store services
        self.settings_service = settings_service
        self.sequence_generator = sequence_generator
        self.chat_service = chat_service
        self.export_service = export_service
        
        # Set up the UI
        self.init_ui()
        
        # Set up signals and slots
        self.connect_signals()
        
    def init_ui(self):
        """Initialize the UI."""
        # Set window properties
        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION}")
        
        # Load saved window geometry (position and size)
        self.restore_window_geometry()
        
        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources", "icon.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Create the central widget and layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create content panels
        self.chat_results_container = ChatResultsContainer(
            self.chat_service, 
            self.sequence_generator,
            self.export_service
        )
        self.specs_panel = SpecificationsPanel(
            self.settings_service, 
            self.sequence_generator, 
            self.chat_service
        )
        
        # Add specifications panel to the sidebar
        self.chat_results_container.sidebar.add_specifications_panel(self.specs_panel)
        
        # Add chat results container to main layout
        main_layout.addWidget(self.chat_results_container)
        
        # Set the central widget
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # Apply theme
        self.apply_theme()
    
    def connect_signals(self):
        """Connect signals and slots."""
        # Connect chat results container signals
        self.chat_results_container.sequence_generated.connect(self.on_sequence_generated)
        
        # Connect specifications panel signals
        self.specs_panel.specifications_changed.connect(self.on_specifications_changed)
        self.specs_panel.api_key_changed.connect(self.on_api_key_changed)
        self.specs_panel.clear_chat_clicked.connect(self.on_clear_chat)
    
    def on_api_key_changed(self, api_key):
        """Handle API key changes.
        
        Args:
            api_key: New API key.
        """
        # Update the API key in the sequence generator
        self.sequence_generator.set_api_key(api_key)
        
        # Only validate the API key if it's not empty
        if api_key.strip():
            # Validate the API key
            self.chat_results_container.validate_api_key()
    
    def on_clear_chat(self):
        """Handle clear chat button clicks."""
        # Clear chat history
        self.chat_service.clear_history()
        
        # Save the empty chat history to disk immediately
        self.chat_service.save_history()
        
        # Update chat panel
        self.chat_results_container.refresh_chat_display()
    
    def on_sequence_generated(self, sequence):
        """Handle sequence generation.
        
        Args:
            sequence: Generated sequence.
        """
        # The sequence is already displayed in the sidebar
        # No need to do anything here
        pass
    
    def on_specifications_changed(self, specifications):
        """Handle specifications changes.
        
        Args:
            specifications: New specifications.
        """
        # The sequence generator is already updated by the specifications panel,
        # so we don't need to do anything here.
        pass
    
    def apply_theme(self):
        """Apply the theme."""
        from ui.styles import apply_theme
        apply_theme(self)
    
    def restore_window_geometry(self):
        """Restore window position and size from settings."""
        try:
            # Get the primary screen geometry
            screen = QApplication.primaryScreen().availableGeometry()
            
            # Reset window geometry if needed while preserving API key
            if not self.settings_service.get_window_geometry():
                self.settings_service.reset_window_geometry()
            
            # Get window geometry from settings
            geometry = self.settings_service.get_window_geometry()
            
            # Get the desired window size
            width = geometry.get("width", 1200)
            height = geometry.get("height", 800)
            
            # Calculate the center position on the primary screen
            x = (screen.width() - width) // 2
            y = (screen.height() - height) // 2
            
            # Ensure the window is within the primary screen bounds
            x = max(screen.left(), min(x, screen.right() - width))
            y = max(screen.top(), min(y, screen.bottom() - height))
            
            # Apply window position and size
            self.setGeometry(x, y, width, height)
            
            # Apply maximized state if needed
            if geometry.get("is_maximized", False):
                self.showMaximized()
            else:
                # Ensure window is normal (not minimized)
                self.setWindowState(Qt.WindowNoState)
                # Raise and activate window
                self.raise_()
                self.activateWindow()
            
            # Log the restoration
            logging.info(f"Restored window geometry: x={x}, y={y}, width={width}, height={height}")
        except Exception as e:
            # Log the error and use default values
            logging.error(f"Error restoring window geometry: {e}")
            # Reset window geometry while preserving settings
            self.settings_service.reset_window_geometry()
            # Center on primary screen with default size
            screen = QApplication.primaryScreen().availableGeometry()
            width, height = APP_WINDOW_SIZE
            x = (screen.width() - width) // 2
            y = (screen.height() - height) // 2
            self.setGeometry(x, y, width, height)
    
    def save_window_geometry(self):
        """Save current window position and size to settings."""
        try:
            # Check if window is maximized
            is_maximized = self.isMaximized()
            
            # Get current geometry
            geometry = self.geometry()
            
            # Create geometry dictionary
            geometry_dict = {
                "x": geometry.x(),
                "y": geometry.y(),
                "width": geometry.width(),
                "height": geometry.height(),
                "is_maximized": is_maximized
            }
            
            # Save to settings
            self.settings_service.set_window_geometry(geometry_dict)
            
            # Log the save
            logging.info(f"Saved window geometry: {geometry_dict}")
        except Exception as e:
            # Log the error
            logging.error(f"Error saving window geometry: {e}")
    
    def closeEvent(self, event):
        """Handle window close event.
        
        Args:
            event: Close event.
        """
        # Save window geometry
        self.save_window_geometry()
        
        # Save settings
        self.settings_service.save_settings()
        
        # Save chat history
        self.chat_service.save_history()
        
        # Accept the event
        event.accept()
        
    def resizeEvent(self, event):
        """Handle window resize events.
        
        Args:
            event: Resize event.
        """
        # Save geometry only if not maximized
        # This avoids saving incorrect sizes during maximize/restore operations
        if not self.isMaximized():
            self.save_window_geometry()
        
        # Let the parent class handle the event
        super().resizeEvent(event)
        
    def moveEvent(self, event):
        """Handle window move events.
        
        Args:
            event: Move event.
        """
        # Save geometry only if not maximized
        # This avoids saving incorrect positions during maximize/restore operations
        if not self.isMaximized():
            self.save_window_geometry()
        
        # Let the parent class handle the event
        super().moveEvent(event)

    def updateWindowTitle(self, status=None):
        """Update the window title, possibly with status information."""
        title = "Spring Test App"
        if status:
            # Replace Together.ai with FTS.ai in window titles
            if "Together.ai" in status:
                status = status.replace("Together.ai", "FTS.ai")
            title += f" - {status}"
        self.setWindowTitle(title)

    def updateStatusBar(self, message):
        """Update the status bar with a message."""
        # Replace Together.ai with FTS.ai in status bar messages
        if message and "Together.ai" in message:
            message = message.replace("Together.ai", "FTS.ai")
        
        if hasattr(self, 'statusBar'):
            self.statusBar().showMessage(message)


def create_main_window(settings_service, sequence_generator, chat_service, export_service):
    """Create and configure the main window.
    
    Args:
        settings_service: Settings service.
        sequence_generator: Sequence generator service.
        chat_service: Chat service.
        export_service: Export service.
        
    Returns:
        Configured MainWindow instance.
    """
    # Create the main window
    window = MainWindow(
        settings_service=settings_service,
        sequence_generator=sequence_generator,
        chat_service=chat_service,
        export_service=export_service
    )
    
    # The position, size and maximized state are now handled in the restore_window_geometry method
    # Simply show the window - it will display with the correct settings
    window.show()
    
    return window 