"""
Debug script for TXT export issues.
This script tests the extract_key_specifications function with a production-like test case.
"""
import os
import logging
import json
from datetime import datetime
from models.data_models import TestSequence
from services.export_service_txt import extract_key_specifications

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("debug_export.log")
    ]
)
logger = logging.getLogger(__name__)

def create_test_sequence_from_actual_data():
    """Create a test sequence with parameters that mirror the actual production data."""
    # Basic test rows (from your example)
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": ""},
        {"Row": "2", "CMD": "FL(P)", "Description": "Measure Free Length-Position", "Condition": "", "Unit": "mm", "Tolerance": "58(52.2,63.8)"},
        {"Row": "3", "CMD": "Mv(P)", "Description": "Move to Position L1", "Condition": "40", "Unit": "mm", "Tolerance": ""},
        {"Row": "4", "CMD": "Mv(P)", "Description": "Move to Position L2", "Condition": "33", "Unit": "mm", "Tolerance": ""},
        {"Row": "5", "CMD": "Scrag", "Description": "Scragging", "Condition": "R04,2", "Unit": "", "Tolerance": ""},
    ]
    
    # Create all kinds of parameter combinations we might encounter
    # These structures mirror what we might see in the actual application
    parameter_sets = [
        # Test 1: The standard format from your friend's code
        {
            "Specifications": {
                "part_name": "Standard Test Spring",
                "part_number": "ST-001",
                "free_length_mm": "58.0",
                "test_mode": "Height Mode",
                "safety_limit_n": "300"
            }
        },
        
        # Test 2: Another format that your application might use
        {
            "spring_specification": {
                "part_name": "Spring Spec Format",
                "part_number": "SS-002",
                "free_length_mm": "60.0",
                "test_mode": "Deflection Mode",
                "safety_limit_n": "350"
            }
        },
        
        # Test 3: Deeply nested format
        {
            "spring_specification": {
                "basic_info": {
                    "part_name": "Nested Format",
                    "part_number": "NF-003",
                    "free_length_mm": "62.0"
                },
                "test_mode": "Force Mode",
                "safety_limit_n": "400"
            }
        },
        
        # Test 4: Direct field access
        {
            "part_name": "Direct Field Format",
            "part_number": "DF-004",
            "free_length": "63.0",
            "test_mode": "Height Mode",
            "safety_limit": "450"
        },
        
        # Test 5: Camel case and mixed formats
        {
            "partName": "Camel Case Format",
            "partNumber": "CC-005",
            "freeLength": "64.0",
            "testMode": "Deflection Mode",
            "safetyLimit": "500"
        },
        
        # Test 6: Empty structure (simulate what might be causing your issue)
        {
            "parameters": { 
                "some_other_data": "Test data"
            },
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        
        # Test 7: Output from LLM with different naming
        {
            "springSpecification": {
                "basicInfo": {
                    "name": "LLM Output Spring",
                    "number": "LLM-007",
                    "length": "66.0"
                },
                "mode": "Height",
                "limit": "550"
            }
        },
        
        # Test 8: Structure with different capitalization
        {
            "SPECIFICATIONS": {
                "PART_NAME": "Uppercase Format",
                "PART_NUMBER": "UP-008",
                "FREE_LENGTH_MM": "67.0",
                "TEST_MODE": "Height Mode",
                "SAFETY_LIMIT_N": "600"
            }
        },
        
        # Test 9: ACTUAL FORMAT from the application - using prompt field
        {
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": """Spring Specifications:
Part Name: Demo Spring
Part Number: Demo Spring-1
ID: 28
Free Length: 58.0 mm
No of Coils: 7.5
Wire Dia: 3.0 mm
OD: 32.0 mm
Set Point-1 Position: 40.0 mm
Set Point-1 Load: 23.6±10.0% N
Set Point-2 Position: 33.0 mm
Set Point-2 Load: 34.14±10.0% N
Set Point-3 Position: 28.0 mm
Set Point-3 Load: 42.36±10.0% N
Safety Limit: 0.0 N
Displacement Unit: mm
Force Unit: N
Test Mode: Height Mode
Component Type: Compression""",
            "specifications_status": "COMPLETE REQUIRED SPECIFICATIONS: All necessary spring specifications are set and valid. The specification includes 3 valid set points."
        }
    ]
    
    # Create a sequence for each parameter set
    sequences = []
    for i, params in enumerate(parameter_sets):
        sequences.append(TestSequence(rows=rows, parameters=params, created_at=datetime.now()))
    
    # Also get a sequence from actual data if we have it
    try:
        if os.path.exists("sample_data.json"):
            with open("sample_data.json", "r") as f:
                actual_params = json.load(f)
                sequences.append(TestSequence(rows=rows, parameters=actual_params, created_at=datetime.now()))
    except Exception as e:
        logger.error(f"Could not load sample data: {e}")
    
    return sequences

def main():
    """Main debug function."""
    # Save your example sequence data for future diagnostics
    sample_output = """
1    Part Number     --    
2    Model Number    --    
3    Free Length     mm    
<Test Sequence> N          --    Height 300 100

ZF     Zero Force                                               
TH     Search Contact       10         N                        
FL(P)  Measure Free Length-Position            mm   58(52.2,63.8)       
Mv(P)  Move to Position L1  40         mm                       
Mv(P)  Move to Position L2  33         mm                       
Scrag  Scragging            R04,2                               
Mv(P)  Move to Position L2  33         mm                       
TH     Search Contact       10         N                        
FL(P)  Measure Free Length-Position            mm   58(52.2,63.8)       
Mv(P)  Move to Position L2  33         mm                       
Fr(P)  Force @ Position L2             N    34.14(30.726,37.554)
Mv(P)  Move to Position L1  40         mm                       
Fr(P)  Force @ Position L1             N    23.6(21.24,26.06)   
Mv(P)  Move to Position L3  28         mm                       
PMsg   User Message         Test Completed
"""
    with open("sample_output.txt", "w") as f:
        f.write(sample_output)
    
    # Create test sequences
    print("Creating test sequences...")
    sequences = create_test_sequence_from_actual_data()
    
    # Test extraction for each sequence
    for i, sequence in enumerate(sequences):
        print(f"\n======= Testing Extraction for Sequence {i+1} =======")
        print(f"Parameters: {sequence.parameters}")
        
        # Try the extraction
        specs = extract_key_specifications(sequence)
        
        # Print the extracted values
        print("\nExtracted Specifications:")
        print(f"  Part Name: '{specs['part_name']}'")
        print(f"  Part Number: '{specs['part_number']}'")
        print(f"  Free Length: '{specs['free_length']}'")
        print(f"  Test Mode: '{specs['test_mode']}'")
        print(f"  Safety Limit: '{specs['safety_limit']}'")
        
        # Format it like the TXT output for verification
        output = f"""
1    Part Number     --    {specs['part_name']}
2    Model Number    --    {specs['part_number']}
3    Free Length     mm    {specs['free_length']}
<Test Sequence> N          --    {specs['test_mode']} {specs['safety_limit']} 100
"""
        print("\nFormatted Output:")
        print(output)
    
    # Create a file to store extracted data
    with open("debug_output.txt", "w") as f:
        f.write("===== Extraction Results =====\n\n")
        for i, sequence in enumerate(sequences):
            f.write(f"======= Sequence {i+1} =======\n")
            f.write(f"Parameters: {sequence.parameters}\n\n")
            
            specs = extract_key_specifications(sequence)
            
            f.write("Extracted Specifications:\n")
            f.write(f"  Part Name: '{specs['part_name']}'\n")
            f.write(f"  Part Number: '{specs['part_number']}'\n")
            f.write(f"  Free Length: '{specs['free_length']}'\n")
            f.write(f"  Test Mode: '{specs['test_mode']}'\n")
            f.write(f"  Safety Limit: '{specs['safety_limit']}'\n\n")
            
            output = f"""
1    Part Number     --    {specs['part_name']}
2    Model Number    --    {specs['part_number']}
3    Free Length     mm    {specs['free_length']}
<Test Sequence> N          --    {specs['test_mode']} {specs['safety_limit']} 100
"""
            f.write("Formatted Output:\n")
            f.write(output)
            f.write("\n" + "="*50 + "\n\n")
    
    print("\nDebug output written to debug_output.txt")
    print("Log data written to debug_export.log")

if __name__ == "__main__":
    main() 