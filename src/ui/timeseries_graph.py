#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Time series graph for visualizing latency over time.
"""

import pyqtgraph as pg
import numpy as np
from collections import deque
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QPen

class TimeSeriesGraph(pg.PlotWidget):
    """Graph showing latency over time for all hops"""
    
    # Signal to notify when time limits have changed
    time_range_changed = pyqtSignal(float, float)
    # Signal emitted when hovering over the graph
    hover_data_changed = pyqtSignal(float, list)
    
    def __init__(self):
        super().__init__()
        
        # Maximum number of points to store (increased for longer time periods)
        self.max_points = 3600  # Store up to 1 hour at 1s intervals
        
        # Data storage - time and latency values
        self.timestamps = deque(maxlen=self.max_points)
        self.hop_lines = {}  # Dict of {hop_num: plot_data_item}
        self.hop_data = {}   # Dict of {hop_num: deque of latency values}
        self.hop_errors = {} # Dict of {hop_num: deque of error_type values}
        self.error_bands = []  # List of error band items
        self.visible_hops = set()  # Set of hop numbers that are currently visible
        
        # Mode settings
        self.final_hop_only_mode = False  # Only show the final hop line
        
        # Reference time (first data point)
        self.reference_time = None
        
        # Time window settings
        self.visible_window = 60  # Default: show last 60 seconds
        self.auto_scroll = True   # Default: auto-scroll to follow new data
        
        # Set up the plot
        self.setup_plot()
        
        # Apply custom styles
        self.apply_styles()
        
        # Set up auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_plot)
        self.timer.start(500)  # Refresh twice per second
        
        # Set up hover line
        self.hover_line = pg.InfiniteLine(angle=90, movable=False, pen=pg.mkPen(color='#888888', width=1, style=Qt.PenStyle.DashLine))
        self.hover_line.setVisible(False)
        self.plotItem.addItem(self.hover_line)
        
        # Connect mouse events for hover tooltip
        self.scene().sigMouseMoved.connect(self.on_mouse_moved)
        
    def setup_plot(self):
        """Configure the plot appearance and behavior"""
        # Set background color
        self.setBackground('k')  # Black background
        
        # Configure axes
        self.plotItem.setLabel('left', 'Latency (ms)')
        self.plotItem.setLabel('bottom', 'Time (s)')
        
        # Configure appearance
        self.plotItem.showGrid(x=True, y=True, alpha=0.3)
        
        # Enable mouse interaction
        self.plotItem.setMouseEnabled(x=True, y=True)
        self.plotItem.enableAutoRange()
        self.plotItem.setAutoVisible(y=True)
        
        # Add a horizontal line at 100ms threshold
        threshold_line = pg.InfiniteLine(pos=100, angle=0, pen=pg.mkPen('r', width=1, style=pg.QtCore.Qt.PenStyle.DotLine))
        self.plotItem.addItem(threshold_line)
        
        # Add legend
        self.legend = self.plotItem.addLegend()
        
        # Set initial axis range
        self.plotItem.setYRange(0, 150)
        self.plotItem.setXRange(0, self.visible_window)  # Show the initial window
        
        # Connect signals for view changes
        self.plotItem.sigXRangeChanged.connect(self.on_view_changed)
        
    def on_mouse_moved(self, pos):
        """Handle mouse movement for hover tooltip"""
        if not self.timestamps or len(self.timestamps) <= 1:
            return
            
        # Get mouse position in plot coordinates
        mouse_point = self.plotItem.vb.mapSceneToView(pos)
        x = mouse_point.x()
        
        # Check if x is within the data range
        if min(self.timestamps) <= x <= max(self.timestamps):
            # Show the hover line
            self.hover_line.setPos(x)
            self.hover_line.setVisible(True)
            
            # Find the closest timestamp
            closest_idx = min(range(len(self.timestamps)), 
                             key=lambda i: abs(self.timestamps[i] - x))
            closest_time = self.timestamps[closest_idx]
            
            # Collect data for all hops at this time point
            hop_values = []
            for hop_num, latency_data in sorted(self.hop_data.items()):
                if len(latency_data) > closest_idx:
                    value = latency_data[closest_idx]
                    if not np.isnan(value):
                        hop_values.append((hop_num, value))
            
            # Emit signal with hover data
            self.hover_data_changed.emit(closest_time, hop_values)
        else:
            # Hide the hover line when outside data range
            self.hover_line.setVisible(False)
            self.hover_data_changed.emit(0, [])
        
    def on_view_changed(self):
        """Handle manual view changes by the user"""
        # If the user manually changes the view, we may want to disable auto-scroll
        if self.timestamps:
            x_range = self.plotItem.viewRange()[0]
            x_max = max(self.timestamps)
            
            # Check if the view has significantly moved away from the latest data
            if x_range[1] < x_max - 5:  # More than 5 seconds behind latest data
                self.auto_scroll = False
            
            # Emit signal with current time range
            self.time_range_changed.emit(x_range[0], x_range[1])
        
    def apply_styles(self):
        """Apply custom styles to the time series graph"""
        self.setBackground('#2b2b2b')
        self.plotItem.getAxis('left').setPen('#ffffff')
        self.plotItem.getAxis('bottom').setPen('#ffffff')
        self.plotItem.getAxis('left').setTextPen('#ffffff')
        self.plotItem.getAxis('bottom').setTextPen('#ffffff')
        
    def add_data_point(self, hop_data):
        """
        Add a new data point for each hop
        
        Args:
            hop_data: List of dictionaries containing hop information
        """
        # Get current timestamp
        now = datetime.now()
        
        # Initialize reference time if needed
        if self.reference_time is None:
            self.reference_time = now
        
        # Calculate seconds since start
        seconds = (now - self.reference_time).total_seconds()
        
        # Add timestamp
        self.timestamps.append(seconds)
        
        # Process each hop
        for hop in hop_data:
            hop_num = hop['hop']
            latency = hop['current']
            error_type = hop.get('error_type')
            
            # Initialize data storage for this hop if needed
            if hop_num not in self.hop_data:
                self.hop_data[hop_num] = deque(maxlen=self.max_points)
                self.hop_errors[hop_num] = deque(maxlen=self.max_points)
                
                # Fill with NaN for previous timestamps
                for _ in range(len(self.timestamps) - 1):
                    self.hop_data[hop_num].append(float('nan'))
                    self.hop_errors[hop_num].append(None)
            
            # Add latency value (or NaN for timeouts)
            if latency > 0:
                self.hop_data[hop_num].append(latency)
            else:
                self.hop_data[hop_num].append(float('nan'))
            
            # Add error type
            self.hop_errors[hop_num].append(error_type)
        
        # Ensure all hops have the same number of data points
        for hop_num in self.hop_data:
            if len(self.hop_data[hop_num]) < len(self.timestamps):
                # Add NaN for missing data points
                while len(self.hop_data[hop_num]) < len(self.timestamps):
                    self.hop_data[hop_num].appendleft(float('nan'))
                    self.hop_errors[hop_num].appendleft(None)
    
    def refresh_plot(self):
        """Refresh the plot with current data"""
        if not self.timestamps:
            return
            
        # Create softer color palette for hops (using more muted/pastel colors)
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
        
        # Clean up old error bands (remove all existing bands)
        for band in self.error_bands:
            self.plotItem.removeItem(band)
        self.error_bands = []
        
        # Update the visible_hops set if it's empty (initialize with all hops)
        if not self.visible_hops and self.hop_data:
            self.visible_hops = set(self.hop_data.keys())
        
        # Get the final hop if in final hop only mode
        final_hop = self.get_final_hop() if self.final_hop_only_mode else None
        
        # Update each hop line
        for i, (hop_num, latency_data) in enumerate(sorted(self.hop_data.items())):
            # Skip if this hop is hidden or if in final hop only mode and not the final hop
            if hop_num not in self.visible_hops or (self.final_hop_only_mode and hop_num != final_hop):
                if hop_num in self.hop_lines:
                    self.hop_lines[hop_num].setVisible(False)
                
                # Even if the hop line is hidden, we still need to process error bands
                # If in final hop only mode, we still show all error bands
                if self.final_hop_only_mode:
                    self.process_error_bands(hop_num)
                    
                continue
                
            # Convert data to numpy arrays
            x = np.array(self.timestamps)
            y = np.array(latency_data)
            
            # Get color for this hop
            color_index = (hop_num - 1) % len(colors)
            color = colors[color_index]
            
            # Create or update line
            if hop_num not in self.hop_lines:
                # Create new line (using thinner line width of 1.5 instead of 2)
                pen = pg.mkPen(color=color, width=1.5)
                line = self.plotItem.plot(x, y, pen=pen, name=f"Hop {hop_num}")
                self.hop_lines[hop_num] = line
            else:
                # Update existing line and ensure it's visible
                self.hop_lines[hop_num].setVisible(True)
                self.hop_lines[hop_num].setData(x, y)
            
            # Process error bands for this hop    
            self.process_error_bands(hop_num)
        
        # Auto-scale Y axis if needed
        max_latency = 150  # Default
        for hop_num, latency_data in self.hop_data.items():
            # Only consider visible hops for y-axis scaling
            if hop_num in self.visible_hops and (not self.final_hop_only_mode or hop_num == final_hop):
                # Filter out NaN values
                filtered_data = [x for x in latency_data if not np.isnan(x)]
                if filtered_data:
                    current_max = max(filtered_data)
                    max_latency = max(max_latency, current_max * 1.1)
        
        # Adjust Y range if significantly different
        current_y_range = self.plotItem.viewRange()[1]
        if max_latency > current_y_range[1] * 0.9 or max_latency < current_y_range[1] * 0.5:
            self.plotItem.setYRange(0, max_latency)
        
        # Handle X-axis scrolling based on settings
        if self.auto_scroll and self.timestamps:
            x_max = max(self.timestamps)
            x_min = max(0, x_max - self.visible_window)
            self.plotItem.setXRange(x_min, x_max)
    
    def set_visible_window(self, seconds):
        """
        Set the visible time window in seconds
        
        Args:
            seconds: Number of seconds to display
        """
        self.visible_window = seconds
        
        # Update the view immediately if auto-scrolling is enabled
        if self.auto_scroll and self.timestamps:
            x_max = max(self.timestamps)
            x_min = max(0, x_max - self.visible_window)
            self.plotItem.setXRange(x_min, x_max)
    
    def set_auto_scroll(self, enabled):
        """
        Enable or disable auto-scrolling
        
        Args:
            enabled: Boolean to enable/disable auto-scrolling
        """
        self.auto_scroll = enabled
        
        # If enabling auto-scroll, immediately scroll to latest data
        if enabled and self.timestamps:
            x_max = max(self.timestamps)
            x_min = max(0, x_max - self.visible_window)
            self.plotItem.setXRange(x_min, x_max)
    
    def goto_latest(self):
        """Scroll to show the latest data"""
        if self.timestamps:
            x_max = max(self.timestamps)
            x_min = max(0, x_max - self.visible_window)
            self.plotItem.setXRange(x_min, x_max)
            self.auto_scroll = True
    
    def goto_time_range(self, x_min, x_max):
        """Set the visible time range explicitly"""
        self.auto_scroll = False
        self.plotItem.setXRange(x_min, x_max)
            
    def clear_data(self):
        """Clear all data and reset the plot"""
        self.timestamps.clear()
        self.hop_data.clear()
        
        # Remove all lines
        for line in self.hop_lines.values():
            self.plotItem.removeItem(line)
        
        self.hop_lines.clear()
        self.reference_time = None
        
    def toggle_hop_visibility(self, hop_num, visible):
        """Toggle visibility of a specific hop line
        
        Args:
            hop_num: The hop number to toggle
            visible: Boolean indicating whether the hop should be visible
        """
        if visible and hop_num not in self.visible_hops:
            self.visible_hops.add(hop_num)
        elif not visible and hop_num in self.visible_hops:
            self.visible_hops.remove(hop_num)
            
        # Update the plot immediately
        if hop_num in self.hop_lines:
            self.hop_lines[hop_num].setVisible(visible)
    
    def set_final_hop_only_mode(self, enabled):
        """Enable or disable final hop only mode
        
        Args:
            enabled: Boolean to enable/disable final hop only mode
        """
        self.final_hop_only_mode = enabled
        # Immediately refresh the plot
        self.refresh_plot()
    
    def get_final_hop(self):
        """Return the number of the final hop (highest hop number)
        
        Returns:
            The highest hop number or None if no hops
        """
        if not self.hop_data:
            return None
        return max(self.hop_data.keys())
    
    def process_error_bands(self, hop_num):
        """Process and draw error bands for a specific hop
        
        Args:
            hop_num: The hop number to process
        """
        error_data = list(self.hop_errors[hop_num])
        
        # Find contiguous regions with 'no_route' errors
        if 'no_route' in error_data:
            # Get timestamps for reference
            x = np.array(self.timestamps)
            
            # Find blocks of consecutive no_route errors
            in_error_block = False
            start_idx = None
            
            for i, error in enumerate(error_data):
                if error == 'no_route' and not in_error_block:
                    # Start of error block
                    start_idx = i
                    in_error_block = True
                elif error != 'no_route' and in_error_block:
                    # End of error block
                    end_idx = i
                    
                    # Create band for this block
                    if start_idx < len(x) and start_idx >= 0:
                        x_start = x[start_idx]
                        x_end = x[end_idx] if end_idx < len(x) else x[-1] + 1.0
                        
                        # Create a very visible band
                        band = pg.LinearRegionItem(
                            [x_start, x_end],
                            movable=False,
                            brush=pg.mkBrush(255, 0, 0, 100)  # Semi-transparent red
                        )
                        band.setZValue(-1)  # Behind data lines but above background
                        self.plotItem.addItem(band)
                        self.error_bands.append(band)
                    
                    in_error_block = False
            
            # Check if we ended in an error state
            if in_error_block and start_idx is not None and start_idx < len(x):
                x_start = x[start_idx]
                x_end = x[-1] + 1.0  # Extend to current time
                
                band = pg.LinearRegionItem(
                    [x_start, x_end],
                    movable=False,
                    brush=pg.mkBrush(255, 0, 0, 100)  # Semi-transparent red
                )
                band.setZValue(-1)
                self.plotItem.addItem(band)
                self.error_bands.append(band)