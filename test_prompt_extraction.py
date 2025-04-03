"""
Test script specifically focused on extracting data from the text prompt.
"""
import os
import logging
from datetime import datetime
from models.data_models import TestSequence
from services.export_service_txt import extract_key_specifications, _extract_from_prompt_text

# Set up logging
logging.basicConfig(level=logging.DEBUG,
                   format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_prompt_extraction():
    """Test the extraction of specifications from a prompt text."""
    # Sample prompt text based on the user's example
    prompt_text = """Spring Specifications:
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
Component Type: Compression"""
    
    # Extract specifications from the prompt text
    specs = _extract_from_prompt_text(prompt_text)
    
    # Print the extracted values
    print("\nExtracted from prompt text:")
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
    
    # Now test with a full sequence
    params = {
        "Timestamp": "2025-04-03 09:45:06",
        "prompt": prompt_text,
        "specifications_status": "COMPLETE REQUIRED SPECIFICATIONS: All necessary spring specifications are set and valid. The specification includes 3 valid set points."
    }
    
    # Basic test rows
    rows = [
        {"Row": "0", "CMD": "ZF", "Description": "Zero Force", "Condition": "", "Unit": "", "Tolerance": ""},
        {"Row": "1", "CMD": "TH", "Description": "Search Contact", "Condition": "10", "Unit": "N", "Tolerance": ""},
        {"Row": "2", "CMD": "FL(P)", "Description": "Measure Free Length-Position", "Condition": "", "Unit": "mm", "Tolerance": "58(52.2,63.8)"},
    ]
    
    # Create a test sequence
    sequence = TestSequence(rows=rows, parameters=params, created_at=datetime.now())
    
    # Extract specifications using the full extraction function
    full_specs = extract_key_specifications(sequence)
    
    # Print the extracted values
    print("\nExtracted from full sequence:")
    print(f"  Part Name: '{full_specs['part_name']}'")
    print(f"  Part Number: '{full_specs['part_number']}'")
    print(f"  Free Length: '{full_specs['free_length']}'")
    print(f"  Test Mode: '{full_specs['test_mode']}'")
    print(f"  Safety Limit: '{full_specs['safety_limit']}'")
    
    # Format it like the TXT output for verification
    output = f"""
1    Part Number     --    {full_specs['part_name']}
2    Model Number    --    {full_specs['part_number']}
3    Free Length     mm    {full_specs['free_length']}
<Test Sequence> N          --    {full_specs['test_mode']} {full_specs['safety_limit']} 100
"""
    print("\nFormatted Output:")
    print(output)

if __name__ == "__main__":
    test_prompt_extraction() 