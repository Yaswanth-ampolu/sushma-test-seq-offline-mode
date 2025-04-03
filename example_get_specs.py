"""
Example script showing how to extract key specifications from a test sequence.
"""
import logging
from datetime import datetime
from models.data_models import TestSequence
from services.export_service_txt import extract_key_specifications

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Example of retrieving specifications from a test sequence."""
    # Create a basic sequence
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": ""},
        {"Row": "2", "CMD": "FL(P)", "Description": "Measure Free Length", "Condition": "", "Unit": "mm", "Tolerance": "58(52.2,63.8)"}
    ]
    
    # Create a sequence with parameters in different formats
    
    # Example 1: Simple flat parameters
    params1 = {
        "part_name": "Flat Spring Example",
        "part_number": "FS-001",
        "free_length": "58.0",
        "test_mode": "Height Mode",
        "safety_limit": "300"
    }
    sequence1 = TestSequence(rows=rows, parameters=params1, created_at=datetime.now())
    
    # Example 2: Nested parameters
    params2 = {
        "spring_specification": {
            "basic_info": {
                "part_name": "Nested Spring Example",
                "part_number": "NS-002",
                "free_length_mm": "60.0"
            },
            "test_mode": "Deflection Mode",
            "safety_limit_n": "350"
        }
    }
    sequence2 = TestSequence(rows=rows, parameters=params2, created_at=datetime.now())
    
    # Retrieve specifications from each sequence
    specs1 = extract_key_specifications(sequence1)
    specs2 = extract_key_specifications(sequence2)
    
    # Display the extracted specifications
    print("\nExtracted specifications from sequence 1:")
    print(f"Part Name: {specs1['part_name']}")
    print(f"Part Number: {specs1['part_number']}")
    print(f"Free Length: {specs1['free_length']} mm")
    print(f"Test Mode: {specs1['test_mode']}")
    print(f"Safety Limit: {specs1['safety_limit']} N")
    
    print("\nExtracted specifications from sequence 2:")
    print(f"Part Name: {specs2['part_name']}")
    print(f"Part Number: {specs2['part_number']}")
    print(f"Free Length: {specs2['free_length']} mm")
    print(f"Test Mode: {specs2['test_mode']}")
    print(f"Safety Limit: {specs2['safety_limit']} N")

if __name__ == "__main__":
    main() 