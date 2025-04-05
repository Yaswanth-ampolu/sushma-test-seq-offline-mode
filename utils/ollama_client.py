"""
Ollama API client module for the Spring Test App.
Contains functions for making API requests to Ollama and handling responses.
"""
import requests
import pandas as pd
import json
import time
import threading
import re
import os
import importlib.util
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from PyQt5.QtCore import QObject, pyqtSignal
from utils.constants import get_prompt_templates

# Remove the circular import
# from utils.api_client import get_api_provider

# Alternative way to get the API provider without circular import
def _get_current_provider():
    """
    Internal function to get the current API provider without circular imports.
    
    Returns:
        String with API provider name.
    """
    # Default provider
    DEFAULT_API_PROVIDER = "together"
    
    # Try to get from environment first
    provider = os.environ.get("SPRING_TEST_API_PROVIDER", DEFAULT_API_PROVIDER).lower()
    
    # If not in environment, check settings file
    if provider == DEFAULT_API_PROVIDER:
        try:
            # Import settings file if available
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

# Default Ollama settings
OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "spring-assistant-complete"  # Updated to use our comprehensive model with Together.ai prompts
DEFAULT_OLLAMA_TEMPERATURE = 0.5
MAX_RETRIES = 3

# Helper functions for formatting and extracting data
def format_parameter_text(parameters: Dict[str, Any]) -> str:
    """
    Format parameters for display or for use in API prompts.
    
    Args:
        parameters: Dictionary of parameters.
        
    Returns:
        Formatted parameter text.
    """
    lines = []
    
    # Format each parameter as a line
    for key, value in parameters.items():
        # Skip timestamp and metadata
        if key in ["Timestamp", "prompt"]:
            continue
            
        # Simple string conversion
        formatted_value = str(value)
        lines.append(f"{key}: {formatted_value}")
    
    return "\n".join(lines)

def extract_command_sequence(text: str) -> Dict[str, Any]:
    """
    Extract a command sequence from text (usually API response).
    
    Args:
        text: The text containing a command sequence, often from API response.
        
    Returns:
        A dictionary representing the command sequence or empty dict if parsing fails.
    """
    import json
    
    # Check if the response uses the hybrid format with markers
    sequence_start_marker = "---SEQUENCE_DATA_START---"
    sequence_end_marker = "---SEQUENCE_DATA_END---"
    
    if sequence_start_marker in text and sequence_end_marker in text:
        # Extract data between markers
        start_idx = text.find(sequence_start_marker) + len(sequence_start_marker)
        end_idx = text.find(sequence_end_marker)
        if start_idx >= 0 and end_idx > start_idx:
            json_content = text[start_idx:end_idx].strip()
        else:
            json_content = text
    else:
        # Try to extract JSON from the response (traditional way)
        json_start_idx = text.find("[")
        json_end_idx = text.rfind("]") + 1
        
        if json_start_idx >= 0 and json_end_idx > json_start_idx:
            # Found JSON-like syntax in brackets
            json_content = text[json_start_idx:json_end_idx]
        else:
            json_content = text
    
    # Clean up any markdown formatting
    if json_content.startswith("```") and json_content.endswith("```"):
        json_content = json_content[3:-3].strip()
    
    # Try to parse the JSON
    try:
        data = json.loads(json_content)
        return data
    except json.JSONDecodeError:
        # If JSON parsing fails, return empty dict
        return {}

def extract_error_message(response_text: str) -> str:
    """
    Extract error message from API response.
    
    Args:
        response_text: The API response text.
        
    Returns:
        The extracted error message, or empty string if none found.
    """
    # Simple extraction - look for common error message patterns
    error_patterns = [
        r"Error:\s*(.+?)(?:\n|$)",
        r"Failed to\s*(.+?)(?:\n|$)",
        r"Unable to\s*(.+?)(?:\n|$)",
        r"I apologize, but I cannot\s*(.+?)(?:\n|$)"
    ]
    
    for pattern in error_patterns:
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return ""


