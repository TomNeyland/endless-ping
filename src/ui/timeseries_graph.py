#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Time series graph for visualizing latency over time.
"""

import pyqtgraph as pg
import numpy as np
from collections import deque
from datetime import datetime
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QPen

class TimeSeriesGraph(pg.PlotWidget):
    """Graph showing latency over time for all hops"""
    
    def __init__(self):
        super().__init__()
        
        # Maximum number of points to display (about 10 minutes at 1s intervals)
        self.max_points = 600
        
        # Data storage - time and latency values
        self.timestamps = deque(maxlen=self.max_points)
        self.hop_lines = {}  # Dict of {hop_num: plot_data_item}
        self.hop_data = {}   # Dict of {hop_num: deque of latency values}
        
        # Reference time (first data point)
        self.reference_time = None
        
        # Set up the plot
        self.setup_plot()
        
        # Apply custom styles
        self.apply_styles()
        
        # Set up auto-refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_plot)
        self.timer.start(500)  # Refresh twice per second
        
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
        self.plotItem.setXRange(0, 60)  # Show last 60 seconds by default
        
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
            
            # Initialize data storage for this hop if needed
            if hop_num not in self.hop_data:
                self.hop_data[hop_num] = deque(maxlen=self.max_points)
                # Fill with NaN for previous timestamps
                for _ in range(len(self.timestamps) - 1):
                    self.hop_data[hop_num].append(float('nan'))
            
            # Add latency value (or NaN for timeouts)
            if latency > 0:
                self.hop_data[hop_num].append(latency)
            else:
                self.hop_data[hop_num].append(float('nan'))
        
        # Ensure all hops have the same number of data points
        for hop_num in self.hop_data:
            if len(self.hop_data[hop_num]) < len(self.timestamps):
                # Add NaN for missing data points
                while len(self.hop_data[hop_num]) < len(self.timestamps):
                    self.hop_data[hop_num].appendleft(float('nan'))
    
    def refresh_plot(self):
        """Refresh the plot with current data"""
        if not self.timestamps:
            return
            
        # Create color palette for hops
        colors = [
            '#ff6060',  # Red
            '#60ff60',  # Green
            '#6060ff',  # Blue
            '#ffcc44',  # Yellow
            '#ff60ff',  # Magenta
            '#60ffff',  # Cyan
            '#ff8040',  # Orange
            '#40ff80',  # Light green
            '#8040ff',  # Purple
            '#ff4080',  # Pink
        ]
        
        # Update each hop line
        for i, (hop_num, latency_data) in enumerate(sorted(self.hop_data.items())):
            # Convert data to numpy arrays
            x = np.array(self.timestamps)
            y = np.array(latency_data)
            
            # Get color for this hop
            color_index = (hop_num - 1) % len(colors)
            color = colors[color_index]
            
            # Create or update line
            if hop_num not in self.hop_lines:
                # Create new line
                pen = pg.mkPen(color=color, width=2)
                line = self.plotItem.plot(x, y, pen=pen, name=f"Hop {hop_num}")
                self.hop_lines[hop_num] = line
            else:
                # Update existing line
                self.hop_lines[hop_num].setData(x, y)
        
        # Auto-scale Y axis if needed
        max_latency = 150  # Default
        for latency_data in self.hop_data.values():
            # Filter out NaN values
            filtered_data = [x for x in latency_data if not np.isnan(x)]
            if filtered_data:
                current_max = max(filtered_data)
                max_latency = max(max_latency, current_max * 1.1)
        
        # Adjust Y range if significantly different
        current_y_range = self.plotItem.viewRange()[1]
        if max_latency > current_y_range[1] * 0.9 or max_latency < current_y_range[1] * 0.5:
            self.plotItem.setYRange(0, max_latency)
        
        # Auto-scroll X axis if viewing the most recent data
        x_range = self.plotItem.viewRange()[0]
        x_max = max(self.timestamps) if self.timestamps else 0
        
        # Check if we're viewing the latest data (within 10% of the end)
        if x_range[1] > x_max - (x_range[1] - x_range[0]) * 0.1:
            # Auto-scroll to keep showing the latest data
            x_min = max(0, x_max - (x_range[1] - x_range[0]))
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