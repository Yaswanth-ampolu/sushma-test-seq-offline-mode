"""
Test script to verify that empty specifications remain empty without default values.
"""
import os
import logging
from datetime import datetime
from models.data_models import TestSequence
from services.export_service_txt import extract_key_specifications, export_txt

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_no_default_values():
    """Test that empty specifications remain empty without default values."""
    # Create a test sequence with minimal parameters
    params = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "part_name": "Test Spring",
        "part_number": "TS-001",
        "free_length": "50.0",
        # Deliberately not including test_mode and safety_limit
    }
    
    # Basic test rows
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": ""},
    ]
    
    # Create a test sequence
    sequence = TestSequence(rows=rows, parameters=params, created_at=datetime.now())
    
    # Extract specifications
    specs = extract_key_specifications(sequence)
    
    # Print the extracted values
    print("\nExtracted specifications:")
    print(f"  Part Name: '{specs['part_name']}'")
    print(f"  Part Number: '{specs['part_number']}'")
    print(f"  Free Length: '{specs['free_length']}'")
    print(f"  Test Mode: '{specs['test_mode']}' - Should be empty!")
    print(f"  Safety Limit: '{specs['safety_limit']}' - Should be empty!")
    
    # Format it like the TXT output for verification
    output = f"""
1    Part Number     --    {specs['part_name']}
2    Model Number    --    {specs['part_number']}
3    Free Length     mm    {specs['free_length']}
<Test Sequence> N          --    {specs['test_mode']} {specs['safety_limit']} 100
"""
    print("\nFormatted Output:")
    print(output)
    
    # Create a temporary file for testing the export
    temp_file = "test_no_defaults.txt"
    success, error = export_txt(sequence, temp_file)
    
    if success:
        print(f"\nExported to {temp_file}. File contents:")
        with open(temp_file, "r") as f:
            print(f.read())
    else:
        print(f"Export failed: {error}")

if __name__ == "__main__":
    print("Testing that empty specifications remain empty without default values...")
    test_no_default_values() 