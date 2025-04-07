#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Tooltip component for displaying detailed data when hovering over the time series graph.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor

class TimeSeriesToolTip(QFrame):
    """Tooltip that displays data for all hops at a specific time point"""
    
    def __init__(self):
        super().__init__()
        
        # Configure frame appearance
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setLineWidth(1)
        
        # Make it appear as a floating tooltip
        self.setWindowFlags(Qt.WindowType.ToolTip)
        
        # Create layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # Create header
        self.time_label = QLabel("Time: ")
        self.time_label.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.time_label)
        
        # Create grid for hop data
        self.grid_layout = QGridLayout()
        self.grid_layout.setColumnStretch(1, 1)
        self.grid_layout.setColumnStretch(2, 1)
        self.layout.addLayout(self.grid_layout)
        
        # Stores colors by hop for consistent appearance
        self.colors = {}
        
        # Column headers
        self.grid_layout.addWidget(QLabel("Hop"), 0, 0)
        self.grid_layout.addWidget(QLabel("Latency (ms)"), 0, 1)
        
        # Set initial visibility
        self.hide()
        
    @pyqtSlot(float, list)
    def update_tooltip(self, timestamp, hop_values):
        """Update the tooltip with new data
        
        Args:
            timestamp: The timestamp for the data point
            hop_values: List of (hop_num, latency) tuples
        """
        # Hide if no data provided
        if not hop_values:
            self.hide()
            return
            
        # Update time label
        mins = int(timestamp // 60)
        secs = int(timestamp % 60)
        self.time_label.setText(f"Time: {mins:02d}:{secs:02d}")
        
        # Clear existing hop data rows - need to keep headers
        for i in reversed(range(self.grid_layout.rowCount())):
            if i > 0:  # Skip header row
                for j in range(self.grid_layout.columnCount()):
                    item = self.grid_layout.itemAtPosition(i, j)
                    if item is not None:
                        widget = item.widget()
                        if widget is not None:
                            self.grid_layout.removeWidget(widget)
                            widget.deleteLater()
                            
        # Make a more muted color palette matching the main graph
        colors = [
            '#d9534f',  # Soft red
            '#5cb85c',  # Soft green
            '#5bc0de',  # Soft blue
            '#f0ad4e',  # Soft amber
            '#a87dc9',  # Soft purple
            '#20c997',  # Soft teal
            '#fd7e14',  # Soft orange
            '#6c757d',  # Soft gray
            '#e83e8c',  # Soft pink
            '#17a2b8',  # Soft cyan
        ]
        
        # Add new hop data rows
        for i, (hop_num, latency) in enumerate(sorted(hop_values)):
            # Row index (after header)
            row = i + 1
            
            # Get color for this hop
            if hop_num not in self.colors:
                color_index = (hop_num - 1) % len(colors)
                self.colors[hop_num] = colors[color_index]
                
            color = self.colors[hop_num]
            
            # Create hop number label with color
            hop_label = QLabel(f"Hop {hop_num}")
            hop_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            self.grid_layout.addWidget(hop_label, row, 0)
            
            # Create latency label
            latency_label = QLabel(f"{latency:.1f}")
            if latency > 100:
                latency_label.setStyleSheet("color: #d9534f; font-weight: bold;")  # Highlight high latency
            self.grid_layout.addWidget(latency_label, row, 1)
        
        # Show the tooltip
        self.adjustSize()
        self.show()
        
    def move_to_position(self, x, y):
        """Move the tooltip to a specific position on the screen
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self.move(x + 15, y - self.height() // 2)  # Offset slightly to avoid covering the cursor