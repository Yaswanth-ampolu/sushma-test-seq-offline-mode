"""
Main entry point for the Spring Test App.
"""
import sys
import os
import logging
import argparse
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# Add current directory to path to make imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import services
from services.settings_service import SettingsService
from services.sequence_generator import SequenceGenerator
from services.chat_service import ChatService
from services.export_service import ExportService

# Import data models
from models.data_models import SpringSpecification, SetPoint

# Import UI components
from ui.main_window import create_main_window
from ui.styles import apply_theme


def setup_logging():
    """Set up logging configuration."""
    # Use the directory where the script is located instead of current working directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logs_dir = os.path.join(base_dir, "logs")
    
    # Create logs directory if it doesn't exist
    if not os.path.exists(logs_dir):
        try:
            os.makedirs(logs_dir)
        except PermissionError:
            # Fallback to user's temp directory if we can't write to app directory
            import tempfile
            logs_dir = os.path.join(tempfile.gettempdir(), "SpringTestApp", "logs")
            os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(logs_dir, "app.log")
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info(f"Logging to: {log_file}")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Spring Test App")
    parser.add_argument(
        "--reset-specs",
        action="store_true",
        help="Reset all spring specifications to default values and remove all set points on startup"
    )
    return parser.parse_args()


def main():
    """Main entry point."""
    # Set up logging
    setup_logging()
    
    logging.info("Starting Spring Test App")
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Spring Test Sequence Generator")
    
    # Set application icon
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "icon.ico")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)
        logging.info(f"Application icon set from {icon_path}")
    else:
        logging.warning(f"Icon file not found at {icon_path}")
    
    # Create services
    logging.info("Initializing services")
    settings_service = SettingsService()
    export_service = ExportService()
    chat_service = ChatService(settings_service)
    
    # Reset specifications if requested
    if args.reset_specs:
        logging.info("Completely resetting spring specifications and clearing all set points")
        
        # Create default spring specification with no default set points
        default_spec = SpringSpecification(create_defaults=False)
        
        # Log confirmation
        logging.info("Created new specification with no set points")
            
        # Set the specification in settings service
        settings_service.set_spring_specification(default_spec)
    
    # Get API key from settings
    api_key = settings_service.get_api_key()
    
    # Create sequence generator with API key
    sequence_generator = SequenceGenerator()
    sequence_generator.set_api_key(api_key)
    
    # Set spring specifications from settings
    spring_specification = settings_service.get_spring_specification()
    sequence_generator.set_spring_specification(spring_specification)
    
    # Create and show main window
    logging.info("Creating main window")
    window = create_main_window(
        settings_service=settings_service,
        sequence_generator=sequence_generator,
        chat_service=chat_service,
        export_service=export_service
    )
    
    # Apply theme
    apply_theme(window)
    
    window.show()
    
    # Start event loop
    logging.info("Application started")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 