#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Time window controls for adjusting the visible time range in the time series graph.
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLabel, QPushButton, 
    QCheckBox, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal

# Configure logger for this module
logger = logging.getLogger('endless_ping.time_window_controls')

class TimeWindowControls(QWidget):
    """Controls for adjusting the visible time window in time series graphs"""
    
    # Define signals
    window_changed = pyqtSignal(int)  # Emitted when the window size changes (in seconds)
    auto_scroll_changed = pyqtSignal(bool)  # Emitted when auto-scroll is toggled
    goto_latest_clicked = pyqtSignal()  # Emitted when "Latest" button is clicked
    final_hop_only_changed = pyqtSignal(bool)  # Emitted when the final hop only mode is toggled
    
    def __init__(self):
        super().__init__()
        
        # Setup UI
        self.setup_ui()
        self.apply_styles()
        
        # Reference to the hop selector (will be set by the main window)
        self.hop_selector = None
    
    def setup_ui(self):
        """Set up the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        layout.setSpacing(10)
        
        # Window size label
        self.window_label = QLabel("Time Window:")
        layout.addWidget(self.window_label)
        
        # Window size selector
        self.window_selector = QComboBox()
        self.setup_window_options()
        self.window_selector.currentIndexChanged.connect(self.on_window_changed)
        layout.addWidget(self.window_selector)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Auto-scroll checkbox
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.stateChanged.connect(self.on_auto_scroll_changed)
        layout.addWidget(self.auto_scroll_check)
        
        # "Go to Latest" button
        self.latest_button = QPushButton("Latest")
        self.latest_button.clicked.connect(self.on_latest_clicked)
        layout.addWidget(self.latest_button)
        
        # Add another separator
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.Shape.VLine)
        separator2.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator2)
        
        # "Final Hop Only" toggle checkbox
        self.final_hop_only_check = QCheckBox("Final Hop Only")
        self.final_hop_only_check.setChecked(False)
        self.final_hop_only_check.stateChanged.connect(self.on_final_hop_only_changed)
        self.final_hop_only_check.setToolTip("Show only the final hop line but retain all failure indicators")
        layout.addWidget(self.final_hop_only_check)
        
        # Add stretch to push everything to the left
        layout.addStretch()
        
    def setup_window_options(self):
        """Set up the time window options"""
        options = [
            ("30s", 30),
            ("1m", 60),
            ("5m", 300),
            ("15m", 900),
            ("30m", 1800),
            ("1h", 3600)
        ]
        
        for label, value in options:
            self.window_selector.addItem(label, value)
        
        # Set default to 1 minute
        self.window_selector.setCurrentIndex(1)
        
    def on_window_changed(self, index):
        """Handle window size selection change"""
        if index >= 0:
            window_seconds = self.window_selector.itemData(index)
            self.window_changed.emit(window_seconds)
            
    def on_auto_scroll_changed(self, state):
        """Handle auto-scroll checkbox change"""
        self.auto_scroll_changed.emit(state == Qt.CheckState.Checked)
        
        # Enable/disable the "Latest" button based on auto-scroll state
        self.latest_button.setEnabled(state != Qt.CheckState.Checked)
            
    def on_latest_clicked(self):
        """Handle "Latest" button click"""
        self.goto_latest_clicked.emit()
        
    def get_current_window(self):
        """Get the current time window in seconds"""
        index = self.window_selector.currentIndex()
        if index >= 0:
            return self.window_selector.itemData(index)
        return 60  # Default to 1 minute
        
    def set_window(self, seconds):
        """Set the time window to the specified value"""
        for i in range(self.window_selector.count()):
            if self.window_selector.itemData(i) == seconds:
                self.window_selector.setCurrentIndex(i)
                break
                
    def set_auto_scroll(self, enabled):
        """Set the auto-scroll checkbox state"""
        self.auto_scroll_check.setChecked(enabled)
        
    def on_final_hop_only_changed(self, state):
        """Handle final hop only checkbox change"""
        is_checked = state == Qt.CheckState.Checked
        logger.debug(f"Final Hop Only checkbox changed to: {is_checked}")
        
        # Emit signal to notify other components
        logger.debug(f"Emitting final_hop_only_changed({is_checked})")
        self.final_hop_only_changed.emit(is_checked)
        
    def get_final_hop_only(self):
        """Get the final hop only state"""
        return self.final_hop_only_check.isChecked()
        
    def set_final_hop_only(self, enabled):
        """Set the final hop only checkbox state"""
        self.final_hop_only_check.setChecked(enabled)
        
    def apply_styles(self):
        """Apply custom styles to the control panel"""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 4px 8px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #4c4f51;
            }
            QPushButton:disabled {
                background-color: #2b2b2b;
                color: #777777;
            }
            QComboBox {
                background-color: #3c3f41;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 4px;
                min-width: 80px;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QFrame[frameShape="5"] { /* VLine */
                color: #555555;
            }
            """
        )