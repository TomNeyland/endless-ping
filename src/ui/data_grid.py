#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Data grid for displaying hop information in the network monitor.
"""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QBrush

class HopDataGrid(QTableWidget):
    """Grid for displaying hop-by-hop network monitoring data"""
    
    def __init__(self):
        super().__init__()
        
        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        
        # Set up columns
        self.setup_columns()
        
        # Set other visual properties
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(False)
        
        self.apply_styles()
        
    def setup_columns(self):
        """Set up the table columns"""
        columns = [
            ("Hop", 50),
            ("Count", 70),
            ("IP", 150),
            ("Hostname", 200),
            ("Avg", 70),
            ("Min", 70),
            ("Cur", 70),
            ("Loss%", 70),
            ("Jitter", 70)
        ]
        
        # Set column count
        self.setColumnCount(len(columns))
        
        # Set headers and widths
        for i, (header, width) in enumerate(columns):
            self.setHorizontalHeaderItem(i, QTableWidgetItem(header))
            self.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            self.horizontalHeader().setDefaultSectionSize(width)
        
        # Allow IP and hostname columns to stretch
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
    def update_data(self, hop_data):
        """
        Update the table with new hop data
        
        Args:
            hop_data: List of dictionaries containing hop information
        """
        # Block signals during update to improve performance
        self.blockSignals(True)
        
        # Set row count
        new_row_count = len(hop_data)
        if self.rowCount() != new_row_count:
            self.setRowCount(new_row_count)
        
        # Update each row
        for row, hop in enumerate(hop_data):
            self.set_cell_value(row, 0, str(hop['hop']))
            self.set_cell_value(row, 1, str(hop['count']))
            self.set_cell_value(row, 2, hop['ip'])
            self.set_cell_value(row, 3, hop['hostname'])
            
            # Format latency values
            avg = "-" if hop['avg'] == 0 else f"{hop['avg']:.1f}"
            min_val = "-" if hop['min'] == float('inf') else f"{hop['min']:.1f}"
            cur = "-" if hop['current'] == 0 else f"{hop['current']:.1f}"
            
            self.set_cell_value(row, 4, avg)
            self.set_cell_value(row, 5, min_val)
            self.set_cell_value(row, 6, cur)
            
            # Format packet loss
            loss = f"{hop['loss']:.1f}"
            self.set_cell_value(row, 7, loss)
            
            # Format jitter
            jitter = f"{hop['jitter']:.1f}"
            self.set_cell_value(row, 8, jitter)
            
            # Apply color based on current latency
            self.color_row(row, hop['current'], hop['loss'])
        
        # Unblock signals
        self.blockSignals(False)
    
    def set_cell_value(self, row, col, value):
        """Set cell value, creating a new item if needed"""
        item = self.item(row, col)
        if item is None:
            item = QTableWidgetItem(value)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, col, item)
        else:
            item.setText(value)
    
    def color_row(self, row, latency, loss):
        """
        Apply color to a row based on latency and loss values
        
        Args:
            row: Row index
            latency: Current latency value
            loss: Packet loss percentage
        """
        if loss > 20:
            # High packet loss: red
            color = QColor(255, 180, 180)
        elif latency > 100:
            # High latency: red
            color = QColor(255, 180, 180)
        elif latency > 50:
            # Medium latency: yellow
            color = QColor(255, 255, 180)
        elif latency > 0:
            # Low latency: green
            color = QColor(180, 255, 180)
        else:
            # No data or timeout: light gray
            color = QColor(220, 220, 220)
        
        brush = QBrush(color)
        
        # Apply to all cells in the row
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                item.setBackground(brush)
    
    def apply_styles(self):
        """Apply custom styles to the data grid"""
        self.setStyleSheet(
            """
            QTableWidget {
                background-color: #2b2b2b;
                color: #ffffff;
                gridline-color: #555555;
            }
            QHeaderView::section {
                background-color: #3c3f41;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                border: none;
                padding: 4px;
            }
            """
        )