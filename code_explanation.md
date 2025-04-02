# Spring Test App Code Explanation

This document provides a detailed explanation of the Spring Test App codebase, with a particular focus on how messages are processed and how the AI integration works.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Message Processing Flow](#message-processing-flow)
3. [AI Integration](#ai-integration)
4. [Response Handling](#response-handling)
5. [Data Models](#data-models)
6. [Key Components](#key-components)
7. [Scrag Command Parsing Enhancement](#scrag-command-parsing-enhancement)
8. [UI Enhancements](#ui-enhancements)

## Architecture Overview

The Spring Test App follows a modular architecture with clear separation of concerns:

- **UI Layer**: Components like `ChatPanel` and `CollapsibleSidebar` that handle user interactions
- **Service Layer**: Services like `ChatService` and `SequenceGenerator` that handle business logic
- **Data Layer**: Data models like `ChatMessage` and `TestSequence` that represent application data
- **Utility Layer**: Utilities like `APIClient` that handle external communication

The application uses PyQt5 for the UI and follows a signal-based approach for asynchronous operations, ensuring the UI remains responsive during API calls or computation-intensive tasks.

## Message Processing Flow

### 1. User Input Capture

The message processing begins in the `ChatPanel` class when the user enters text and clicks the send button:

```python
def on_send_clicked(self):
    # Get user input
    user_input = self.user_input.toPlainText()
    
    # Check if input is empty
    if not user_input:
        QMessageBox.warning(self, "Missing Input", "Please enter your request.")
        return
    
    # Add user message to chat history
    self.chat_service.add_message("user", user_input)
    
    # Clear the input field immediately after sending
    self.user_input.clear()
    
    # Refresh chat display
    self.refresh_chat_display()
    
    # Process the message
    # ...
```

### 2. Input Analysis and Spring Specification Detection

The app analyzes the user input to detect if it contains spring specifications:

```python
# Check if the input contains spring specifications and parse them
contains_specs = self.parse_spring_specs(user_input)

# If specs were parsed, update the sequence generator
if contains_specs:
    # Get the updated specification and set it in the sequence generator
    updated_spec = self.settings_service.get_spring_specification()
    self.sequence_generator.set_spring_specification(updated_spec)
    
    # Add a note to the chat about using the parsed specifications
    self.chat_service.add_message(
        "assistant",
        "I'll use the current spring specifications for this request."
    )
    self.refresh_chat_display()
```

The `parse_spring_specs` method uses regular expressions to extract spring specifications from the user's message, looking for patterns like:
- Part name, part number, and part ID
- Spring dimensions (free length, wire diameter, outer diameter)
- Set points (position and load measurements)

### 3. Parameter Preparation

Before sending the message to the AI, the app prepares the parameters:

```python
# Extract parameters from user input
parameters = extract_parameters(user_input)

# Add the original prompt to parameters if not already there
if "prompt" not in parameters:
    parameters["prompt"] = user_input

# Include spring specification in the prompt if available and enabled
spring_spec = self.sequence_generator.get_spring_specification()
if spring_spec and spring_spec.enabled:
    # Add specification text to the prompt if not already included
    if 'prompt' in parameters:
        spec_text = spring_spec.to_prompt_text()
        if spec_text not in parameters['prompt']:
            parameters['prompt'] = f"{spec_text}\n\n{parameters['prompt']}"
```

The `SequenceGenerator` further enhances the parameters with calculated values based on spring physics:

```python
def _prepare_parameters_with_specification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
    if not self.spring_specification or not self.spring_specification.enabled:
        return parameters
    
    # Create a new parameters dictionary
    updated_params = parameters.copy()
    
    # Calculate optimal speeds based on spring characteristics
    speeds = self.calculate_optimal_speeds(self.spring_specification)
    
    # Add spring specification as context
    if 'prompt' in updated_params:
        spec_text = self.spring_specification.to_prompt_text()
        updated_params['prompt'] = f"{spec_text}\n\n{updated_params['prompt']}"
    
    # Add additional parameters with detailed spring specs
    updated_params['spring_specification'] = {
        'part_name': self.spring_specification.part_name,
        # ... other properties
        'optimal_speeds': speeds
    }
    
    return updated_params
```

### 4. AI Request Initialization

The app starts the AI request asynchronously to avoid freezing the UI:

```python
def start_generation(self, parameters):
    # Set generating state
    self.set_generating_state(True)
    
    # Reset progress and status
    self.progress_bar.setValue(0)
    self.status_label.setText("Starting generation...")
    
    # Start async generation
    self.sequence_generator.generate_sequence_async(parameters)
```

## AI Integration

### 1. API Client Setup

The core of the AI integration is the `APIClient` class, which handles communication with the AI provider:

```python
class APIClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.last_raw_response = ""
        self.chat_memory = []
        self.request_history = []
        self.session = requests.Session()
        self.current_worker = None
        self.current_thread = None
```

### 2. Asynchronous Request Processing

The app uses a worker thread to make API requests without blocking the UI:

```python
def generate_sequence_async(self, parameters: Dict[str, Any], 
                         callback: Callable[[pd.DataFrame, str], None],
                         progress_callback: Optional[Callable[[int], None]] = None,
                         status_callback: Optional[Callable[[str], None]] = None,
                         model: str = DEFAULT_MODEL, 
                         temperature: float = DEFAULT_TEMPERATURE,
                         max_retries: int = 3) -> None:
    # Cancel any existing operation
    self.cancel_current_operation()
    
    # Create a worker
    self.current_worker = APIClientWorker(
        self, parameters, model, temperature, max_retries
    )
    
    # Connect signals
    self.current_worker.finished.connect(callback)
    if progress_callback:
        self.current_worker.progress.connect(progress_callback)
    if status_callback:
        self.current_worker.status.connect(status_callback)
    
    # Create a thread for the worker
    self.current_thread = threading.Thread(target=self.current_worker.run)
    self.current_thread.daemon = True
    
    # Start the thread
    self.current_thread.start()
```

### 3. API Request Construction

The API request is formatted using templates that guide the AI to produce structured responses:

```python
# Create payload
payload = {
    "model": self.model,
    "messages": [
        {"role": "system", "content": SYSTEM_PROMPT_TEMPLATE},
        {"role": "user", "content": user_prompt}
    ],
    "temperature": self.temperature
}
```

The system prompt template (defined in `constants.py`) provides detailed instructions to the AI on how to format its responses for spring testing sequences:

```python
SYSTEM_PROMPT_TEMPLATE = """
You are an expert AI assistant specialized in spring force testing systems, generating precise test sequences for engineers.

HYBRID RESPONSE FORMAT:
You can respond in three ways depending on the user's intent:
1. PLAIN TEXT ONLY: For general questions, conversations, or analysis without sequence data
2. JSON ARRAY ONLY: For simple requests for new test sequences
3. HYBRID FORMAT: For analysis requests that require both explanation and sequence data...
"""
```

## Response Handling

### 1. Response Parsing

The app can handle three different response formats from the AI:

```python
# Check for hybrid response format with both text and sequence data
sequence_data_start = "---SEQUENCE_DATA_START---"
sequence_data_end = "---SEQUENCE_DATA_END---"

if sequence_data_start in response_text and sequence_data_end in response_text:
    # This is a hybrid response with both text and sequence data
    # Extract the parts
    parts = response_text.split(sequence_data_start)
    conversation_text = parts[0].strip()
    
    # Extract the sequence data
    seq_parts = parts[1].split(sequence_data_end)
    sequence_json_text = seq_parts[0].strip()
    
    # Process both conversation and sequence data
    # ...
    
# Handle JSON-only responses (sequence data without conversation)
elif response_text.strip().startswith("[") and response_text.strip().endswith("]"):
    # Parse as JSON array
    # ...
else:
    # No sequence data found - this was a conversational response
    # Create a custom message-only DataFrame
    message_df = pd.DataFrame([{"Row": "CHAT", "CMD": "CHAT", "Description": response_text}])
    df = message_df
```

### 2. Response Signal Emission

When the response processing is complete, the worker emits a signal with the results:

```python
# Always return df - if it's empty or contains a CHAT row, will be handled correctly by the receiver
self.finished.emit(df, error_message)
```

### 3. Response Handling in Sequence Generator

The `SequenceGenerator` class processes the raw response from the API and transforms it into a usable format:

```python
def _on_sequence_generated(self, df: pd.DataFrame, error_msg: str) -> None:
    # Check if this is a chat message (has a CHAT row)
    if not df.empty and "CHAT" in df["Row"].values:
        # For chat messages, just pass the DataFrame directly
        self.sequence_generated.emit(df, error_msg)
        return
        
    sequence = None
    
    if not df.empty:
        # Create TestSequence object
        sequence = TestSequence(
            rows=df.to_dict('records'),
            parameters=self.last_parameters
        )
        
        # Save sequence for reference
        self.last_sequence = sequence
        
        # Add to history
        self.history.append(sequence)
        if len(self.history) > 10:  # Keep history limited
            self.history = self.history[-10:]
    
    # Emit signal
    self.sequence_generated.emit(sequence, error_msg)
```

### 4. Chat Panel Response Processing

Finally, the `ChatPanel` handles the response based on its type:

```python
def on_sequence_generated_async(self, sequence, error):
    # Reset generating state
    self.set_generating_state(False)
    
    # Check if sequence is None or empty
    if sequence is None or (isinstance(sequence, pd.DataFrame) and sequence.empty):
        # Handle error case
        # ...
        return
    
    # Handle different types of sequence objects properly
    if isinstance(sequence, pd.DataFrame):
        # Check if it has a CHAT row (for conversation or hybrid responses)
        chat_rows = sequence[sequence["Row"] == "CHAT"]
        
        # If we have chat content, display it
        if not chat_rows.empty:
            chat_message = chat_rows["Description"].values[0]
            self.chat_service.add_message("assistant", chat_message)
            self.refresh_chat_display()
        
        # Check if we also have actual sequence rows
        sequence_rows = sequence[sequence["Row"] != "CHAT"]
        if not sequence_rows.empty:
            # Create TestSequence object and emit
            # ...
    
    elif hasattr(sequence, 'rows') and hasattr(sequence, 'parameters'):
        # It's a TestSequence object - handle accordingly
        # ...
    else:
        # Unknown object type - show error
        # ...
```

## Data Models

The app uses several data models to represent different types of information:

### 1. ChatMessage

```python
@dataclass
class ChatMessage:
    """Represents a single chat message in the conversation."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
```

### 2. TestSequence

```python
@dataclass
class TestSequence:
    """Represents a generated test sequence with metadata."""
    rows: List[Dict[str, Any]]
    parameters: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)
    name: Optional[str] = None
```

### 3. SpringSpecification

```python
@dataclass
class SpringSpecification:
    """Specifications for a spring to be tested."""
    part_name: str = "Demo Spring"
    part_number: str = "Demo Spring-1"
    part_id: int = 28
    free_length_mm: float = 58.0
    coil_count: float = 7.5
    wire_dia_mm: float = 3.0
    outer_dia_mm: float = 32.0
    set_points: List[SetPoint] = field(default_factory=list)
    safety_limit_n: float = 300.0
    unit: str = "mm"  # mm or inch
    enabled: bool = True
```

## Key Components

### ChatService

The `ChatService` manages the chat history and provides methods for adding, retrieving, and saving messages:

```python
def add_message(self, role: str, content: str) -> ChatMessage:
    """Add a message to the chat history."""
    message = ChatMessage(role=role, content=content)
    self.history.append(message)
    
    # Limit history size
    if len(self.history) > self.max_history:
        self.history = self.history[-self.max_history:]
    
    return message
```

### ChatPanel

The `ChatPanel` is the UI component that displays the chat history and handles user input:

```python
def refresh_chat_display(self):
    """Refresh the chat display with current history."""
    self.chat_display.clear()
    
    # Get chat history
    history = self.chat_service.get_history()
    
    # Display each message
    for message in history:
        if message.role == "user":
            self.chat_display.append(f"<b>{USER_ICON} You:</b>")
            self.chat_display.append(message.content)
            self.chat_display.append("")
        else:
            self.chat_display.append(f"<b>{ASSISTANT_ICON} Assistant:</b>")
            self.chat_display.append(message.content)
            self.chat_display.append("")
```

### SequenceGenerator

The `SequenceGenerator` processes user input and generates test sequences by communicating with the AI:

```python
def generate_sequence_async(self, parameters: Dict[str, Any]) -> None:
    """Generate a test sequence based on parameters asynchronously."""
    # Save parameters for reference
    self.last_parameters = parameters.copy()
    
    # Add spring specification to parameters
    parameters_with_spec = self._prepare_parameters_with_specification(parameters)
    
    # Start async generation
    self.api_client.generate_sequence_async(
        parameters_with_spec,
        self._on_sequence_generated,
        self.progress_updated.emit,  # Forward progress signal
        self.status_updated.emit     # Forward status signal
    )
```

### APIClient

The `APIClient` handles communication with the AI service and processes the responses:

```python
def run(self):
    # Format parameter text for prompt
    parameter_text = format_parameter_text(self.parameters)
    
    # Get the original user prompt
    original_prompt = self.parameters.get('prompt', '')
    
    # Create user prompt with instructions
    user_prompt = f"""
{parameter_text}

My message: {original_prompt}

IMPORTANT - RESPONSE FORMAT:
- Use your natural language understanding to decide how to respond to my request
- For NEW test sequence requests: Include a JSON array with the required test sequence format
- For analysis requests about EXISTING sequences: Provide conversational analysis in plain text 
- You can COMBINE both formats when appropriate
"""
    
    # Make API request and handle response
    # ...
```

## Conclusion

The Spring Test App demonstrates a sophisticated approach to integrating AI capabilities into a desktop application. The message processing flow is well-designed with clear separation of concerns:

1. The UI layer captures user input and displays responses
2. The service layer processes input, communicates with the AI, and transforms responses
3. The data layer provides structured representations of messages and sequences
4. The utility layer handles the technical details of API communication

This architecture allows the application to provide a responsive user experience while leveraging the power of AI for generating complex test sequences and answering user queries. 

## Scrag Command Parsing Enhancement

### Problem Statement

The Spring Test App encountered an issue when parsing test sequences containing Scrag commands with references in the format "Rxx,y" (e.g., "R03,2"). The comma in these references was being interpreted as a cell separator during parsing, causing the value to be split across multiple cells, disrupting the integrity of the sequence data.

### Technical Details of the Fix

To address this parsing issue, we enhanced the parsing logic in both the chat panel (`ui/chat_components/chat_panel.py`) and the Together API client (`utils/together_api_client.py`). The key improvements include:

#### 1. Cell Position Tracking

We added cell index tracking to recognize the specific position of each cell in the row:

```python
cell_index = 0  # Track which cell position we're in
found_scrag_cmd = False  # Flag to track if we've seen "Scrag" in the CMD position
```

When processing each comma in the input, we now increment the cell index to maintain awareness of which column we're currently handling:

```python
cells.append(completed_cell)
current_cell = ""
cell_index += 1
```

#### 2. Command Type Detection

We implemented detection of Scrag commands in the CMD field (the 2nd column):

```python
# Check if we just processed the CMD cell and it's a Scrag command
if cell_index == 1 and completed_cell == "Scrag":
    found_scrag_cmd = True
    print(f"DEBUG: Found Scrag command in CMD position")
```

#### 3. Pattern-Based Condition Detection

We use regular expressions to detect when a cell in the condition field (4th column) contains a Scrag reference:

```python
# Special case for Scrag command format "Rxx,y" in the Condition field (4th column)
if (found_scrag_cmd and cell_index == 3 and 
    completed_cell and 
    (re.match(r'^"?R\d+$', completed_cell) or  # Pattern is "R" followed by digits (like R03)
     re.match(r'^"?R\d+,\d*"?$', completed_cell))):  # Pattern already has comma (like R03,2)
    # This is a reference to another row in Scrag command, keep it intact
    current_cell += char
    print(f"DEBUG: Keeping comma in Scrag condition: {current_cell}")
```

#### 4. Second Comma Detection

We added logic to detect when the Scrag condition is complete (after reaching the pattern "Rxx,y"), ensuring that subsequent commas are properly treated as cell separators:

```python
# Check if this is the second comma for Scrag
if re.match(r'^"?R\d+,\d+$', current_cell.strip()):
    # We've already got the full R03,2 pattern, next comma should be a separator
    cells.append(current_cell.strip())
    current_cell = ""
    cell_index += 1
```

#### 5. Trailing Comma Cleanup

We implemented cleanup of any trailing commas that might appear in the parsed values:

```python
# Remove quotes around cells if present
for i in range(len(cells)):
    if cells[i].startswith('"') and cells[i].endswith('"'):
        cells[i] = cells[i][1:-1]
    # Also clean up any trailing commas from Scrag commands
    if cells[i].endswith(","):
        cells[i] = cells[i][:-1]
```

#### 6. Improved Sequence Generation

In the `test_sequence_sample.py` script, we enhanced the sequence generation code to properly format Scrag conditions with quotation marks when needed:

```python
is_scrag_condition = (field == "Condition" and row["CMD"] == "Scrag" and 
                      re.match(r'^R\d+,\d+$', str(value)) if value else False)

if value and ("," in str(value) or is_scrag_condition):
    # Make sure we don't double-quote
    if not (str(value).startswith('"') and str(value).endswith('"')):
        value = f'"{value}"'
```

### Testing Approach

We developed a comprehensive test script (`test_parser_fixed.py`) to verify the parsing improvements. This script tests multiple formats:

1. Standard row without commas
2. Rows with quoted tolerance values containing commas
3. Rows with Scrag conditions with commas (both quoted and unquoted)
4. Rows with both tolerance and Scrag condition values containing commas

The test results confirmed that our parsing logic correctly preserves the integrity of "Rxx,y" values in Scrag commands, ensuring they remain in a single cell during parsing.

### Benefits of the Enhancement

These parsing improvements provide several benefits:

1. **Data Integrity**: Scrag command references like "R03,2" are correctly preserved as a single value, maintaining the integrity of the test sequence.

2. **Proper Sequence Execution**: With correctly parsed values, the spring testing machine can properly execute Scrag commands with the intended parameters.

3. **Improved User Experience**: Users can now input and display sequence data with Scrag commands without concerns about data corruption.

4. **Robust Error Handling**: The enhanced parsing logic includes improved error handling and debugging output to facilitate troubleshooting of any future parsing issues.

5. **Compatibility**: The solution maintains compatibility with both API-generated sequences and manually entered sequences, ensuring consistent behavior across different input methods.

### Implementation Notes

The enhanced parsing logic was implemented in multiple places to ensure consistent behavior throughout the application:

1. In `ui/chat_components/chat_panel.py` for manually entered sequences
2. In `utils/together_api_client.py` for API-generated sequences
3. In `test_sequence_sample.py` for generating sample sequences with proper formatting

This comprehensive approach ensures that Scrag command values are correctly handled at all points in the application's workflow, from input to display and export.

## UI Enhancements

### Sidebar Components

The Spring Test App features two key sidebar components that provide rich visualization and interaction capabilities:

1. **WebEngineSidebar**: A modern sidebar component that uses PyQt's WebEngine capabilities for enhanced styling and animations. This component is used in the main chat interface.

2. **CollapsibleSidebar**: A simpler sidebar implementation focused on providing collapsible behavior and basic content display. This is used in various contexts throughout the application.

Both sidebar components fulfill the same essential purpose: displaying test sequence information, spring parameters, and specifications, while allowing the user to export sequences in various formats.

### Sequence and JSON View Integration

A recent enhancement to the application combines the previously separate Sequence and JSON tabs into a unified view with a dropdown selector. This improvement streamlines the user interface while maintaining full functionality.

#### Implementation Details

The integration was implemented in both sidebar classes:

1. In the `WebEngineSidebar` and `CollapsibleSidebar` classes:
   - The separate JSON tab was eliminated
   - A view selector dropdown was added to the Sequence tab header
   - A `QStackedWidget` was introduced to manage switching between table and JSON views
   - Methods were added to handle view selection changes

```python
# Header with title and view selector
header_layout = QHBoxLayout()

# Table header
sequence_title = QLabel("Generated Test Sequence")
header_layout.addWidget(sequence_title)

# Add view selector dropdown
header_layout.addStretch()
view_selector_label = QLabel("View:")
header_layout.addWidget(view_selector_label)

self.view_selector = QComboBox()
self.view_selector.addItem("Table")
self.view_selector.addItem("JSON")
self.view_selector.setFixedWidth(80)
self.view_selector.currentIndexChanged.connect(self.on_view_selector_changed)
header_layout.addWidget(self.view_selector)
```

#### View Selection Mechanism

The view selection is managed through a simple index-based approach:

```python
def on_view_selector_changed(self):
    """Handle view selector changes."""
    # Get current index
    current_index = self.view_selector.currentIndex()
    
    # Show the selected view
    self.sequence_stack.setCurrentIndex(current_index)
    
    # Log the change
    logger.debug("Changed view to: %s", self.view_selector.currentText())
```