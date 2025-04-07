#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hop selector component for controlling which hops are visible in the time series graph.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QCheckBox, QLabel,
    QGroupBox, QFrame, QHBoxLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QBrush, QPen

class ColorIndicator(QFrame):
    """A simple colored square to indicate hop color"""
    
    def __init__(self, color):
        super().__init__()
        self.color = QColor(color)
        self.setMinimumSize(12, 12)
        self.setMaximumSize(12, 12)
        self.setFrameShape(QFrame.Shape.Box)
        
    def paintEvent(self, event):
        """Paint the color indicator"""
        painter = QPainter(self)
        painter.setBrush(QBrush(self.color))
        painter.setPen(QPen(Qt.GlobalColor.black, 1))
        painter.drawRect(0, 0, self.width()-1, self.height()-1)

class HopSelector(QWidget):
    """Component that allows users to select which hops are visible in the graph"""
    
    # Signal emitted when hop visibility changes
    hop_visibility_changed = pyqtSignal(int, bool)
    highlight_hop_changed = pyqtSignal(int)  # Emitted when a hop is highlighted
    all_hops_visibility_changed = pyqtSignal(bool)  # Emitted when "Select All" is toggled
    
    def __init__(self):
        super().__init__()
        
        # Store hop checkboxes
        self.hop_checkboxes = {}
        self.hop_rows = {}
        
        # Configure layout
        self.setup_ui()
        
        # Color palette (must match the one in TimeSeriesGraph)
        self.colors = [
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
        
    def setup_ui(self):
        """Set up the UI components"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a group box
        group_box = QGroupBox("Hop Visibility")
        main_layout.addWidget(group_box)
        
        # Create a layout for the group box
        group_layout = QVBoxLayout(group_box)
        
        # Add "Select All" checkbox
        self.select_all_checkbox = QCheckBox("Select All")
        self.select_all_checkbox.setChecked(True)
        self.select_all_checkbox.stateChanged.connect(self.on_select_all_changed)
        group_layout.addWidget(self.select_all_checkbox)
        
        # Create a scroll area for hop checkboxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        group_layout.addWidget(scroll_area)
        
        # Create a widget to hold all hop checkboxes
        self.hop_list_widget = QWidget()
        self.hop_list_layout = QVBoxLayout(self.hop_list_widget)
        self.hop_list_layout.setContentsMargins(0, 0, 0, 0)
        self.hop_list_layout.setSpacing(4)
        self.hop_list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add the widget to the scroll area
        scroll_area.setWidget(self.hop_list_widget)
        
        # Add a stretcher to push all content to the top
        group_layout.addStretch(1)
        
    def on_select_all_changed(self, state):
        """Handle 'Select All' checkbox state change"""
        checked = state == Qt.CheckState.Checked
        
        # Update all checkboxes
        for checkbox in self.hop_checkboxes.values():
            checkbox.setChecked(checked)
            
        # Emit signal for toggle all functionality
        self.all_hops_visibility_changed.emit(checked)
        
    def on_hop_checkbox_changed(self, hop_num, state):
        """Handle individual hop checkbox state change"""
        checked = state == Qt.CheckState.Checked
        self.hop_visibility_changed.emit(hop_num, checked)
        
        # Update "Select All" checkbox if needed
        self.update_select_all_state()
        
    def on_hop_row_entered(self, hop_num):
        """Handle mouse hover over a hop row"""
        self.highlight_hop_changed.emit(hop_num)
        
    def update_select_all_state(self):
        """Update the state of the 'Select All' checkbox based on individual hop checkboxes"""
        if not self.hop_checkboxes:
            return
            
        all_checked = all(checkbox.isChecked() for checkbox in self.hop_checkboxes.values())
        any_checked = any(checkbox.isChecked() for checkbox in self.hop_checkboxes.values())
        
        # Block signals to prevent recursion
        self.select_all_checkbox.blockSignals(True)
        
        if all_checked:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Checked)
        elif any_checked:
            self.select_all_checkbox.setCheckState(Qt.CheckState.PartiallyChecked)
        else:
            self.select_all_checkbox.setCheckState(Qt.CheckState.Unchecked)
            
        self.select_all_checkbox.blockSignals(False)
        
    def update_hops(self, hop_data):
        """Update the hop list based on current data
        
        Args:
            hop_data: List of dictionaries containing hop information
        """
        # Get current hop numbers
        current_hops = {hop['hop'] for hop in hop_data}
        
        # Add new hops
        for hop_num in sorted(current_hops):
            if hop_num not in self.hop_checkboxes:
                self.add_hop(hop_num)
                
        # Remove stale hops
        for hop_num in list(self.hop_checkboxes.keys()):
            if hop_num not in current_hops:
                self.remove_hop(hop_num)
                
    def add_hop(self, hop_num):
        """Add a new hop to the list
        
        Args:
            hop_num: The hop number to add
        """
        # Create a widget for the row
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        
        # Create a color indicator
        color_index = (hop_num - 1) % len(self.colors)
        color = self.colors[color_index]
        color_indicator = ColorIndicator(color)
        row_layout.addWidget(color_indicator)
        
        # Create a checkbox
        checkbox = QCheckBox(f"Hop {hop_num}")
        checkbox.setChecked(True)  # Default to visible
        checkbox.stateChanged.connect(lambda state, h=hop_num: self.on_hop_checkbox_changed(h, state))
        row_layout.addWidget(checkbox)
        
        # Add stretch to push widgets to the left
        row_layout.addStretch(1)
        
        # Add to the layout in the correct position (sort by hop number)
        position = 0
        for i, existing_hop in enumerate(sorted(self.hop_checkboxes.keys())):
            if hop_num < existing_hop:
                position = i
                break
            else:
                position = i + 1
                
        self.hop_list_layout.insertWidget(position, row_widget)
        
        # Store the checkbox and row widget
        self.hop_checkboxes[hop_num] = checkbox
        self.hop_rows[hop_num] = row_widget
        
        # Connect hover event for the row
        row_widget.enterEvent = lambda event, h=hop_num: self.on_hop_row_entered(h)
        
        # Update "Select All" checkbox if needed
        self.update_select_all_state()
        
    def remove_hop(self, hop_num):
        """Remove a hop from the list
        
        Args:
            hop_num: The hop number to remove
        """
        if hop_num in self.hop_checkboxes:
            # Remove the row widget from the layout
            self.hop_list_layout.removeWidget(self.hop_rows[hop_num])
            
            # Delete the row widget
            self.hop_rows[hop_num].deleteLater()
            
            # Clean up the dictionaries
            del self.hop_checkboxes[hop_num]
            del self.hop_rows[hop_num]
            
            # Update "Select All" checkbox if needed
            self.update_select_all_state()
            
    def set_hop_visibility(self, hop_num, visible):
        """Set the visibility of a specific hop
        
        Args:
            hop_num: The hop number to set
            visible: Boolean indicating whether it should be visible
        """
        if hop_num in self.hop_checkboxes:
            checkbox = self.hop_checkboxes[hop_num]
            checkbox.blockSignals(True)
            checkbox.setChecked(visible)
            checkbox.blockSignals(False)
            
            # Update "Select All" checkbox if needed
            self.update_select_all_state()
            
    def highlight_hop(self, hop_num):
        """Temporarily highlight a hop in the list
        
        Args:
            hop_num: The hop number to highlight
        """
        # This could be implemented with CSS styling to highlight the row
        pass