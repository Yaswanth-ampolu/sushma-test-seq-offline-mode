"""
Tool to capture the actual parameters from a sequence for debugging.
Add this to your application temporarily to capture the data.
"""
import json
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def capture_sequence_data(sequence, filename="captured_sequence_data.json"):
    """
    Capture the parameters from a sequence to a JSON file for debugging.
    Add this to your export_sequence function to capture the actual data.
    
    Example usage:
        # In export_service.py or where you handle the export
        from capture_data import capture_sequence_data
        
        def export_sequence(self, sequence, file_path, format_name=None):
            # Capture the data for debugging
            capture_sequence_data(sequence)
            
            # Rest of your export code...
    """
    try:
        # Convert sequence parameters to a serializable format
        params = sequence.parameters
        
        # Create a structure with all relevant information
        data = {
            "parameters": params,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rows_count": len(sequence.rows),
            "export_format": "TXT"
        }
        
        # Create captures directory if it doesn't exist
        os.makedirs("captures", exist_ok=True)
        
        # Save to file with timestamp to avoid overwriting
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        full_filename = f"captures/{timestamp}_{filename}" 
        
        with open(full_filename, "w") as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Captured sequence data to {full_filename}")
        print(f"Captured sequence data to {full_filename}")
        
        return True
    except Exception as e:
        logger.error(f"Error capturing sequence data: {e}")
        return False

# Example of how to add this to your code
"""
# In export_service.py or where you handle the export
from capture_data import capture_sequence_data

# Original function
def export_sequence(self, sequence, file_path, format_name=None):
    # Capture the data when exporting a sequence
    capture_sequence_data(sequence)
    
    # Rest of your export code...
"""

if __name__ == "__main__":
    print("This is a utility module to capture sequence data.")
    print("Import this module and call capture_sequence_data() from your export function.")
    print("Example usage:")
    print("  from capture_data import capture_sequence_data")
    print("  capture_sequence_data(sequence)  # Add this to your export_sequence function") 