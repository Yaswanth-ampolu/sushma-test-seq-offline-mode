"""
API client module for the Spring Test App.
Contains functions for making API requests to Together.ai or Ollama and handling responses.
"""

# This file serves as a wrapper that allows switching between different API clients
# based on configuration settings.

import importlib.util
import os
import sys

# Default to Together API
DEFAULT_API_PROVIDER = "together"

# Get the current API provider from environment or settings
def get_api_provider():
    """Get the current API provider from environment or settings.
    
    Returns:
        String with API provider name.
    """
    # Try to get from environment first
    provider = os.environ.get("SPRING_TEST_API_PROVIDER", DEFAULT_API_PROVIDER).lower()
    
    # If not in environment, check settings file
    if provider == DEFAULT_API_PROVIDER:
        try:
            # Import settings file if available
            # This is a simple approach that avoids circular imports
            if importlib.util.find_spec("utils.settings") is not None:
                from utils.settings import get_settings
                settings = get_settings()
                provider = settings.get("api_provider", DEFAULT_API_PROVIDER).lower()
        except:
            # If settings can't be loaded, use default
            pass
    
    # Validate provider
    if provider not in ["together", "ollama"]:
        print(f"Warning: Unknown API provider '{provider}'. Using default: {DEFAULT_API_PROVIDER}")
        provider = DEFAULT_API_PROVIDER
    
    return provider

# Get the current API provider
CURRENT_PROVIDER = get_api_provider()

# Import client modules after determining the provider
# This avoids circular imports
from utils.together_api_client import TogetherAPIClient, TogetherAPIClientWorker
from utils.ollama_client import OllamaAPIClient, OllamaAPIClientWorker

# Create a new API client with the current provider settings
def create_api_client():
    """Create a new API client instance with the current provider settings.
    
    This is useful when the provider has changed and you need a new client instance
    without restarting the application.
    
    Returns:
        New APIClient instance with the current provider.
    """
    provider = get_api_provider()
    if provider == "ollama":
        return OllamaAPIClient()
    else:
        return TogetherAPIClient()

# Export the appropriate API client based on the provider
if CURRENT_PROVIDER == "ollama":
    APIClient = OllamaAPIClient
    APIClientWorker = OllamaAPIClientWorker
else:
    APIClient = TogetherAPIClient
    APIClientWorker = TogetherAPIClientWorker

# Re-export the selected client
__all__ = ['APIClient', 'APIClientWorker', 'get_api_provider', 'create_api_client'] 