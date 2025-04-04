"""
TXT Export service for the Spring Test App.
Contains functions for exporting sequences to TXT format.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from models.data_models import TestSequence, SpringSpecification

# Set up logging
logger = logging.getLogger(__name__)

def _extract_nested_value(data: Dict, key_path: List[str], default_value: str = "") -> str:
    """Extract a value from a deeply nested dictionary.
    
    Args:
        data: The dictionary to extract from.
        key_path: List of keys to traverse.
        default_value: Default value to return if not found.
        
    Returns:
        The extracted value or default value.
    """
    current = data
    for key in key_path:
        if not isinstance(current, dict) or key not in current:
            return default_value
        current = current[key]
    
    if current is None or current in ('None', 'null', ''):
        return default_value
    
    return str(current).strip()

def _extract_parameter_value(params: Dict, *keys: str, default_value: str = "") -> str:
    """Extract a parameter value by trying multiple keys.
    
    Args:
        params: Dictionary containing parameters.
        *keys: One or more keys to try in order.
        default_value: Default value to return if not found.
        
    Returns:
        The value found or default value.
    """
    for key in keys:
        if key in params and params[key] is not None:
            value = params[key]
            if value not in ('None', 'null', None, ''):
                return str(value).strip()
    return default_value

def _flatten_dict(nested_dict, parent_key='', sep='_'):
    """Flatten a nested dictionary into a single-level dictionary.
    
    Args:
        nested_dict: Nested dictionary to flatten.
        parent_key: Key of parent.
        sep: Separator between parent and child keys.
        
    Returns:
        Flattened dictionary.
    """
    items = []
    for k, v in nested_dict.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def _extract_from_prompt_text(prompt_text: str) -> Dict[str, str]:
    """Extract specifications from a prompt text string.
    
    The prompt text format looks like:
    Spring Specifications:
    Part Name: Demo Spring
    Part Number: Demo Spring-1
    Free Length: 58.0 mm
    ...
    
    Args:
        prompt_text: The prompt text to extract specifications from.
        
    Returns:
        Dictionary containing key specifications.
    """
    result = {
        "part_name": "",
        "part_number": "",
        "free_length": "",
        "test_mode": "",
        "safety_limit": ""
    }
    
    if not prompt_text:
        return result
    
    try:
        # Look for each field in the text
        logger.debug(f"Extracting from prompt text:\n{prompt_text}")
        
        # Part Name
        part_name_match = None
        for pattern in ["Part Name:", "PartName:", "Name:"]:
            if pattern in prompt_text:
                part_name_start = prompt_text.find(pattern) + len(pattern)
                part_name_end = prompt_text.find("\n", part_name_start)
                if part_name_end > part_name_start:
                    part_name_match = prompt_text[part_name_start:part_name_end].strip()
                    break
        
        if part_name_match:
            result["part_name"] = part_name_match
            logger.debug(f"Found part_name in prompt text: {part_name_match}")
        
        # Part Number
        part_number_match = None
        for pattern in ["Part Number:", "PartNumber:", "Number:"]:
            if pattern in prompt_text:
                part_number_start = prompt_text.find(pattern) + len(pattern)
                part_number_end = prompt_text.find("\n", part_number_start)
                if part_number_end > part_number_start:
                    part_number_match = prompt_text[part_number_start:part_number_end].strip()
                    break
        
        if part_number_match:
            result["part_number"] = part_number_match
            logger.debug(f"Found part_number in prompt text: {part_number_match}")
        
        # Free Length
        free_length_match = None
        for pattern in ["Free Length:", "FreeLength:", "Length:"]:
            if pattern in prompt_text:
                free_length_start = prompt_text.find(pattern) + len(pattern)
                free_length_end = prompt_text.find("\n", free_length_start)
                if free_length_end > free_length_start:
                    free_length_text = prompt_text[free_length_start:free_length_end].strip()
                    # Extract just the numeric part if it includes units
                    if " mm" in free_length_text:
                        free_length_match = free_length_text.split(" mm")[0].strip()
                    else:
                        free_length_match = free_length_text
                    break
        
        if free_length_match:
            result["free_length"] = free_length_match
            logger.debug(f"Found free_length in prompt text: {free_length_match}")
        
        # Test Mode
        test_mode_match = None
        for pattern in ["Test Mode:", "TestMode:", "Mode:"]:
            if pattern in prompt_text:
                test_mode_start = prompt_text.find(pattern) + len(pattern)
                test_mode_end = prompt_text.find("\n", test_mode_start)
                if test_mode_end > test_mode_start:
                    test_mode_text = prompt_text[test_mode_start:test_mode_end].strip()
                    # Just get the first word
                    test_mode_match = test_mode_text.split()[0]
                    break
        
        if test_mode_match:
            result["test_mode"] = test_mode_match
            logger.debug(f"Found test_mode in prompt text: {test_mode_match}")
        
        # Safety Limit
        safety_limit_match = None
        for pattern in ["Safety Limit:", "SafetyLimit:", "Limit:"]:
            if pattern in prompt_text:
                safety_limit_start = prompt_text.find(pattern) + len(pattern)
                safety_limit_end = prompt_text.find("\n", safety_limit_start)
                if safety_limit_end > safety_limit_start:
                    safety_limit_text = prompt_text[safety_limit_start:safety_limit_end].strip()
                    # Extract just the numeric part if it includes units
                    if " N" in safety_limit_text:
                        safety_limit_match = safety_limit_text.split(" N")[0].strip()
                    else:
                        safety_limit_match = safety_limit_text
                    break
        
        if safety_limit_match and safety_limit_match != "0.0":
            result["safety_limit"] = safety_limit_match
            logger.debug(f"Found safety_limit in prompt text: {safety_limit_match}")
    
    except Exception as e:
        logger.error(f"Error extracting from prompt text: {str(e)}")
    
    return result

def extract_key_specifications(sequence: TestSequence) -> Dict[str, str]:
    """Extract key specifications from a test sequence.
    
    Args:
        sequence: The test sequence to extract specifications from.
        
    Returns:
        Dictionary containing key specifications (part_name, part_number, free_length, 
        test_mode, safety_limit).
    """
    # Initialize result dictionary with default values
    result = {
        "part_name": "",
        "part_number": "",
        "free_length": "",
        "test_mode": "",
        "safety_limit": ""
    }
    
    try:
        # Log the entire sequence parameters for debugging
        logger.debug(f"Extracting specifications from sequence - all parameters: {sequence.parameters}")
        
        # Extract all parameters from the sequence
        params = sequence.parameters
        
        # Check for prompt field first - this contains text-based specifications
        prompt_text = params.get("prompt", "")
        if prompt_text:
            # Extract specifications from the prompt text
            prompt_specs = _extract_from_prompt_text(prompt_text)
            
            # Copy values from prompt specs to result
            for key, value in prompt_specs.items():
                if value:  # Only copy non-empty values
                    result[key] = value
            
            # If we found all specifications in the prompt, return early
            if all(result.values()):
                logger.debug(f"Found all specifications in prompt text: {result}")
                return result
        
        # Create a flattened version of parameters for simpler access
        flat_params = _flatten_dict(params)
        logger.debug(f"Flattened parameters: {flat_params}")
        
        # Create a case-insensitive parameter dictionary for searching
        case_insensitive_params = {}
        for k, v in flat_params.items():
            case_insensitive_params[k.lower()] = v
        logger.debug(f"Case-insensitive parameters: {case_insensitive_params}")
        
        # Extract specifications from all possible locations
        specs_locations = [
            params.get("Specifications", {}),
            params.get("specifications", {}),
            params.get("spring_specification", {}), 
            params.get("Spring_Specification", {}),
            params.get("springSpecification", {})
        ]
        
        # Find the first non-empty specs dictionary
        specs = {}
        for loc in specs_locations:
            if loc and isinstance(loc, dict):
                specs = loc
                logger.debug(f"Found specifications at: {loc}")
                break
        
        # Also check specifically for "spring" object
        spring = params.get("spring", {})
        if spring and isinstance(spring, dict):
            logger.debug(f"Found spring object: {spring}")
            if not specs:
                specs = spring
        
        # Direct extraction from top-level params - try multiple variants of keys
        # Part Name
        part_name_keys = ["part_name", "partName", "part name", "name", "spring_name", "springName", "spring name", 
                          "PART_NAME", "PartName", "Part Name", "Name", "SPRING_NAME", "SpringName"]
        for key in part_name_keys:
            value = params.get(key, "")
            if value and value not in ('None', 'null', None, ''):
                result["part_name"] = str(value).strip()
                logger.debug(f"Found part_name directly with key '{key}': {value}")
                break
        
        # Part Number
        part_number_keys = ["part_number", "partNumber", "part number", "number", "spring_number", "springNumber", 
                           "spring number", "PART_NUMBER", "PartNumber", "Part Number", "Number", "SPRING_NUMBER", 
                           "SpringNumber", "model", "model_number", "modelNumber", "Model Number"]
        for key in part_number_keys:
            value = params.get(key, "")
            if value and value not in ('None', 'null', None, ''):
                result["part_number"] = str(value).strip()
                logger.debug(f"Found part_number directly with key '{key}': {value}")
                break
        
        # Free Length
        free_length_keys = ["free_length", "freeLength", "free length", "length", "free_length_mm", "freeLengthMm", 
                           "FREE_LENGTH", "FreeLength", "Free Length", "Length", "FREE_LENGTH_MM", "FreeLengthMm", 
                           "initial_length", "initialLength", "initial length", "spring_length", "springLength"]
        for key in free_length_keys:
            value = params.get(key, "")
            if value and value not in ('None', 'null', None, ''):
                result["free_length"] = str(value).strip()
                logger.debug(f"Found free_length directly with key '{key}': {value}")
                break
        
        # Check for specifications in case-insensitive flat dictionary
        if not result["part_name"]:
            for key in case_insensitive_params:
                if "part" in key.lower() and "name" in key.lower():
                    value = case_insensitive_params[key]
                    if value and value not in ('None', 'null', None, ''):
                        result["part_name"] = str(value).strip()
                        logger.debug(f"Found part_name in case-insensitive with key '{key}': {value}")
                        break
        
        if not result["part_number"]:
            for key in case_insensitive_params:
                if ("part" in key.lower() and "number" in key.lower()) or "model" in key.lower():
                    value = case_insensitive_params[key]
                    if value and value not in ('None', 'null', None, ''):
                        result["part_number"] = str(value).strip()
                        logger.debug(f"Found part_number in case-insensitive with key '{key}': {value}")
                        break
        
        if not result["free_length"]:
            for key in case_insensitive_params:
                if "free" in key.lower() and ("length" in key.lower() or "long" in key.lower()):
                    value = case_insensitive_params[key]
                    if value and value not in ('None', 'null', None, ''):
                        result["free_length"] = str(value).strip()
                        logger.debug(f"Found free_length in case-insensitive with key '{key}': {value}")
                        break
        
        # Also check spring_specification
        spring_spec = params.get("spring_specification", {})
        if spring_spec and not specs:
            specs = spring_spec
            logger.debug(f"Using spring_specification: {spring_spec}")
        
        # Check basic_info
        basic_info_locations = [
            params.get("basic_info", {}),
            params.get("Basic_Info", {}),
            params.get("basicInfo", {}),
            params.get("info", {}),
            spring_spec.get("basic_info", {}) if isinstance(spring_spec, dict) else {},
            spring_spec.get("Basic_Info", {}) if isinstance(spring_spec, dict) else {},
            spring_spec.get("basicInfo", {}) if isinstance(spring_spec, dict) else {},
            spring_spec.get("info", {}) if isinstance(spring_spec, dict) else {},
        ]
        
        # Find the first non-empty basic_info dictionary
        basic_info = {}
        for loc in basic_info_locations:
            if loc and isinstance(loc, dict):
                basic_info = loc
                logger.debug(f"Found basic_info at: {loc}")
                break
        
        # Try all possible paths for part_name if not already found
        if not result["part_name"]:
            possible_paths = [
                ["part_name"],
                ["Part_Name"],
                ["PartName"],
                ["partName"],
                ["Name"],
                ["name"],
                ["spring_specification", "part_name"],
                ["spring_specification", "Part_Name"],
                ["spring_specification", "PartName"],
                ["SpringSpecification", "partName"],
                ["springSpecification", "name"],
                ["basic_info", "part_name"],
                ["basic_info", "Part_Name"],
                ["Basic_Info", "name"],
                ["basicInfo", "partName"],
                ["spring_specification", "basic_info", "part_name"],
                ["spring_specification", "basic_info", "Part_Name"],
                ["SpringSpecification", "BasicInfo", "partName"],
                ["springSpecification", "basicInfo", "name"]
            ]
            
            for path in possible_paths:
                value = _extract_nested_value(params, path)
                if value:
                    result["part_name"] = value
                    logger.debug(f"Found part_name through path {path}: {value}")
                    break
        
        # Try all possible paths for part_number if not already found
        if not result["part_number"]:
            possible_paths = [
                ["part_number"],
                ["Part_Number"],
                ["PartNumber"],
                ["partNumber"],
                ["Number"],
                ["number"],
                ["model_number"],
                ["Model_Number"],
                ["ModelNumber"],
                ["modelNumber"],
                ["spring_specification", "part_number"],
                ["spring_specification", "Part_Number"],
                ["spring_specification", "PartNumber"],
                ["SpringSpecification", "partNumber"],
                ["springSpecification", "number"],
                ["basic_info", "part_number"],
                ["basic_info", "Part_Number"],
                ["Basic_Info", "number"],
                ["basicInfo", "partNumber"],
                ["spring_specification", "basic_info", "part_number"],
                ["spring_specification", "basic_info", "Part_Number"],
                ["SpringSpecification", "BasicInfo", "partNumber"],
                ["springSpecification", "basicInfo", "number"]
            ]
            
            for path in possible_paths:
                value = _extract_nested_value(params, path)
                if value:
                    result["part_number"] = value
                    logger.debug(f"Found part_number through path {path}: {value}")
                    break
        
        # Try all possible paths for free_length if not already found
        if not result["free_length"]:
            possible_paths = [
                ["free_length"],
                ["free_length_mm"],
                ["Free_Length"],
                ["Free_Length_MM"],
                ["FreeLength"],
                ["FreeLength_MM"],
                ["freeLength"],
                ["freeLengthMm"],
                ["Length"],
                ["length"],
                ["spring_specification", "free_length"],
                ["spring_specification", "free_length_mm"],
                ["spring_specification", "Free_Length"],
                ["SpringSpecification", "freeLength"],
                ["springSpecification", "freeLengthMm"],
                ["basic_info", "free_length"],
                ["basic_info", "free_length_mm"],
                ["Basic_Info", "Free_Length"],
                ["basicInfo", "freeLengthMm"],
                ["spring_specification", "basic_info", "free_length"],
                ["spring_specification", "basic_info", "free_length_mm"],
                ["SpringSpecification", "BasicInfo", "freeLength"],
                ["springSpecification", "basicInfo", "freeLengthMm"]
            ]
            
            for path in possible_paths:
                value = _extract_nested_value(params, path)
                if value:
                    result["free_length"] = value
                    logger.debug(f"Found free_length through path {path}: {value}")
                    break
        
        # Try all possible paths for test_mode
        if not result["test_mode"]:
            possible_paths = [
                ["test_mode"],
                ["Test_Mode"],
                ["TestMode"],
                ["testMode"],
                ["Mode"],
                ["mode"],
                ["spring_specification", "test_mode"],
                ["spring_specification", "Test_Mode"],
                ["SpringSpecification", "testMode"],
                ["springSpecification", "mode"],
                ["basic_info", "test_mode"],
                ["Basic_Info", "Test_Mode"],
                ["basicInfo", "testMode"],
                ["spring_specification", "basic_info", "test_mode"],
                ["SpringSpecification", "BasicInfo", "testMode"]
            ]
            
            test_mode_value = ""
            for path in possible_paths:
                value = _extract_nested_value(params, path)
                if value:
                    test_mode_value = value
                    logger.debug(f"Found test_mode through path {path}: {value}")
                    break
            
            # Extract first word of test mode (Height, Deflection, or Tension) if not empty
            result["test_mode"] = test_mode_value.split()[0] if test_mode_value else ""
        
        # Try all possible paths for safety_limit
        if not result["safety_limit"]:
            possible_paths = [
                ["safety_limit"],
                ["safety_limit_n"],
                ["Safety_Limit"],
                ["Safety_Limit_N"],
                ["SafetyLimit"],
                ["SafetyLimitN"],
                ["safetyLimit"],
                ["safetyLimitN"],
                ["Limit"],
                ["limit"],
                ["spring_specification", "safety_limit"],
                ["spring_specification", "safety_limit_n"],
                ["SpringSpecification", "safetyLimit"],
                ["springSpecification", "safetyLimitN"],
                ["basic_info", "safety_limit"],
                ["basic_info", "safety_limit_n"],
                ["Basic_Info", "Safety_Limit"],
                ["basicInfo", "safetyLimitN"],
                ["spring_specification", "basic_info", "safety_limit"],
                ["spring_specification", "basic_info", "safety_limit_n"],
                ["SpringSpecification", "BasicInfo", "safetyLimit"],
                ["springSpecification", "basicInfo", "safetyLimitN"]
            ]
            
            for path in possible_paths:
                value = _extract_nested_value(params, path)
                if value:
                    result["safety_limit"] = value
                    logger.debug(f"Found safety_limit through path {path}: {value}")
                    break
        
        # Similar to exportservice.py - direct extraction from specs dictionary
        if isinstance(specs, dict):
            # Try multiple possible key names in specs
            part_name_keys = ["part_name", "partName", "Part_Name", "PartName", "Name", "name"]
            part_number_keys = ["part_number", "partNumber", "Part_Number", "PartNumber", "Number", "number"]
            free_length_keys = ["free_length", "free_length_mm", "freeLength", "freeLengthMm", "Free_Length", "Free_Length_MM", "Length", "length"]
            safety_limit_keys = ["safety_limit", "safety_limit_n", "safetyLimit", "safetyLimitN", "Safety_Limit", "Safety_Limit_N", "Limit", "limit"]
            test_mode_keys = ["test_mode", "testMode", "Test_Mode", "TestMode", "Mode", "mode"]
            
            if not result["part_name"]:
                for key in part_name_keys:
                    value = specs.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["part_name"] = str(value).strip()
                        logger.debug(f"Found part_name in specs with key '{key}': {value}")
                        break
            
            if not result["part_number"]:
                for key in part_number_keys:
                    value = specs.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["part_number"] = str(value).strip()
                        logger.debug(f"Found part_number in specs with key '{key}': {value}")
                        break
            
            if not result["free_length"]:
                for key in free_length_keys:
                    value = specs.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["free_length"] = str(value).strip()
                        logger.debug(f"Found free_length in specs with key '{key}': {value}")
                        break
            
            if result["safety_limit"] == "300":
                for key in safety_limit_keys:
                    value = specs.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["safety_limit"] = str(value).strip()
                        logger.debug(f"Found safety_limit in specs with key '{key}': {value}")
                        break
            
            if not result["test_mode"]:
                for key in test_mode_keys:
                    value = specs.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        test_mode = value
                        result["test_mode"] = test_mode.split()[0] if test_mode else ""
                        logger.debug(f"Found test_mode in specs with key '{key}': {value}")
                        break
        
        # Also check basicInfo if still not found
        if isinstance(basic_info, dict):
            part_name_keys = ["part_name", "partName", "Part_Name", "PartName", "Name", "name"]
            part_number_keys = ["part_number", "partNumber", "Part_Number", "PartNumber", "Number", "number"]
            free_length_keys = ["free_length", "free_length_mm", "freeLength", "freeLengthMm", "Free_Length", "Free_Length_MM", "Length", "length"]
            
            if not result["part_name"]:
                for key in part_name_keys:
                    value = basic_info.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["part_name"] = str(value).strip()
                        logger.debug(f"Found part_name in basic_info with key '{key}': {value}")
                        break
            
            if not result["part_number"]:
                for key in part_number_keys:
                    value = basic_info.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["part_number"] = str(value).strip()
                        logger.debug(f"Found part_number in basic_info with key '{key}': {value}")
                        break
            
            if not result["free_length"]:
                for key in free_length_keys:
                    value = basic_info.get(key, '')
                    if value and value not in ('None', 'null', None, ''):
                        result["free_length"] = str(value).strip()
                        logger.debug(f"Found free_length in basic_info with key '{key}': {value}")
                        break
        
        # Special handling for SpringSpecification object
        if isinstance(specs, SpringSpecification):
            if not result["part_name"] and hasattr(specs, 'part_name') and specs.part_name:
                result["part_name"] = specs.part_name
                logger.debug(f"Found part_name in SpringSpecification object: {specs.part_name}")
            if not result["part_number"] and hasattr(specs, 'part_number') and specs.part_number:
                result["part_number"] = specs.part_number
                logger.debug(f"Found part_number in SpringSpecification object: {specs.part_number}")
            if not result["free_length"] and hasattr(specs, 'free_length_mm') and specs.free_length_mm:
                result["free_length"] = str(specs.free_length_mm)
                logger.debug(f"Found free_length in SpringSpecification object: {specs.free_length_mm}")
            if hasattr(specs, 'safety_limit_n') and specs.safety_limit_n:
                result["safety_limit"] = str(specs.safety_limit_n)
                logger.debug(f"Found safety_limit in SpringSpecification object: {specs.safety_limit_n}")
            if hasattr(specs, 'test_mode') and specs.test_mode:
                result["test_mode"] = specs.test_mode.split()[0]
                logger.debug(f"Found test_mode in SpringSpecification object: {specs.test_mode}")
        
        # Clean up values (as in exportservice.py)
        result["part_name"] = '' if result["part_name"] in ('None', 'null', None, '') else str(result["part_name"]).strip()
        result["part_number"] = '' if result["part_number"] in ('None', 'null', None, '') else str(result["part_number"]).strip()
        result["free_length"] = '' if result["free_length"] in ('None', 'null', None, '') else str(result["free_length"]).strip()
        result["safety_limit"] = '' if result["safety_limit"] in ('None', 'null', None, '') else str(result["safety_limit"]).strip()
        
        # Final check - try looking at any parameter with names containing relevant terms
        if not result["part_name"] or not result["part_number"] or not result["free_length"]:
            logger.debug("Some values still missing, performing deep parameter search...")
            
            for key, value in flat_params.items():
                key_lower = key.lower()
                if (not result["part_name"]) and ("part" in key_lower and "name" in key_lower):
                    if value and value not in ('None', 'null', None, ''):
                        result["part_name"] = str(value).strip()
                        logger.debug(f"Deep search found part_name in key '{key}': {value}")
                
                if (not result["part_number"]) and (("part" in key_lower and "number" in key_lower) or 
                                                   ("model" in key_lower)):
                    if value and value not in ('None', 'null', None, ''):
                        result["part_number"] = str(value).strip()
                        logger.debug(f"Deep search found part_number in key '{key}': {value}")
                
                if (not result["free_length"]) and ("free" in key_lower and "length" in key_lower):
                    if value and value not in ('None', 'null', None, ''):
                        result["free_length"] = str(value).strip()
                        logger.debug(f"Deep search found free_length in key '{key}': {value}")
        
        logger.debug(f"Final extracted specifications: {result}")
        
    except Exception as e:
        logger.error(f"Error extracting specifications: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    return result

def export_txt(sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
    """Export a sequence to TXT format with improved parameter extraction.
    
    Args:
        sequence: Sequence to export.
        file_path: Path to the output file. Will be modified to follow pattern "AS 01~<Part Number>.txt"
        
    Returns:
        Tuple of (success flag, error message)
    """
    try:
        # Get key specifications using the new function
        specs = extract_key_specifications(sequence)
        part_name = specs["part_name"]
        part_number = specs["part_number"]
        # Use "--" as default for empty free_length
        free_length = specs["free_length"] if specs["free_length"] else "--"
        test_mode = specs["test_mode"]
        safety_limit = specs["safety_limit"]
        
        logger.debug(f"Final values - Part name: {part_name}, Part number: {part_number}, Free length: {free_length}, Test mode: {test_mode}, Safety limit: {safety_limit}")
        
        # Create the standardized filename using part_number
        if not part_number:
            # If no part number found, use a default
            part_number = "unknown_part"
            
        # Get the directory from the original file_path
        output_dir = os.path.dirname(file_path)
        if not output_dir:  # If no directory specified, use current directory
            output_dir = "."
        
        # Create the new filename following the requested format
        new_filename = f"AS 01~{part_number}.txt"
        
        # Combine directory with new filename
        new_file_path = os.path.join(output_dir, new_filename)
        
        logger.debug(f"Original file path: {file_path}")
        logger.debug(f"Modified file path: {new_file_path}")
        
        with open(new_file_path, "w") as f:
            # Write header with mapping from specification panel values - with vertical pipe separators
            f.write(f"1|Part Number|--|{part_number}|\n")
            f.write(f"2|Model Number|--|{part_name}|\n")
            f.write(f"3|Free Length|mm|{free_length}|\n")
            
            # Only include test mode and safety limit if they exist
            test_mode_text = test_mode if test_mode else ""
            safety_limit_text = safety_limit if safety_limit else ""
            f.write(f"<Test Sequence>|N|--|{test_mode_text}|{safety_limit_text}|100|\n\n")
            
            # Get rows from sequence
            rows = sequence.rows
            
            # Write sequence data with vertical pipe separators
            for index, row in enumerate(rows):
                cmd = row.get('CMD', '')
                desc = row.get('Description', '')
                condition = row.get('Condition', '')
                unit = row.get('Unit', '')
                tolerance = row.get('Tolerance', '')
                speed_rpm = row.get('Speed rpm', '')  # Extract Speed rpm field
                
                # Modified row string format with vertical pipes, including Speed rpm
                row_str = f"{cmd}|{desc}|{condition}|{unit}|{tolerance}|{speed_rpm}|\n"
                f.write(row_str)
            
            logger.debug(f"TXT export completed successfully to {new_file_path}")
            
        # Return the success message with the actual file path that was used
        return True, f"Successfully exported to {new_file_path}"
    except Exception as e:
        logger.error(f"TXT export error: {str(e)}")
        return False, f"TXT export error: {str(e)}" 