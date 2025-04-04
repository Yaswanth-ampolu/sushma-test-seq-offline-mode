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
    parser.add_argument(
        "--clear-chat",
        action="store_true",
        help="Clear chat history on startup"
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
    
    # Clear chat history if running as executable or if clear-chat flag is specified
    if getattr(sys, 'frozen', False) or args.clear_chat:
        logging.info("Clearing chat history on startup (running as executable or --clear-chat specified)")
        chat_service.clear_history()
        # Save empty history to disk immediately to ensure it's persisted
        chat_service.save_history()
    
    # Reset specifications if requested
    if args.reset_specs:
        logging.info("Completely resetting spring specifications and clearing all set points")
        
        # Create default spring specification with ALL fields explicitly reset
        default_spec = SpringSpecification(
            part_name="",
            part_number="",
            part_id=0,
            free_length_mm=0.0,
            coil_count=0.0,
            wire_dia_mm=0.0,
            outer_dia_mm=0.0,
            set_points=[],
            safety_limit_n=0.0,
            unit="mm",
            enabled=False,
            create_defaults=False,
            force_unit="N",
            test_mode="Height Mode",
            component_type="Compression",
            first_speed=0.0,
            second_speed=0.0,
            offer_number="",
            production_batch_number="",
            part_rev_no_date="",
            material_description="",
            surface_treatment="",
            end_coil_finishing=""
        )
        
        # Log confirmation
        logging.info("Created new specification with all fields explicitly reset")
            
        # Set the specification in settings service
        success = settings_service.set_spring_specification(default_spec)
        
        if success:
            logging.info("Successfully reset specifications")
            # Completely reset the settings service state
            settings_service.reset_settings_state()
        else:
            logging.error("Failed to reset specifications")
    
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