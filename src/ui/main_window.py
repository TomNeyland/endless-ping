#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Main window for the network monitoring application.
"""

import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter, QSizePolicy,
    QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt, QSettings, QTimer, QEvent, QPoint
from PyQt6.QtGui import QCursor

from ui.controls import ControlPanel
from ui.data_grid import HopDataGrid
from ui.latency_graph import LatencyBarGraph
from ui.timeseries_graph import TimeSeriesGraph
from ui.time_window_controls import TimeWindowControls
from ui.hop_selector import HopSelector
from ui.timeseries_tooltip import TimeSeriesToolTip
from core.network import NetworkMonitor

# Configure logger for this module
logger = logging.getLogger('endless_ping.main_window')

class MainWindow(QMainWindow):
    """Main application window that organizes all UI components"""
    
    def __init__(self):
        super().__init__()
        
        # Setup window properties
        self.setWindowTitle("Python Network Monitor")
        self.resize(900, 700)
        
        # Initialize settings
        self.settings = QSettings()
        
        # Create the network monitor
        self.network_monitor = NetworkMonitor()
        
        # Setup UI
        self.setup_ui()
        
        # Create timer for updates
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_data)
        
        # Create tooltip for time series graph
        self.time_series_tooltip = TimeSeriesToolTip()
        
        # Reference to highlighted hop
        self.highlighted_hop = None
        
        # Load last session or initialize
        self.load_settings()
        
    def setup_ui(self):
        """Create and arrange all UI components"""
        # Create central widget with vertical layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)
        self.setCentralWidget(central_widget)
        
        # Add control panel at the top
        self.control_panel = ControlPanel(self.network_monitor)
        main_layout.addWidget(self.control_panel)
        
        # Create splitter for main content area
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        content_splitter.setChildrenCollapsible(False)
        main_layout.addWidget(content_splitter, 1)
        
        # Create middle area with hop data and bar graph
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create horizontal splitter for hop data and bar graph
        hop_splitter = QSplitter(Qt.Orientation.Horizontal)
        hop_splitter.setChildrenCollapsible(False)
        
        # Add hop data grid
        self.hop_data_grid = HopDataGrid()
        hop_splitter.addWidget(self.hop_data_grid)
        
        # Add latency bar graph
        self.latency_bar_graph = LatencyBarGraph()
        hop_splitter.addWidget(self.latency_bar_graph)
        
        # Set splitter sizes (70% for table, 30% for bar graph)
        hop_splitter.setSizes([600, 300])
        
        middle_layout.addWidget(hop_splitter)
        content_splitter.addWidget(middle_widget)
        
        # Create bottom area for time series visualization
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(0)
        
        # Add time window controls
        self.time_window_controls = TimeWindowControls()
        bottom_layout.addWidget(self.time_window_controls)
        
        # Create a horizontal splitter for time series graph and hop selector
        ts_splitter = QSplitter(Qt.Orientation.Horizontal)
        ts_splitter.setChildrenCollapsible(False)
        
        # Add time series graph
        self.time_series_graph = TimeSeriesGraph()
        ts_splitter.addWidget(self.time_series_graph)
        
        # Add hop selector panel
        self.hop_selector = HopSelector()
        ts_splitter.addWidget(self.hop_selector)
        
        # Set splitter sizes (85% for graph, 15% for hop selector)
        ts_splitter.setSizes([750, 150])
        
        bottom_layout.addWidget(ts_splitter, 1)
        
        # Set reference to hop selector in time window controls
        self.time_window_controls.hop_selector = self.hop_selector
        
        # Connect time window controls signals
        self.time_window_controls.window_changed.connect(self.time_series_graph.set_visible_window)
        self.time_window_controls.auto_scroll_changed.connect(self.time_series_graph.set_auto_scroll)
        self.time_window_controls.goto_latest_clicked.connect(self.time_series_graph.goto_latest)
        self.time_window_controls.final_hop_only_changed.connect(self.time_series_graph.set_final_hop_only_mode)
        self.time_series_graph.time_range_changed.connect(self.update_time_range_display)
        
        # Connect hop selector signals
        self.hop_selector.hop_visibility_changed.connect(self.time_series_graph.toggle_hop_visibility)
        self.hop_selector.all_hops_visibility_changed.connect(self.time_series_graph.toggle_all_hops_visibility)
        self.hop_selector.highlight_hop_changed.connect(self.highlight_hop)
        
        # Connect time series graph hover signal to tooltip update
        self.time_series_graph.hover_data_changed.connect(self.update_tooltip)
        
        # Connect timeseries graph signals to update hop selector UI
        self.time_series_graph.hop_visibility_updated.connect(self.sync_hop_selector_with_graph)
        
        # Add bottom widget to content splitter
        content_splitter.addWidget(bottom_widget)
        
        # Set splitter sizes (40% for middle area, 60% for time series graph)
        content_splitter.setSizes([300, 400])
        
        # Connect network monitor signals
        self.control_panel.interval_changed.connect(self.set_update_interval)
        self.control_panel.start_clicked.connect(self.start_monitoring)
        self.control_panel.pause_clicked.connect(self.pause_monitoring)
        self.control_panel.target_changed.connect(self.set_target)
        
        # Connect save/load signals
        self.control_panel.save_clicked.connect(self.save_session)
        
        # Connect hop data grid row selection to highlight function
        self.hop_data_grid.row_selected.connect(self.highlight_hop)
        
    def set_update_interval(self, interval_ms):
        """Set the update interval for network monitoring"""
        self.update_timer.setInterval(interval_ms)
        self.network_monitor.set_interval(interval_ms // 1000)  # Convert to seconds
        
    def start_monitoring(self):
        """Start or resume network monitoring"""
        if not self.update_timer.isActive():
            target = self.control_panel.get_current_target()
            if target:
                self.network_monitor.set_target(target)
                self.network_monitor.start()
                self.update_timer.start()
                self.control_panel.set_monitoring_active(True)
    
    def pause_monitoring(self):
        """Pause network monitoring"""
        if self.update_timer.isActive():
            self.update_timer.stop()
            self.network_monitor.pause()
            self.control_panel.set_monitoring_active(False)
    
    def set_target(self, target):
        """Set a new target for monitoring"""
        self.network_monitor.set_target(target)
        
    def update_data(self):
        """Update UI with latest monitoring data"""
        data = self.network_monitor.get_current_data()
        if data:
            self.hop_data_grid.update_data(data)
            self.latency_bar_graph.update_data(data)
            self.time_series_graph.add_data_point(data)
            self.hop_selector.update_hops(data)
    
    def save_session(self):
        """Save the current session data"""
        # Implement saving functionality
        pass
        
    def load_settings(self):
        """Load application settings and last session"""
        # Restore window geometry
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        # Set default interval
        default_interval = 2500  # 2.5 seconds in ms
        interval = self.settings.value("interval", default_interval, type=int)
        self.control_panel.set_interval(interval)
        self.set_update_interval(interval)
        
        # Load time window settings
        default_window = 60  # Default to 1 minute
        time_window = self.settings.value("time_window", default_window, type=int)
        self.time_window_controls.set_window(time_window)
        self.time_series_graph.set_visible_window(time_window)
        
        auto_scroll = self.settings.value("auto_scroll", True, type=bool)
        self.time_window_controls.set_auto_scroll(auto_scroll)
        self.time_series_graph.set_auto_scroll(auto_scroll)
        
        # Load last target
        last_target = self.settings.value("last_target", "")
        if last_target:
            self.control_panel.set_target(last_target)
            
        # Load visible hops settings
        # (Will be implemented when we have them)
            
    def save_settings(self):
        """Save application settings"""
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("interval", self.update_timer.interval())
        self.settings.setValue("last_target", self.control_panel.get_current_target())
        self.settings.setValue("time_window", self.time_window_controls.get_current_window())
        self.settings.setValue("auto_scroll", self.time_window_controls.auto_scroll_check.isChecked())
        
        # Save visible hops settings
        # (Will be implemented when we have them)
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.save_settings()
        event.accept()
        
    def update_time_range_display(self, x_min, x_max):
        """
        Update UI when the time range changes (due to user interaction)
        
        Args:
            x_min: Minimum X value (start time in seconds)
            x_max: Maximum X value (end time in seconds)
        """
        # Update auto-scroll status in the time window controls
        # If the range is showing the latest data, auto-scroll is likely enabled
        if self.time_series_graph.timestamps:
            latest_time = max(self.time_series_graph.timestamps)
            if abs(x_max - latest_time) < 5:  # Within 5 seconds of the latest data
                self.time_window_controls.set_auto_scroll(True)
            else:
                self.time_window_controls.set_auto_scroll(False)
                
        # Try to match the window size in the dropdown if it's close to a preset value
        window_size = x_max - x_min
        for i in range(self.time_window_controls.window_selector.count()):
            preset_size = self.time_window_controls.window_selector.itemData(i)
            if abs(window_size - preset_size) < preset_size * 0.1:  # Within 10% of a preset
                self.time_window_controls.window_selector.blockSignals(True)
                self.time_window_controls.window_selector.setCurrentIndex(i)
                self.time_window_controls.window_selector.blockSignals(False)
                break
                
    def update_tooltip(self, timestamp, hop_values):
        """Update the tooltip for time series graph hover
        
        Args:
            timestamp: The timestamp for the data point
            hop_values: List of (hop_num, latency) tuples
        """
        if hop_values:
            # Get mouse position and update tooltip
            cursor_pos = QCursor.pos()
            self.time_series_tooltip.update_tooltip(timestamp, hop_values)
            self.time_series_tooltip.move_to_position(cursor_pos.x(), cursor_pos.y())
        else:
            self.time_series_tooltip.hide()
            
    def highlight_hop(self, hop_num):
        """Highlight a specific hop in the UI
        
        Args:
            hop_num: The hop number to highlight
        """
        self.highlighted_hop = hop_num
        
        # Could implement hop highlighting in the time series graph
        # This would make the selected hop's line more prominent and others more faded

    def sync_hop_selector_with_graph(self):
        """Synchronize the hop selector UI with the graph's current visibility state"""
        logger.debug("sync_hop_selector_with_graph called")
        final_hop = self.time_series_graph.get_final_hop()
        logger.debug(f"Final hop: {final_hop}")
        logger.debug(f"Graph final_hop_only_mode: {self.time_series_graph.final_hop_only_mode}")
        logger.debug(f"Graph visible_hops: {self.time_series_graph.visible_hops}")
        
        # If the graph is in final hop only mode, update the hop selector accordingly
        if self.time_series_graph.final_hop_only_mode:
            logger.debug(f"Setting hop selector to final hop only mode: {final_hop}")
            self.hop_selector.set_final_hop_only_mode(True, final_hop)
            
            # Also ensure the checkbox in time window controls is checked
            logger.debug("Setting time window controls final hop only checkbox to checked")
            self.time_window_controls.set_final_hop_only(True)
        else:
            # If not in final hop only mode, restore normal hop visibility
            logger.debug("Disabling final hop only mode in hop selector")
            self.hop_selector.set_final_hop_only_mode(False)
            
            # Also ensure the checkbox in time window controls is unchecked
            logger.debug("Setting time window controls final hop only checkbox to unchecked")
            self.time_window_controls.set_final_hop_only(False)
            
            # Update individual hop checkboxes to match graph visibility
            for hop_num in self.hop_selector.hop_checkboxes:
                visible = hop_num in self.time_series_graph.visible_hops
                logger.debug(f"Setting hop {hop_num} visibility to {visible}")
                self.hop_selector.set_hop_visibility(hop_num, visible)