"""
Export service for the Spring Test App.
Contains classes and functions for exporting sequences to different formats.
"""
import os
import pandas as pd
import json
from typing import Dict, Any, Optional, List, Union, Tuple
from models.data_models import TestSequence, SpringSpecification
from utils.constants import FILE_FORMATS


class ExportService:
    """Service for exporting test sequences to different formats."""
    
    def __init__(self):
        """Initialize the export service."""
        self.supported_formats = {
            "CSV": self._export_csv,
            "JSON": self._export_json,
            "Excel": self._export_excel,
            "TXT": self._export_txt,  # Add TXT support
        }
        # Print supported formats for debugging
        print(f"ExportService initialized with formats: {list(self.supported_formats.keys())}")
        print(f"FILE_FORMATS dictionary: {FILE_FORMATS}")
    
    def export_sequence(self, sequence: TestSequence, file_path: str, format_name: str = None) -> Tuple[bool, str]:
        """Export a sequence to a file.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            format_name: Format to export to. If None, infer from file extension.
            
        Returns:
            Tuple of (success flag, error message)
        """
        # If format is not specified, infer from file extension
        if format_name is None:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            # Use the FILE_FORMATS dictionary to find the corresponding format
            format_name = None
            for fmt, fmt_ext in FILE_FORMATS.items():
                if fmt_ext.lower() == ext:
                    format_name = fmt
                    break
            
            if format_name is None:
                return False, f"Unsupported file extension: {ext}"
        
        # Check if format is supported
        if format_name not in self.supported_formats:
            return False, f"Unsupported format: {format_name}"
        
        # Export the sequence
        try:
            export_func = self.supported_formats[format_name]
            return export_func(sequence, file_path)
        except Exception as e:
            return False, f"Export error: {str(e)}"
    
    def _export_csv(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to CSV.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Create DataFrame from sequence
            df = pd.DataFrame(sequence.rows)
            
            # Add a header row with metadata
            metadata = [
                f"# Spring Test Sequence",
                f"# Created: {sequence.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            ]
            
            # Add parameter information
            for key, value in sequence.parameters.items():
                # Skip timestamp and other metadata
                if key in ["Timestamp"]:
                    continue
                metadata.append(f"# {key}: {value}")
            
            # Write to file
            with open(file_path, "w") as f:
                # Write metadata
                for line in metadata:
                    f.write(line + "\n")
                
                # Write CSV
                df.to_csv(f, index=False)
            
            return True, ""
        except Exception as e:
            return False, f"CSV export error: {str(e)}"
    
    def _export_json(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to JSON.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Convert sequence to dict
            data = sequence.to_dict()
            
            # Write to file
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            
            return True, ""
        except Exception as e:
            return False, f"JSON export error: {str(e)}"
    
    def _export_excel(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to Excel.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        try:
            # Create DataFrame from sequence
            df = pd.DataFrame(sequence.rows)
            
            # Create parameters DataFrame
            param_data = [[key, str(value)] for key, value in sequence.parameters.items() if key != "Timestamp"]
            param_df = pd.DataFrame(param_data, columns=["Parameter", "Value"])
            
            # Create Excel writer
            with pd.ExcelWriter(file_path) as writer:
                # Write sequence to 'Sequence' sheet
                df.to_excel(writer, sheet_name="Sequence", index=False)
                
                # Write parameters to 'Parameters' sheet
                param_df.to_excel(writer, sheet_name="Parameters", index=False)
            
            return True, ""
        except Exception as e:
            return False, f"Excel export error: {str(e)}"
    
    def _export_txt(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to TXT."""
        try:
            # Create DataFrame from sequence
            df = pd.DataFrame(sequence.rows)
            
            with open(file_path, "w") as f:
                # Get specifications from sequence parameters
                specs = sequence.parameters.get("Specifications", {})
                
                # Initialize variables
                part_name = ""       # Will be printed on Part Number line
                part_number = ""     # Will be printed on Model Number line  
                free_length = ""
                test_mode = "Height"
                safety_limit = "300"
                
                # Get values from specifications
                if isinstance(specs, SpringSpecification):
                    # Get values from SpringSpecification object
                    part_name = specs.part_name if hasattr(specs, 'part_name') else ""
                    part_number = specs.part_number if hasattr(specs, 'part_number') else ""
                    free_length = str(specs.free_length_mm) if hasattr(specs, 'free_length_mm') else ""
                    safety_limit = str(specs.safety_limit_n) if hasattr(specs, 'safety_limit_n') else "300"
                    test_mode = specs.test_mode if hasattr(specs, 'test_mode') else "Height Mode"
                elif isinstance(specs, dict):
                    # Get values from dictionary
                    part_name = str(specs.get('part_name', ''))
                    part_number = str(specs.get('part_number', ''))
                    free_length = str(specs.get('free_length_mm', ''))
                    safety_limit = str(specs.get('safety_limit_n', '300'))
                    test_mode = specs.get('test_mode', 'Height Mode')
                
                # Clean up values
                part_name = '' if part_name in ('None', 'null', None) else str(part_name).strip()
                part_number = '' if part_number in ('None', 'null', None) else str(part_number).strip()
                free_length = '' if free_length in ('None', 'null', None) else str(free_length).strip()
                safety_limit = '300' if safety_limit in ('None', 'null', None) else str(safety_limit).strip()
                
                # Extract first word of test mode (Height, Deflection, or Tension)
                test_mode = test_mode.split()[0] if test_mode else "Height"
                
                # Write header with mapping from specification panel values
                f.write(f"1    Part Number     --    {part_name}\n")        # Using part_name here
                f.write(f"2    Model Number    --    {part_number}\n")      # Using part_number here  
                f.write(f"3    Free Length     mm    {free_length}\n")      # Using free_length here
                f.write(f"<Test Sequence> N          --    {test_mode} {safety_limit} 100\n\n")
                
                # Write sequence data
                for index, row in df.iterrows():
                    cmd = row.get('CMD', '')
                    desc = row.get('Description', '')
                    condition = row.get('Condition', '')
                    unit = row.get('Unit', '')
                    tolerance = row.get('Tolerance', '')
                    
                    row_str = f"R{index:02d}  {cmd:<6} {desc:<20} {condition:<10} {unit:<4} {tolerance:<20}\n"
                    f.write(row_str)
            
            return True, ""
        except Exception as e:
            return False, f"TXT export error: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Get the list of supported export formats.
        
        Returns:
            List of supported format names.
        """
        return list(self.supported_formats.keys())


from typing import Tuple, Dict, List, Optional, Any

class TemplateManager:
    """Manager for sequence templates."""
    
    def __init__(self, templates_dir: str = "templates"):
        """Initialize the template manager.
        
        Args:
            templates_dir: Directory to store templates in.
        """
        self.templates_dir = templates_dir
        self._ensure_templates_dir()
        self.templates = self._load_templates()
    
    def _ensure_templates_dir(self) -> None:
        """Ensure the templates directory exists."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
    
    def _load_templates(self) -> Dict[str, TestSequence]:
        """Load templates from the templates directory.
        
        Returns:
            Dictionary of template name -> TestSequence.
        """
        templates = {}
        
        # List template files
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(".json")]
        
        # Load each template
        for file_name in template_files:
            try:
                file_path = os.path.join(self.templates_dir, file_name)
                with open(file_path, "r") as f:
                    data = json.load(f)
                
                # Create TestSequence from data
                sequence = TestSequence.from_dict(data)
                
                # Use file name without extension as template name
                template_name = os.path.splitext(file_name)[0]
                
                templates[template_name] = sequence
            except (json.JSONDecodeError, IOError, KeyError):
                # Skip invalid templates
                pass
        
        return templates
    
    def save_template(self, name: str, sequence: TestSequence) -> bool:
        """Save a sequence as a template.
        
        Args:
            name: Template name.
            sequence: Sequence to save.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Create file path
            file_path = os.path.join(self.templates_dir, f"{name}.json")
            
            # Save sequence to file
            with open(file_path, "w") as f:
                json.dump(sequence.to_dict(), f, indent=2)
            
            # Add to templates
            self.templates[name] = sequence
            
            return True
        except Exception:
            return False
    
    def delete_template(self, name: str) -> bool:
        """Delete a template.
        
        Args:
            name: Template name.
            
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if template exists
            if name not in self.templates:
                return False
            
            # Delete template file
            file_path = os.path.join(self.templates_dir, f"{name}.json")
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Remove from templates
            del self.templates[name]
            
            return True
        except Exception:
            return False
    
    def get_template(self, name: str) -> Optional[TestSequence]:
        """Get a template.
        
        Args:
            name: Template name.
            
        Returns:
            Template sequence, or None if not found.
        """
        return self.templates.get(name)
    
    def get_template_names(self) -> List[str]:
        """Get the list of template names.
        
        Returns:
            List of template names.
        """
        return list(self.templates.keys())
    
    def get_templates(self) -> Dict[str, TestSequence]:
        """Get all templates.
        
        Returns:
            Dictionary of template name -> TestSequence.
        """
        return self.templates