class OllamaAPIClientWorker(QObject):
    """Worker class for making API requests to Ollama in a separate thread."""
    
    # Define signals
    finished = pyqtSignal(object, str)  # (DataFrame, error_message)
    progress = pyqtSignal(int)  # Progress percentage (0-100)
    status = pyqtSignal(str)    # Status message
    
    def __init__(self, api_client, parameters, model, temperature, max_retries):
        """Initialize the worker.
        
        Args:
            api_client: The API client to use for requests.
            parameters: Dictionary of spring parameters.
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
        """
        super().__init__()
        self.api_client = api_client
        self.parameters = parameters
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        self.is_cancelled = False
    
    def cancel(self):
        """Cancel the current operation."""
        self.is_cancelled = True
    
    def run(self):
        """Run the API request in a separate thread."""
        # Format parameter text for prompt
        parameter_text = format_parameter_text(self.parameters)
        
        # Get the original user prompt
        original_prompt = self.parameters.get('prompt', '')
        
        # Get specifications status if provided
        specifications_status = self.parameters.get('specifications_status', 'No specification status provided')
        
        # Extract free length value for template
        free_length_value = self.parameters.get('Free Length', 'Not provided')
        
        # Extract first_speed and second_speed from parameters
        first_speed_value = self.parameters.get('First Speed', '50')
        second_speed_value = self.parameters.get('Second Speed', '50')
        
        # If free_length_value is not provided, check if it's in the spring_specification
        if free_length_value == 'Not provided' and 'spring_specification' in self.parameters:
            # Try to get it from the spring_specification
            spring_spec = self.parameters['spring_specification']
            if isinstance(spring_spec, dict) and 'free_length_mm' in spring_spec:
                free_length_value = str(spring_spec['free_length_mm'])
                print(f"Found free length in spring_specification: {free_length_value}")
        
        # Check if test_type is provided in parameters
        test_type_text = ""
        if "Test Type" in self.parameters:
            test_type = self.parameters["Test Type"]
            test_type_text = f"This should be a {test_type} test sequence."
        
        # Determine the user's intent based on the prompt or a dedicated flag
        intent_flag = "GENERAL_CONVERSATION"
        
        # Check for explicit test sequence generation requests
        sequence_keywords = ["generate", "create", "make", "build", "produce"]
        if any(keyword in original_prompt.lower() for keyword in sequence_keywords) and "sequence" in original_prompt.lower():
            intent_flag = "GENERATE_TEST_SEQUENCE"
        # Check for analysis requests    
        elif any(keyword in original_prompt.lower() for keyword in ["analyze", "compare", "evaluate", "assess", "review"]):
            intent_flag = "ANALYZE_WITH_SEQUENCE"
        # Check if this is likely a general conversation or question
        elif any(keyword in original_prompt.lower() for keyword in ["what", "how", "why", "when", "explain", "tell me about", "describe"]):
            intent_flag = "GENERAL_CONVERSATION"
        
        # Force GENERATE_TEST_SEQUENCE intent if the prompt contains "generate the test sequence" or 
        # "can you generate the test sequence" or similar direct requests
        if re.search(r'(generate|create)\s+.{0,20}?(test\s+sequence|sequence)', original_prompt.lower()):
            intent_flag = "GENERATE_TEST_SEQUENCE"
            print(f"Forcing GENERATE_TEST_SEQUENCE intent based on direct request")
        
        # Get the appropriate prompt templates for the current provider
        # Use "ollama" directly since this is the Ollama client
        _, user_prompt_template = get_prompt_templates("ollama")
        
        # Use the appropriate user prompt template
        user_prompt = user_prompt_template.format(
            parameter_text=parameter_text,
            test_type_text=test_type_text,
            prompt=original_prompt,
            free_length_value=free_length_value,
            intent_flag=intent_flag,
            first_speed_value=first_speed_value,
            second_speed_value=second_speed_value
        )
        
        # Add explicit FREE_LENGTH_INFO if we're generating a test sequence and have the value
        if intent_flag == "GENERATE_TEST_SEQUENCE" and free_length_value != 'Not provided':
            user_prompt += f"\n\nFREE_LENGTH_INFO: The spring's free length is {free_length_value} mm. This is a required specification that has been provided."
            print(f"Added explicit FREE_LENGTH_INFO to prompt")
        
        # Include previous context if available
        if self.api_client.chat_memory:
            user_prompt += "\n\nPrevious context:\n" + "\n".join(self.api_client.chat_memory[-3:])
        
        # Create payload for Ollama API - NO SYSTEM PROMPT since it's embedded in the model
        payload = {
            "model": self.model,  # Use the model passed in initialization instead of hardcoded value
            "prompt": user_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature
            }
        }
        
        # Save the request for debugging
        self.api_client.request_history.append({
            "timestamp": time.time(),
            "payload": payload
        })
        
        # Make the request with retries
        response_text = ""
        error_message = ""
        
        self.status.emit("Preparing request...")
        self.progress.emit(10)
        
        for attempt in range(self.max_retries):
            if self.is_cancelled:
                self.finished.emit(pd.DataFrame(), "Operation cancelled")
                return
                
            try:
                self.status.emit(f"Sending request to Ollama (attempt {attempt+1}/{self.max_retries})...")
                self.progress.emit(20 + (attempt * 15))
                
                response = self.api_client.session.post(
                    OLLAMA_ENDPOINT,
                    headers={
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=120  # Longer timeout for local models
                )
                
                # Check if response is successful
                if response.status_code == 200:
                    # Parse response
                    response_data = response.json()
                    response_text = response_data.get("response", "")
                    
                    # Save the response for debugging
                    self.api_client.response_history.append({
                        "timestamp": time.time(),
                        "response": response_data
                    })
                    
                    # Break on success
                    self.status.emit("Processing response...")
                    self.progress.emit(70)
                    break
                else:
                    error_message = f"Error: API request failed with status code {response.status_code}"
                    self.status.emit(error_message)
                    self.progress.emit(20)  # Reset progress to retry
                    time.sleep(1)  # Wait before retrying
                    
            except Exception as e:
                error_message = f"Error: {str(e)}"
                self.status.emit(error_message)
                self.progress.emit(20)  # Reset progress to retry
                time.sleep(1)  # Wait before retrying
        
        # Check if any response was received
        if not response_text:
            self.finished.emit(pd.DataFrame(), error_message or "No response received from Ollama")
            return
            
        # Process the sequence response
        try:
            self.status.emit("Extracting sequence data...")
            self.progress.emit(80)
            
            # Try to extract a command sequence
            sequence_data = extract_command_sequence(response_text)
            
            if sequence_data and isinstance(sequence_data, list) and len(sequence_data) > 0:
                # Successfully extracted a sequence, convert to DataFrame
                df = pd.DataFrame(sequence_data)
                
                # Add the original AI response text for reference
                df.attrs['original_response'] = response_text
                
                # Signal completion
                self.status.emit("Sequence generated successfully!")
                self.progress.emit(100)
                self.finished.emit(df, "")
                
            else:
                # No sequence data found - this is likely a chat response
                # Instead of returning as an error, create a chat DataFrame
                self.status.emit("No sequence data found - processing as chat response.")
                self.progress.emit(100)
                
                # Create a chat DataFrame with the response text
                chat_df = pd.DataFrame({
                    "Row": ["CHAT"],
                    "CMD": ["CHAT"],
                    "Description": [response_text],
                    "Condition": [""],
                    "Unit": [""],
                    "Tolerance": [""],
                    "Speed rpm": [""]
                })
                
                # Signal completion with chat DataFrame
                self.finished.emit(chat_df, "")
                
        except Exception as e:
            error_message = f"Error processing sequence: {str(e)}"
            self.status.emit(error_message)
            self.progress.emit(100)
            self.finished.emit(pd.DataFrame(), error_message)


class OllamaAPIClient:
    """Client for making API requests to Ollama."""
    
    def __init__(self, model=DEFAULT_OLLAMA_MODEL, temperature=DEFAULT_OLLAMA_TEMPERATURE, max_retries=MAX_RETRIES):
        """Initialize the API client.
        
        Args:
            model: The model to use for generation.
            temperature: The temperature to use for generation.
            max_retries: Maximum number of retry attempts.
        """
        self.model = model
        self.temperature = temperature
        self.max_retries = max_retries
        
        # Initialize session for API requests
        self.session = requests.Session()
        
        # Histories for debugging
        self.request_history = []
        self.response_history = []
        
        # Store previous messages for context
        self.chat_memory = []
        
        # Track current worker and thread
        self.current_worker = None
        self.current_thread = None
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key (not used for Ollama but included for interface compatibility).
        
        Ollama doesn't require an API key, but this method is included to maintain
        compatibility with the TogetherAPIClient interface expected by the SequenceGenerator.
        
        Args:
            api_key: API key string (ignored).
        """
        # Log that this method is called but not needed
        import logging
        logging.getLogger("SpringTestApp").debug("set_api_key called on OllamaAPIClient - no API key needed for Ollama")
        
        # Do nothing as Ollama doesn't need an API key
        pass
    
    def check_ollama_availability(self) -> Dict[str, Any]:
        """
        Check if Ollama is available and get list of models.
        
        Returns:
            Dict with status and model list.
        """
        try:
            # Try to get list of models from Ollama
            response = self.session.get("http://localhost:11434/api/tags", timeout=5)
            
            if response.status_code == 200:
                models_data = response.json()
                models = [model["name"] for model in models_data.get("models", [])]
                return {
                    "available": True,
                    "models": models
                }
            else:
                return {
                    "available": False,
                    "error": f"Ollama returned status code {response.status_code}"
                }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }
    
    def generate_sequence(self, parameters, callback, progress_callback=None):
        """Generate a test sequence.
        
        Args:
            parameters: Dictionary of spring parameters.
            callback: Callback function to call with results.
            progress_callback: Callback function for progress updates.
            
        Returns:
            Nothing. Results are passed to the callback function.
        """
        # Cancel any existing operation
        self.cancel_generation()
        
        # Create a worker thread
        self.current_worker = OllamaAPIClientWorker(
            self, parameters, self.model, self.temperature, self.max_retries
        )
        
        # Connect signals
        self.current_worker.finished.connect(callback)
        if progress_callback:
            self.current_worker.progress.connect(progress_callback)
            self.current_worker.status.connect(lambda msg: print(f"Status: {msg}"))
        
        # Start the thread
        self.current_thread = threading.Thread(target=self.current_worker.run)
        self.current_thread.daemon = True
        self.current_thread.start()
    
    def generate_sequence_async(self, parameters, 
                            callback=None, 
                            progress_callback=None, 
                            status_callback=None,
                            model=None,
                            temperature=None,
                            max_retries=None):
        """Generate a test sequence asynchronously.
        
        Args:
            parameters: Dictionary of spring parameters.
            callback: Function to call with the result.
            progress_callback: Function to call with progress updates.
            status_callback: Function to call with status updates.
            model: Model name (optional, uses default if not provided).
            temperature: Temperature setting (optional, uses default if not provided).
            max_retries: Maximum retry attempts (optional, uses default if not provided).
            
        Returns:
            A tuple of (DataFrame, error_message). DataFrame is empty if an error occurred.
        """
        # Use provided parameters if given, otherwise use defaults
        actual_model = model or self.model
        actual_temperature = temperature or self.temperature
        actual_max_retries = max_retries or self.max_retries
        
        # Cancel any existing operation
        self.cancel_generation()
        
        # Create a worker thread
        self.current_worker = OllamaAPIClientWorker(
            self, parameters, actual_model, actual_temperature, actual_max_retries
        )
        
        # Connect signals
        if callback:
            self.current_worker.finished.connect(callback)
        if progress_callback:
            self.current_worker.progress.connect(progress_callback)
        if status_callback:
            self.current_worker.status.connect(status_callback)
        
        # Start the thread
        self.current_thread = threading.Thread(target=self.current_worker.run)
        self.current_thread.daemon = True
        self.current_thread.start()
        
        # If no callback is provided, wait for the result
        if not callback:
            # Create an event to signal completion
            event = threading.Event()
            result = [None, None]  # [DataFrame, error_message]
            
            # Define the callback function
            def internal_callback(df, error_message):
                result[0] = df
                result[1] = error_message
                event.set()
            
            # Connect the callback
            self.current_worker.finished.connect(internal_callback)
            
            # Wait for the result
            event.wait()
            
            # Return the result
            return result
    
    def cancel_generation(self):
        """Cancel the current generation."""
        if self.current_worker:
            self.current_worker.cancel()
        
        # Clean up
        self.current_worker = None
        self.current_thread = None
    
    def cancel_current_operation(self):
        """Alias for cancel_generation to maintain interface compatibility with TogetherAPIClient."""
        self.cancel_generation()
    
    def add_to_chat_memory(self, message):
        """Add a message to the chat memory.
        
        Args:
            message: The message to add.
            
        Returns:
            Nothing.
        """
        self.chat_memory.append(message)
        
        # Keep only the most recent messages
        if len(self.chat_memory) > 10:
            self.chat_memory = self.chat_memory[-10:] 