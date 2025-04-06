#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Control panel for network monitoring application.
"""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, 
    QComboBox, QLabel, QCompleter
)
from PyQt6.QtCore import Qt, pyqtSignal, QStringListModel

class ControlPanel(QWidget):
    """Top control panel with target input, buttons, and interval selection"""
    
    # Define signals
    target_changed = pyqtSignal(str)
    start_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    save_clicked = pyqtSignal()
    interval_changed = pyqtSignal(int)
    
    def __init__(self, network_monitor):
        super().__init__()
        
        self.network_monitor = network_monitor
        self.recent_targets = []
        self.max_recent_targets = 10
        
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # Target input
        self.target_label = QLabel("Target:")
        layout.addWidget(self.target_label)
        
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Enter hostname or IP address")
        self.target_input.returnPressed.connect(self.on_target_enter)
        layout.addWidget(self.target_input)
        
        # Recent targets dropdown
        self.target_dropdown = QComboBox()
        self.target_dropdown.setMinimumWidth(150)
        self.target_dropdown.currentTextChanged.connect(self.on_dropdown_changed)
        layout.addWidget(self.target_dropdown)
        
        # Interval selector
        self.interval_label = QLabel("Interval:")
        layout.addWidget(self.interval_label)
        
        self.interval_selector = QComboBox()
        self.setup_intervals()
        self.interval_selector.currentIndexChanged.connect(self.on_interval_changed)
        layout.addWidget(self.interval_selector)
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)
        
        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)
        layout.addWidget(self.pause_button)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.on_save_clicked)
        layout.addWidget(self.save_button)
        
        # Set up auto-complete for target input
        self.completer = QCompleter()
        self.target_input.setCompleter(self.completer)
        
        self.apply_styles()
        
    def setup_intervals(self):
        """Set up the interval selection dropdown"""
        intervals = [
            ("1.0s", 1000),
            ("2.5s", 2500),
            ("5.0s", 5000),
            ("10.0s", 10000)
        ]
        
        for label, value in intervals:
            self.interval_selector.addItem(label, value)
        
        # Set default to 2.5s
        self.interval_selector.setCurrentIndex(1)
        
    def on_target_enter(self):
        """Handle target input when Enter is pressed"""
        target = self.target_input.text().strip()
        if target:
            self.add_recent_target(target)
            self.target_changed.emit(target)
            
    def add_recent_target(self, target):
        """Add a target to the recent targets list"""
        # Remove if it already exists (to move it to the top)
        if target in self.recent_targets:
            self.recent_targets.remove(target)
            
        # Add to the top of the list
        self.recent_targets.insert(0, target)
        
        # Trim list if needed
        if len(self.recent_targets) > self.max_recent_targets:
            self.recent_targets = self.recent_targets[:self.max_recent_targets]
            
        # Update dropdown and completer
        self.update_recent_targets_ui()
            
    def update_recent_targets_ui(self):
        """Update the UI components with recent targets"""
        # Block signals to prevent recursive calls
        self.target_dropdown.blockSignals(True)
        
        # Clear and repopulate
        self.target_dropdown.clear()
        self.target_dropdown.addItem("Recent Targets")
        self.target_dropdown.addItems(self.recent_targets)
        
        # Unblock signals
        self.target_dropdown.blockSignals(False)
        
        # Update completer
        model = QStringListModel(self.recent_targets)
        self.completer.setModel(model)
        
    def on_dropdown_changed(self, text):
        """Handle selection from the recent targets dropdown"""
        if text and text != "Recent Targets":
            self.target_input.setText(text)
            self.target_changed.emit(text)
            
    def on_interval_changed(self, index):
        """Handle interval selection change"""
        if index >= 0:
            interval_ms = self.interval_selector.itemData(index)
            self.interval_changed.emit(interval_ms)
            
    def on_start_clicked(self):
        """Handle start button click"""
        target = self.target_input.text().strip()
        if target:
            self.add_recent_target(target)
            self.target_changed.emit(target)
            self.start_clicked.emit()
            
    def on_pause_clicked(self):
        """Handle pause button click"""
        self.pause_clicked.emit()
        
    def on_save_clicked(self):
        """Handle save button click"""
        self.save_clicked.emit()
        
    def set_monitoring_active(self, active):
        """Update button states based on monitoring status"""
        self.start_button.setEnabled(not active)
        self.pause_button.setEnabled(active)
        
    def get_current_target(self):
        """Get the current target text"""
        return self.target_input.text().strip()
        
    def set_target(self, target):
        """Set the target input text"""
        self.target_input.setText(target)
        self.add_recent_target(target)
        
    def set_interval(self, interval_ms):
        """Set the interval selector to the specified value"""
        for i in range(self.interval_selector.count()):
            if self.interval_selector.itemData(i) == interval_ms:
                self.interval_selector.setCurrentIndex(i)
                break

    def apply_styles(self):
        """Apply custom styles to the control panel"""
        self.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #3c3f41;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 4px;
            }
            QPushButton {
                background-color: #3c3f41;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 6px;
            }
            QPushButton:hover {
                background-color: #4c4f51;
            }
            QComboBox {
                background-color: #3c3f41;
                border: 1px solid #555555;
                color: #ffffff;
                padding: 4px;
            }
            QLabel {
                color: #ffffff;
            }
            """
        )