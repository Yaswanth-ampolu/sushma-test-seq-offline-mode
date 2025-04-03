"""
Export service for the Spring Test App.
Contains classes and functions for exporting sequences to different formats.
"""
import os
import pandas as pd
import json
import logging
from typing import Dict, Any, Optional, List, Union, Tuple
from models.data_models import TestSequence, SpringSpecification
from utils.constants import FILE_FORMATS

# Import the specialized TXT export function
from services.export_service_txt import export_txt

# Set up logging
logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting test sequences to different formats."""
    
    def __init__(self):
        """Initialize the export service."""
        self.supported_formats = {
            "CSV": self._export_csv,
            "JSON": self._export_json,
            "TXT": self._export_txt,  # Will use the external function
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
            logger.debug(f"Exporting sequence to {format_name} format at {file_path}")
            export_func = self.supported_formats[format_name]
            return export_func(sequence, file_path)
        except Exception as e:
            logger.error(f"Export error: {str(e)}")
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
    
    def _export_txt(self, sequence: TestSequence, file_path: str) -> Tuple[bool, str]:
        """Export a sequence to TXT using the specialized external function.
        
        Args:
            sequence: Sequence to export.
            file_path: Path to the output file.
            
        Returns:
            Tuple of (success flag, error message)
        """
        # Call the specialized TXT export function
        return export_txt(sequence, file_path)
    
    def get_supported_formats(self) -> List[str]:
        """Get the list of supported export formats.
        
        Returns:
            List of supported format names.
        """
        return list(self.supported_formats.keys())