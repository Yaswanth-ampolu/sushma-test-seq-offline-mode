"""
Results panel module for the Spring Test App.
Contains the components for displaying and exporting test sequences.
"""
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, 
                           QPushButton, QHeaderView, QFileDialog, QMessageBox, 
                           QComboBox, QGroupBox, QFormLayout, QTabWidget, QTextEdit)
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QFont

import pandas as pd
from models.table_models import PandasModel
from models.data_models import TestSequence
from utils.constants import FILE_FORMATS
import os
import datetime


class ResultsPanel(QWidget):
    """Results panel widget for the Spring Test App."""
    
    def __init__(self, export_service):
        """Initialize the results panel.
        
        Args:
            export_service: Export service.
        """
        super().__init__()
        
        # Store services
        self.export_service = export_service
        
        # Current sequence
        self.current_sequence = None
        
        # Set up the UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI."""
        # Main layout
        layout = QVBoxLayout()
        
        # Tab widget for different views
        self.tab_widget = QTabWidget()
        
        # Results table tab
        table_tab = QWidget()
        table_layout = QVBoxLayout()
        
        # Results table label
        table_label = QLabel("Generated Test Sequence")
        table_label.setFont(QFont("Arial", 12, QFont.Bold))
        table_layout.addWidget(table_label)
        
        # Results table
        self.results_table = QTableView()
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSortingEnabled(True)
        table_layout.addWidget(self.results_table)
        
        table_tab.setLayout(table_layout)
        self.tab_widget.addTab(table_tab, "Sequence")
        
        # Parameters tab
        params_tab = QWidget()
        params_layout = QVBoxLayout()
        
        # Parameters label
        params_label = QLabel("Spring Parameters")
        params_label.setFont(QFont("Arial", 12, QFont.Bold))
        params_layout.addWidget(params_label)
        
        # Parameters display
        self.parameters_display = QTextEdit()
        self.parameters_display.setReadOnly(True)
        params_layout.addWidget(self.parameters_display)
        
        params_tab.setLayout(params_layout)
        self.tab_widget.addTab(params_tab, "Parameters")
        
        # JSON view tab
        json_tab = QWidget()
        json_layout = QVBoxLayout()
        
        # JSON label
        json_label = QLabel("JSON Representation")
        json_label.setFont(QFont("Arial", 12, QFont.Bold))
        json_layout.addWidget(json_label)
        
        # JSON display
        self.json_display = QTextEdit()
        self.json_display.setReadOnly(True)
        self.json_display.setFont(QFont("Courier New", 10))
        json_layout.addWidget(self.json_display)
        
        json_tab.setLayout(json_layout)
        self.tab_widget.addTab(json_tab, "JSON")
        
        # Add tab widget to layout
        layout.addWidget(self.tab_widget)
        
        # Export group
        export_group = QGroupBox("Export Options")
        export_layout = QVBoxLayout()
        
        # Export format selection
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("Format:"))
        
        self.format_combo = QComboBox()
        for format_name in self.export_service.get_supported_formats():
            self.format_combo.addItem(format_name)
        format_layout.addWidget(self.format_combo)
        
        export_layout.addLayout(format_layout)
        
        # Export buttons
        export_btn_layout = QHBoxLayout()
        
        self.export_btn = QPushButton("Export Sequence")
        self.export_btn.clicked.connect(self.on_export_clicked)
        self.export_btn.setEnabled(False)  # Disabled until a sequence is available
        export_btn_layout.addWidget(self.export_btn)
        
        export_layout.addLayout(export_btn_layout)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        # Set the layout
        self.setLayout(layout)
    
    def display_sequence(self, sequence):
        """Display a sequence in the results panel.
        
        Args:
            sequence: TestSequence object.
        """
        # Store the sequence
        self.current_sequence = sequence
        
        # Display in table
        df = pd.DataFrame(sequence.rows)
        model = PandasModel(df)
        self.results_table.setModel(model)
        
        # Update parameters display
        params_text = ""
        for key, value in sequence.parameters.items():
            # Skip timestamp and other metadata
            if key in ["Timestamp"]:
                continue
            params_text += f"<b>{key}:</b> {value}<br>"
        self.parameters_display.setHtml(params_text)
        
        # Update JSON display
        import json
        json_text = json.dumps(sequence.to_dict(), indent=2)
        self.json_display.setText(json_text)
        
        # Enable export buttons
        self.export_btn.setEnabled(True)
        
        # Switch to sequence tab
        self.tab_widget.setCurrentIndex(0)
    
    def on_export_clicked(self):
        """Handle export button clicks."""
        # Check if a sequence is available
        if not self.current_sequence or not self.export_service:
            QMessageBox.warning(self, "No Sequence", "No test sequence available to export.")
            return
        
        # Get selected format
        format_name = self.format_combo.currentText()
        file_extension = FILE_FORMATS.get(format_name, ".csv")
        
        # Use the fixed export directory instead of showing file dialog
        export_directory = r"C:\SI\SI-FTS Software-NPD\Master Data"
        
        # Create the directory if it doesn't exist
        if not os.path.exists(export_directory):
            try:
                os.makedirs(export_directory)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not create export directory: {str(e)}")
                return
        
        # Generate a default filename using timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"spring_sequence_{timestamp}{file_extension}"
        
        # Create the full file path
        file_name = os.path.join(export_directory, default_filename)
        
        # Export the sequence
        success, message = self.export_service.export_sequence(
            self.current_sequence, file_name, format_name
        )
        
        if success:
            # For TXT exports, the success message contains the actual file path used
            if format_name == "TXT" and message:
                QMessageBox.information(self, "Export Successful", message)
            else:
                QMessageBox.information(self, "Export Successful", f"Sequence exported to {file_name}")
        else:
            QMessageBox.critical(self, "Export Failed", f"Failed to export sequence: {message}")
    
    def clear_display(self):
        """Clear the results display."""
        # Clear table
        self.results_table.setModel(None)
        
        # Clear parameters display
        self.parameters_display.clear()
        
        # Clear JSON display
        self.json_display.clear()
        
        # Disable export buttons
        self.export_btn.setEnabled(False)
        
        # Clear current sequence
        self.current_sequence = None 