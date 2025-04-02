"""
Settings module for the Spring Test App.
Handles saving and loading settings including API provider selection.
"""
import json
import os
import logging
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

# Default settings
DEFAULT_SETTINGS = {
    "api_provider": "together",  # together or ollama
    "api_together_model": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "api_together_temperature": 0.1,
    "api_ollama_model": "qwen2.5-coder:7b",
    "api_ollama_temperature": 0.1,
    "theme": "light",
    "last_export_format": "CSV",
    "last_export_directory": "",
}

# Get the application data directory
def get_app_data_dir():
    """Get the application data directory."""
    # Use standard OS-specific app data directories
    home = Path.home()
    
    if os.name == 'nt':  # Windows
        app_data = os.environ.get('APPDATA', str(home / 'AppData' / 'Roaming'))
        return Path(app_data) / 'SpringTestApp'
    elif os.name == 'posix':  # Linux, macOS
        if os.path.exists(home / '.config'):  # Linux, newer macOS
            return home / '.config' / 'SpringTestApp'
        else:  # older macOS
            return home / 'Library' / 'Application Support' / 'SpringTestApp'
    else:  # Fallback
        return home / '.spring_test_app'

# Create app data directory if it doesn't exist
def ensure_app_data_dir():
    """Create app data directory if it doesn't exist."""
    app_data_dir = get_app_data_dir()
    os.makedirs(app_data_dir, exist_ok=True)
    return app_data_dir

# Settings file path
def get_settings_file():
    """Get the settings file path."""
    app_data_dir = ensure_app_data_dir()
    return app_data_dir / 'settings.json'

# Load settings from file
def get_settings():
    """Load settings from file or return defaults if file doesn't exist."""
    settings_file = get_settings_file()
    
    if not settings_file.exists():
        logger.info("Settings file not found. Using defaults.")
        return DEFAULT_SETTINGS.copy()
    
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        # Ensure all default settings are present
        for key, value in DEFAULT_SETTINGS.items():
            if key not in settings:
                settings[key] = value
        
        return settings
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

# Save settings to file
def save_settings(settings):
    """Save settings to file."""
    settings_file = get_settings_file()
    
    try:
        with open(settings_file, 'w') as f:
            json.dump(settings, f, indent=2)
        logger.info("Settings saved successfully.")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False

# Update a specific setting
def update_setting(key, value):
    """Update a specific setting and save to file."""
    settings = get_settings()
    settings[key] = value
    return save_settings(settings)

# Get a specific setting
def get_setting(key, default=None):
    """Get a specific setting."""
    settings = get_settings()
    return settings.get(key, default)

# Set the API provider
def set_api_provider(provider):
    """Set the API provider and save to file."""
    if provider not in ["together", "ollama"]:
        raise ValueError(f"Invalid API provider: {provider}")
    
    return update_setting("api_provider", provider)

# Get the API provider
def get_api_provider():
    """Get the API provider."""
    return get_setting("api_provider", "together") 