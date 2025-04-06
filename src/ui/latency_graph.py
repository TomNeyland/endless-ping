#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Bar graph visualization for latency by hop.
"""

import pyqtgraph as pg
import numpy as np
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QGraphicsRectItem  # Add this import

class LatencyBarGraph(pg.PlotWidget):
    """Horizontal bar graph showing latency by hop"""
    
    def __init__(self):
        super().__init__()
        
        # Data storage
        self.hop_data = []
        
        # Configure plot properties
        self.setup_plot()
        
        # Create bar graph item
        self.bars = None
        
        # Set up refresh timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_plot)
        self.timer.start(100)  # Refresh every 100ms
        
        self.apply_styles()
        
    def setup_plot(self):
        """Configure the plot appearance and behavior"""
        # Set background color
        self.setBackground('k')  # Black background
        
        # Configure axes
        self.plotItem.setLabel('left', 'Hop')
        self.plotItem.setLabel('bottom', 'Latency (ms)')
        
        # Configure appearance
        self.plotItem.showGrid(x=True, y=False, alpha=0.3)
        
        # Flip y-axis to match the hop table (top-to-bottom)
        self.plotItem.invertY(True)
        
        # Add a vertical line at 100ms threshold
        threshold_line = pg.InfiniteLine(pos=100, angle=90, pen=pg.mkPen('r', width=1, style=pg.QtCore.Qt.PenStyle.DotLine))
        self.plotItem.addItem(threshold_line)
        
        # Set initial axis range
        self.plotItem.setYRange(0, 10)  # Will auto-adjust based on hop count
        self.plotItem.setXRange(0, 150)
        
    def apply_styles(self):
        """Apply custom styles to the latency bar graph"""
        self.setBackground('#2b2b2b')
        self.plotItem.getAxis('left').setPen('#ffffff')
        self.plotItem.getAxis('bottom').setPen('#ffffff')
        self.plotItem.getAxis('left').setTextPen('#ffffff')
        self.plotItem.getAxis('bottom').setTextPen('#ffffff')
        
    def update_data(self, hop_data):
        """
        Update the graph with new hop data
        
        Args:
            hop_data: List of dictionaries containing hop information
        """
        self.hop_data = hop_data
        
    def refresh_plot(self):
        """Refresh the plot with current data"""
        if not self.hop_data:
            return

        # Extract latency and hop numbers
        hops = [hop['hop'] for hop in self.hop_data]
        latencies = [hop['current'] if hop['current'] > 0 else 0 for hop in self.hop_data]

        # Convert to numpy arrays for plotting
        y = np.array(hops)
        x = np.array(latencies)

        # Generate colors based on latency values
        colors = []
        for latency in latencies:
            if latency == 0:
                colors.append('#888888')  # Gray for no data
            elif latency > 100:
                colors.append('#ff6060')  # Red for high latency
            elif latency > 50:
                colors.append('#ffcc44')  # Yellow for medium latency
            else:
                colors.append('#60ff60')  # Green for low latency

        # Remove old bar graph if it exists
        if self.bars is not None:
            for bar in self.bars:
                self.plotItem.removeItem(bar)

        # Create new bars
        self.bars = []
        bar_width = 0.6
        for i, (latency, color) in enumerate(zip(latencies, colors)):
            bar = QGraphicsRectItem(0, i + 1 - bar_width / 2, latency, bar_width)
            bar.setBrush(pg.mkBrush(color))
            self.plotItem.addItem(bar)
            self.bars.append(bar)

        # Adjust y-axis range
        max_hop = max(y) if y.size > 0 else 10
        self.plotItem.setYRange(0, max_hop + 1)

        # Adjust x-axis range dynamically based on data
        max_latency = max(x) if x.size > 0 else 150
        self.plotItem.setXRange(0, max(150, max_latency * 1.1))