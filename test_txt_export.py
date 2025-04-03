"""
Test script for the TXT export functionality.
Run this script to verify the TXT export with different parameter combinations.
"""
import os
import sys
import logging
from datetime import datetime
from models.data_models import TestSequence, SpringSpecification
from services.export_service import ExportService

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def create_test_sequence():
    """Create a test sequence with various parameter formats."""
    # Create a basic sequence
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": "", "Speed rpm": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": "", "Speed rpm": ""},
        {"Row": "2", "CMD": "FL(P)", "Description": "Measure Free Length-Position", "Condition": "", "Unit": "mm", "Tolerance": "58(52.2,63.8)", "Speed rpm": ""},
        {"Row": "3", "CMD": "Mv(P)", "Description": "Move to Position L1", "Condition": "40", "Unit": "mm", "Tolerance": "", "Speed rpm": ""},
        {"Row": "4", "CMD": "Mv(P)", "Description": "Move to Position L2", "Condition": "33", "Unit": "mm", "Tolerance": "", "Speed rpm": ""},
        {"Row": "5", "CMD": "Scrag", "Description": "Scragging", "Condition": "R04,2", "Unit": "", "Tolerance": "", "Speed rpm": ""},
    ]
    
    # Create different parameter combinations to test
    
    # Test 1: Basic parameters in top level
    params1 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "part_name": "Test Spring 1",
        "part_number": "TST-001",
        "free_length": "58.0",
        "test_mode": "Height Mode",
        "safety_limit": "300"
    }
    
    # Test 2: Parameters in spring_specification dictionary
    spring_spec = {
        "part_name": "Test Spring 2",
        "part_number": "TST-002",
        "free_length_mm": "60.0",
        "test_mode": "Deflection Mode",
        "safety_limit_n": "350"
    }
    params2 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "spring_specification": spring_spec
    }
    
    # Test 3: Parameters in basic_info dictionary
    basic_info = {
        "part_name": "Test Spring 3",
        "part_number": "TST-003",
        "free_length": "62.0",
        "test_mode": "Force Mode",
        "safety_limit": "400"
    }
    params3 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "basic_info": basic_info
    }
    
    # Test 4: Mixed sources with one source missing some values
    params4 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "part_name": "Test Spring 4",
        # part_number missing at top level
        "free_length": "63.0",
        "spring_specification": {
            # part_name missing in spring_specification
            "part_number": "TST-004",
            # free_length missing in spring_specification
            "test_mode": "Height Mode",
            "safety_limit_n": "450"
        }
    }
    
    # Test 5: Deeply nested structure simulating complex app state
    params5 = {
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "chat_message": "Here's your test sequence",
        "spring_specification": {
            "basic_info": {
                "part_name": "Test Spring 5",
                "part_number": "TST-005",
                "free_length": "65.0"
            },
            "test_mode": "Height Mode",
            "safety_limit_n": "500"
        }
    }
    
    # Create sequences with each parameter set
    sequences = [
        TestSequence(rows=rows, parameters=params1, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params2, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params3, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params4, created_at=datetime.now()),
        TestSequence(rows=rows, parameters=params5, created_at=datetime.now()),
    ]
    
    return sequences

def main():
    """Main test function."""
    # Create export service
    export_service = ExportService()
    
    # Create test sequences
    sequences = create_test_sequence()
    
    # Create output directory if it doesn't exist
    if not os.path.exists("test_output"):
        os.makedirs("test_output")
    
    # Export each sequence to TXT
    for i, sequence in enumerate(sequences):
        output_path = f"test_output/test_sequence_{i+1}.txt"
        success, error = export_service.export_sequence(sequence, output_path, "TXT")
        
        if success:
            logger.info(f"Successfully exported Test {i+1} to {output_path}")
            # Print the file content
            with open(output_path, "r") as f:
                logger.info(f"File content for Test {i+1}:\n{f.read()}")
        else:
            logger.error(f"Failed to export Test {i+1}: {error}")

if __name__ == "__main__":
    main() 