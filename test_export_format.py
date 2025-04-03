"""
Test script for verifying the TXT export format matches requirements.
This script will create test sequences with different parameter structures
and export them to TXT format to check the output.
"""
import os
import logging
from datetime import datetime
from models.data_models import TestSequence
from services.export_service import ExportService
from services.export_service_txt import extract_key_specifications

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def create_test_sequences():
    """Create various test sequences with different parameter structures."""
    # Basic sequence rows
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": ""},
        {"Row": "2", "CMD": "FL(P)", "Description": "Measure Free Length", "Condition": "", "Unit": "mm", "Tolerance": "58(52.2,63.8)"}
    ]
    
    # Create different parameter combinations
    
    # Test 1: Parameters in Specifications dictionary (like in original exportservice.py)
    params1 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Specifications": {
            "part_name": "Test Spring 1",
            "part_number": "TS-001",
            "free_length_mm": "58.0",
            "test_mode": "Height Mode",
            "safety_limit_n": "300"
        }
    }
    
    # Test 2: Parameters directly in top level (direct access)
    params2 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "part_name": "Test Spring 2",
        "part_number": "TS-002",
        "free_length": "60.0",
        "test_mode": "Deflection Mode",
        "safety_limit": "350"
    }
    
    # Test 3: Parameters in spring_specification (like newer code)
    params3 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "spring_specification": {
            "part_name": "Test Spring 3",
            "part_number": "TS-003",
            "free_length_mm": "62.0",
            "test_mode": "Force Mode",
            "safety_limit_n": "400"
        }
    }
    
    # Create the sequences
    sequences = [
        TestSequence(rows=rows, parameters=params1, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params2, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params3, created_at=datetime.now())
    ]
    
    return sequences

def main():
    """Main function to test TXT export."""
    # Create export service
    export_service = ExportService()
    
    # Create test sequences
    sequences = create_test_sequences()
    
    # Ensure output directory exists
    if not os.path.exists("test_output"):
        os.makedirs("test_output")
    
    # Test extract_key_specifications function
    print("\nTesting specification extraction:")
    for i, sequence in enumerate(sequences):
        specs = extract_key_specifications(sequence)
        print(f"\nSequence {i+1} specifications:")
        print(f"  Part Name: '{specs['part_name']}'")
        print(f"  Part Number: '{specs['part_number']}'")
        print(f"  Free Length: '{specs['free_length']}'")
        print(f"  Test Mode: '{specs['test_mode']}'")
        print(f"  Safety Limit: '{specs['safety_limit']}'")
    
    # Export sequences to TXT
    print("\nExporting to TXT format:")
    for i, sequence in enumerate(sequences):
        output_path = f"test_output/test_sequence_{i+1}.txt"
        success, error = export_service.export_sequence(sequence, output_path, "TXT")
        
        if success:
            print(f"Successfully exported Sequence {i+1} to {output_path}")
            # Print the file content
            with open(output_path, "r") as f:
                content = f.read()
                print(f"\nFile content for Sequence {i+1}:\n{content}")
        else:
            print(f"Failed to export Sequence {i+1}: {error}")

if __name__ == "__main__":
    main() 