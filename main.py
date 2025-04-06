#!/usr/bin/env python3
"""
Network Monitoring Tool - PingPlotter-style Application

A comprehensive network monitoring tool for visualizing latency and packet loss
across network hops. Features include real-time monitoring, visualization, and
session persistence.

This single-file version contains all components of the application for easy
distribution and execution.
"""
import sys
import os
import logging
import subprocess
import platform
import re
import socket
import time
import json
import threading
from queue import Queue
from typing import List, Dict, Any, Optional
from collections import defaultdict, deque
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QDoubleSpinBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QSizePolicy,
    
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QColor, QBrush

import pyqtgraph as pg
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Dark mode stylesheet - defined as a string for single file distribution
DARK_STYLE = """
/* Dark Style Sheet for Network Monitor */

/* Main Application */
QMainWindow, QDialog {
    background-color: #2D2D30;
    color: #F0F0F0;
}

QWidget {
    background-color: #2D2D30;
    color: #F0F0F0;
}

/* Menu Bar */
QMenuBar {
    background-color: #1E1E1E;
    color: #F0F0F0;
}

QMenuBar::item {
    background-color: transparent;
    padding: 4px 10px;
}

QMenuBar::item:selected {
    background-color: #3E3E40;
}

QMenu {
    background-color: #1E1E1E;
    color: #F0F0F0;
    border: 1px solid #3E3E40;
}

QMenu::item {
    padding: 6px 20px;
}

QMenu::item:selected {
    background-color: #3E3E40;
}

/* Status Bar */
QStatusBar {
    background-color: #1E1E1E;
    color: #F0F0F0;
}

/* Controls */
QPushButton {
    background-color: #3E3E40;
    color: #F0F0F0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 5px 15px;
    min-width: 80px;
}

QPushButton:hover {
    background-color: #505050;
}

QPushButton:pressed {
    background-color: #555555;
}

QPushButton:disabled {
    background-color: #2D2D30;
    color: #808080;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: #252526;
    color: #F0F0F0;
    border: 1px solid #555555;
    border-radius: 3px;
    padding: 4px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #007ACC;
}

QComboBox::drop-down {
    border: 0px;
    width: 20px;
}

QComboBox QAbstractItemView {
    background-color: #252526;
    color: #F0F0F0;
    border: 1px solid #555555;
    selection-background-color: #3E3E40;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #252526;
    color: #F0F0F0;
    border: 1px solid #3E3E40;
    gridline-color: #3E3E40;
    selection-background-color: #3F3F46;
    selection-color: #FFFFFF;
    alternate-background-color: #2A2A2C;
}

QTableWidget::item, QTableView::item {
    border: 0px;
    padding: 5px;
}

QHeaderView {
    background-color: #1E1E1E;
    color: #F0F0F0;
}

QHeaderView::section {
    background-color: #1E1E1E;
    color: #F0F0F0;
    padding: 5px;
    border: 1px solid #3E3E40;
}

QHeaderView::section:checked {
    background-color: #007ACC;
}

/* Scroll Bars */
QScrollBar:vertical {
    background-color: #2D2D30;
    width: 12px;
    margin: 12px 0px 12px 0px;
    border: 1px solid #3E3E40;
}

QScrollBar:horizontal {
    background-color: #2D2D30;
    height: 12px;
    margin: 0px 12px 0px 12px;
    border: 1px solid #3E3E40;
}

QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
    background-color: #3E3E40;
}

QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    background-color: #2D2D30;
    height: 12px;
    width: 12px;
    subcontrol-origin: margin;
}

QScrollBar::add-line:vertical {
    subcontrol-position: bottom;
}

QScrollBar::sub-line:vertical {
    subcontrol-position: top;
}

QScrollBar::add-line:horizontal {
    subcontrol-position: right;
}

QScrollBar::sub-line:horizontal {
    subcontrol-position: left;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3E3E40;
}

QTabBar::tab {
    background-color: #2D2D30;
    color: #F0F0F0;
    border: 1px solid #3E3E40;
    padding: 6px 12px;
    margin-right: 2px;
}

QTabBar::tab:selected {
    background-color: #3E3E40;
    border-bottom-color: #3E3E40;
}

QTabBar::tab:hover:!selected {
    background-color: #3E3E40;
}

/* Splitter */
QSplitter::handle {
    background-color: #3E3E40;
}

QSplitter::handle:horizontal {
    width: 3px;
}

QSplitter::handle:vertical {
    height: 3px;
}

QSplitter::handle:hover {
    background-color: #007ACC;
}
"""


#------------------------------------------------------------------------------
# Core Functionality
#------------------------------------------------------------------------------

class NetworkMonitor:
    """Handles network monitoring operations including ping and traceroute"""
    
    def __init__(self):
        self.running = False
        self.target = ""
        self.interval = 2.5  # Default interval in seconds
        self.max_hops = 30
        self.timeout = 1000  # Timeout in milliseconds
        self.results_queue = Queue()
        self.monitor_thread = None
        self.os_type = platform.system().lower()
    
    def set_target(self, target: str) -> None:
        """Set the target to monitor"""
        self.target = target
    
    def set_interval(self, interval: float) -> None:
        """Set the interval between pings"""
        self.interval = max(1.0, min(interval, 10.0))  # Clamp between 1 and 10 seconds
    
    def start_monitoring(self) -> None:
        """Start the monitoring process"""
        if not self.target:
            logger.error("No target specified")
            return
        
        if self.running:
            logger.warning("Monitoring already running")
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitoring_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        logger.info(f"Started monitoring {self.target} at {self.interval}s intervals")
    
    def stop_monitoring(self) -> None:
        """Stop the monitoring process"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        logger.info("Stopped monitoring")
    
    def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        # Run traceroute once to establish the path
        trace_result = self.run_traceroute(self.target)
        hop_ips = {hop.get("hop"): hop.get("ip") for hop in trace_result if hop.get("ip")}
        
        while self.running:
            try:
                timestamp = time.time()
                results = {
                    "timestamp": timestamp,
                    "target": self.target,
                    "hops": []
                }
                
                # Ping each hop from the traceroute
                for hop_num, ip in hop_ips.items():
                    if ip:
                        ping_result = self.ping_host(ip, count=1)
                        hop_data = {
                            "hop": hop_num,
                            "ip": ip,
                            "hostname": next((h.get("hostname") for h in trace_result if h.get("hop") == hop_num), ip),
                            "latency": ping_result.get("latency"),
                            "packet_loss": ping_result.get("packet_loss")
                        }
                        results["hops"].append(hop_data)
                
                # Put results in queue for processing
                self.results_queue.put(results)
                
                # Sleep for the specified interval
                time.sleep(self.interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(1)  # Wait a bit before retrying
    
    def run_traceroute(self, target: str) -> List[Dict[str, Any]]:
        """
        Run traceroute to the specified target
        Returns a list of hops with IP, hostname, and hop number
        """
        hops = []
        
        try:
            # Windows uses tracert, Unix-like systems use traceroute
            if self.os_type == "windows":
                cmd = ["tracert", "-d", "-w", str(self.timeout), "-h", str(self.max_hops), target]
            else:  # Linux, Darwin (macOS)
                cmd = ["traceroute", "-n", "-w", "1", "-m", str(self.max_hops), target]
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Process output line by line
            for line in process.stdout:
                hop_data = self._parse_traceroute_line(line)
                if hop_data:
                    hops.append(hop_data)
            
            process.wait()
            
        except Exception as e:
            logger.error(f"Error running traceroute: {str(e)}")
        
        return hops
    
    def _parse_traceroute_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a line from traceroute output"""
        line = line.strip()
        
        # Skip header lines
        if "traceroute to" in line.lower() or "tracing route to" in line.lower():
            return None
        
        # Windows format: "  1    <1 ms    <1 ms    <1 ms  192.168.1.1"
        # Unix format: " 1  192.168.1.1  0.123 ms  0.456 ms  0.789 ms"
        
        hop_match = re.search(r'^\s*(\d+)', line)
        ip_match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
        
        if not hop_match:
            return None
        
        hop_num = int(hop_match.group(1))
        ip = ip_match.group(1) if ip_match else None
        
        # Handle timeouts, marked by * in traceroute output
        if "*" in line and not ip:
            return {
                "hop": hop_num,
                "ip": None,
                "hostname": None,
                "latency": None,
                "packet_loss": 100  # 100% packet loss
            }
        
        # Try to resolve hostname if IP is available
        hostname = None
        if ip:
            try:
                hostname_info = socket.gethostbyaddr(ip)
                hostname = hostname_info[0]
            except (socket.herror, socket.gaierror):
                hostname = ip  # Use IP as hostname if resolution fails
        
        return {
            "hop": hop_num,
            "ip": ip,
            "hostname": hostname,
            "latency": None,  # Will be filled by ping
            "packet_loss": None  # Will be filled by ping
        }
    
    def ping_host(self, host: str, count: int = 4) -> Dict[str, Any]:
        result = {
            "min": None,
            "max": None,
            "avg": None,
            "latency": None,  # Current latency
            "packet_loss": 100.0  # Default to 100% packet loss
        }
        
        try:
            # Windows and Unix-like systems have different ping commands
            if self.os_type == "windows":
                cmd = ["ping", "-n", str(count), "-w", str(self.timeout), host]
            else:  # Linux, Darwin (macOS)
                cmd = ["ping", "-c", str(count), host]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            output, error = process.communicate()
            
            if process.returncode != 0:
                # Log unreachable host
                logger.warning(f"Host {host} is unreachable: {error.strip()}")
                return result
            
            # Parse the output
            latencies = []
            time_pattern = re.compile(r'time[=<](\d+\.?\d*)(\s?ms)?')
            round_trip_pattern = re.compile(r'round-trip min/avg/max/stddev = (\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+)/(\d+\.\d+) ms')
            
            for line in output.splitlines():
                # Match individual ping times
                match = time_pattern.search(line)
                if match:
                    latency = float(match.group(1))
                    latencies.append(latency)
                
                # Match round-trip statistics
                round_trip_match = round_trip_pattern.search(line)
                if round_trip_match:
                    result["min"] = float(round_trip_match.group(1))
                    result["avg"] = float(round_trip_match.group(2))
                    result["max"] = float(round_trip_match.group(3))
            
            # Calculate packet loss
            if count > 0 and latencies:
                result["packet_loss"] = (1 - len(latencies) / count) * 100
                result["latency"] = latencies[-1]  # Most recent latency
            else:
                result["packet_loss"] = 100.0
        
        except Exception as e:
            logger.error(f"Error pinging host {host}: {str(e)}")
        
        return result


class StatisticsProcessor:
    """Processes and stores network monitoring statistics"""
    
    def __init__(self, history_length: int = 600):
        """
        Initialize the statistics processor
        
        Args:
            history_length: Number of data points to keep in history (default: 600 = 10 minutes at 1 ping/sec)
        """
        self.history_length = history_length
        self.target_history = {}  # Dict of target -> list of results
        self.current_stats = {}  # Dict of target -> current statistics
    
    def process_result(self, result: Dict[str, Any]) -> None:
        """
        Process a new result from the network monitor
        
        Args:
            result: Dict containing timestamp, target, and hop data
        """
        target = result.get("target")
        timestamp = result.get("timestamp")
        hops = result.get("hops", [])
        
        if not target or not timestamp or not hops:
            logger.warning("Invalid result data")
            return
        
        # Initialize target history if not exists
        if target not in self.target_history:
            self.target_history[target] = deque(maxlen=self.history_length)
        
        # Add result to history
        self.target_history[target].append(result)
        
        # Update current statistics
        self._update_statistics(target)
    
    def _update_statistics(self, target: str) -> None:
        """
        Update statistics for a target
        
        Args:
            target: The target hostname/IP to update stats for
        """
        if target not in self.target_history or not self.target_history[target]:
            return
        
        history = self.target_history[target]
        
        # Initialize stats structure
        hop_stats = defaultdict(lambda: {
            "count": 0,
            "avg": 0.0,
            "min": float('inf'),
            "max": 0.0,
            "current": 0.0,
            "packet_loss": 0.0,
            "latency_history": [],
            "hop": 0,
            "ip": "",
            "hostname": ""
        })
        
        # Process each result in history to build statistics
        for result in history:
            for hop_data in result.get("hops", []):
                hop_num = hop_data.get("hop")
                if hop_num is None:
                    continue
                
                latency = hop_data.get("latency")
                packet_loss = hop_data.get("packet_loss", 0.0)
                
                # Update basic hop info
                hop_stats[hop_num]["hop"] = hop_num
                hop_stats[hop_num]["ip"] = hop_data.get("ip", "")
                hop_stats[hop_num]["hostname"] = hop_data.get("hostname", "")
                
                # Update statistics
                if latency is not None:
                    hop_stats[hop_num]["count"] += 1
                    hop_stats[hop_num]["current"] = latency
                    hop_stats[hop_num]["min"] = min(hop_stats[hop_num]["min"], latency)
                    hop_stats[hop_num]["max"] = max(hop_stats[hop_num]["max"], latency)
                    
                    # Update running average
                    count = hop_stats[hop_num]["count"]
                    if count > 1:
                        hop_stats[hop_num]["avg"] = (
                            (hop_stats[hop_num]["avg"] * (count - 1) + latency) / count
                        )
                    else:
                        hop_stats[hop_num]["avg"] = latency
                    
                    # Store latency in history
                    hop_stats[hop_num]["latency_history"].append((result["timestamp"], latency))
                
                # Update packet loss (use most recent value)
                if packet_loss is not None:
                    hop_stats[hop_num]["packet_loss"] = packet_loss
        
        # Convert to list sorted by hop number and cleanup infinite values
        stats_list = []
        for hop_num, stats in sorted(hop_stats.items()):
            if stats["min"] == float('inf'):
                stats["min"] = 0.0
            
            # Ensure latency_history doesn't grow too large
            stats["latency_history"] = stats["latency_history"][-self.history_length:]
            
            stats_list.append(stats)
        
        # Store updated statistics
        self.current_stats[target] = stats_list
    
    def get_current_stats(self, target: str) -> List[Dict[str, Any]]:
        """
        Get current statistics for a target
        
        Args:
            target: The target hostname/IP
            
        Returns:
            List of statistics for each hop
        """
        return self.current_stats.get(target, [])
    
    def get_hop_history(self, target: str, hop: int) -> List[tuple]:
        """
        Get latency history for a specific hop
        
        Args:
            target: The target hostname/IP
            hop: The hop number
            
        Returns:
            List of (timestamp, latency) tuples
        """
        stats = self.current_stats.get(target, [])
        for hop_stats in stats:
            if hop_stats["hop"] == hop:
                return hop_stats.get("latency_history", [])
        return []
    
    def get_all_hop_history(self, target: str) -> Dict[int, List[tuple]]:
        """
        Get latency history for all hops of a target
        
        Args:
            target: The target hostname/IP
            
        Returns:
            Dict of hop number -> list of (timestamp, latency) tuples
        """
        result = {}
        stats = self.current_stats.get(target, [])
        for hop_stats in stats:
            hop_num = hop_stats["hop"]
            result[hop_num] = hop_stats.get("latency_history", [])
        return result
    
    def clear_history(self, target: Optional[str] = None) -> None:
        """
        Clear history for a target or all targets
        
        Args:
            target: Target to clear, or None to clear all
        """
        if target:
            if target in self.target_history:
                del self.target_history[target]
            if target in self.current_stats:
                del self.current_stats[target]
        else:
            self.target_history.clear()
            self.current_stats.clear()


class SessionStorage:
    """Handles session persistence for the network monitor"""
    
    def __init__(self, base_dir: str = None):
        """
        Initialize the session storage
        
        Args:
            base_dir: Base directory for session files, defaults to user's home directory
        """
        if base_dir is None:
            self.base_dir = os.path.join(Path.home(), ".network_monitor")
        else:
            self.base_dir = base_dir
        
        # Create directory if it doesn't exist
        os.makedirs(self.base_dir, exist_ok=True)
        
        # Path to auto-save session
        self.auto_save_path = os.path.join(self.base_dir, "last_session.json")
        
        # Keep track of recent targets
        self.recent_targets = []
        self._load_recent_targets()
    
    def save_session(self, target: str, stats: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Save a session to file
        
        Args:
            target: Target hostname/IP
            stats: List of statistics for each hop
            filepath: Custom file path, or None to generate one
            
        Returns:
            Path to the saved file
        """
        if filepath is None:
            # Generate filename based on target and timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{target.replace('.', '_')}_{timestamp}.json"
            filepath = os.path.join(self.base_dir, filename)
        
        session_data = {
            "target": target,
            "timestamp": time.time(),
            "stats": stats
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2)
            logger.info(f"Session saved to {filepath}")
            
            # Add to recent targets
            self._add_recent_target(target)
            
            return filepath
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return ""
    
    def auto_save_session(self, target: str, stats: List[Dict[str, Any]]) -> None:
        """
        Auto-save the current session
        
        Args:
            target: Target hostname/IP
            stats: List of statistics for each hop
        """
        self.save_session(target, stats, self.auto_save_path)
    
    def load_session(self, filepath: str) -> Dict[str, Any]:
        """
        Load a session from file
        
        Args:
            filepath: Path to the session file
            
        Returns:
            Session data dict or empty dict if error
        """
        try:
            with open(filepath, 'r') as f:
                session_data = json.load(f)
            
            # Add to recent targets
            target = session_data.get("target")
            if target:
                self._add_recent_target(target)
            
            return session_data
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return {}
    
    def load_auto_saved_session(self) -> Dict[str, Any]:
        """
        Load the auto-saved session
        
        Returns:
            Auto-saved session data or empty dict if none
        """
        if os.path.exists(self.auto_save_path):
            return self.load_session(self.auto_save_path)
        return {}
    
    def export_csv(self, target: str, stats: List[Dict[str, Any]], filepath: Optional[str] = None) -> str:
        """
        Export statistics as CSV
        
        Args:
            target: Target hostname/IP
            stats: List of statistics for each hop
            filepath: Custom file path, or None to generate one
            
        Returns:
            Path to the saved file
        """
        if filepath is None:
            # Generate filename based on target and timestamp
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{target.replace('.', '_')}_{timestamp}.csv"
            filepath = os.path.join(self.base_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                # Write CSV header
                f.write("Hop,IP,Hostname,Count,Min,Max,Avg,Current,PacketLoss\n")
                
                # Write data rows
                for hop in stats:
                    row = [
                        str(hop.get("hop", "")),
                        hop.get("ip", ""),
                        hop.get("hostname", ""),
                        str(hop.get("count", 0)),
                        f"{hop.get('min', 0):.1f}",
                        f"{hop.get('max', 0):.1f}",
                        f"{hop.get('avg', 0):.1f}",
                        f"{hop.get('current', 0):.1f}",
                        f"{hop.get('packet_loss', 0):.1f}"
                    ]
                    f.write(",".join(row) + "\n")
            
            logger.info(f"CSV exported to {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error exporting CSV: {str(e)}")
            return ""
    
    def _add_recent_target(self, target: str) -> None:
        """
        Add a target to the recent targets list
        
        Args:
            target: Target hostname/IP
        """
        # Remove if already exists (to move to front)
        if target in self.recent_targets:
            self.recent_targets.remove(target)
        
        # Add to front
        self.recent_targets.insert(0, target)
        
        # Keep only the 10 most recent
        self.recent_targets = self.recent_targets[:10]
        
        # Save to file
        self._save_recent_targets()
    
    def _save_recent_targets(self) -> None:
        """Save recent targets to file"""
        recent_targets_path = os.path.join(self.base_dir, "recent_targets.json")
        try:
            with open(recent_targets_path, 'w') as f:
                json.dump(self.recent_targets, f)
        except Exception as e:
            logger.error(f"Error saving recent targets: {str(e)}")
    
    def _load_recent_targets(self) -> None:
        """Load recent targets from file"""
        recent_targets_path = os.path.join(self.base_dir, "recent_targets.json")
        if os.path.exists(recent_targets_path):
            try:
                with open(recent_targets_path, 'r') as f:
                    self.recent_targets = json.load(f)
            except Exception as e:
                logger.error(f"Error loading recent targets: {str(e)}")
                self.recent_targets = []
        else:
            self.recent_targets = []
    
    def get_recent_targets(self) -> List[str]:
        """
        Get list of recent targets
        
        Returns:
            List of recent target hostnames/IPs
        """
        return self.recent_targets


#------------------------------------------------------------------------------
# UI Components
#------------------------------------------------------------------------------

class ControlPanel(QWidget):
    """Control panel with target input, interval selection, and control buttons"""
    
    # Signals
    target_entered = pyqtSignal(str)
    interval_changed = pyqtSignal(float)
    start_clicked = pyqtSignal()
    pause_clicked = pyqtSignal()
    
    def __init__(self, recent_targets=None):
        super().__init__()
        
        self.recent_targets = recent_targets or []
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the control panel UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)
        
        # Target input with label
        layout.addWidget(QLabel("Target:"))
        
        # Combobox for target selection
        self.target_combo = QComboBox()
        self.target_combo.setEditable(True)
        self.target_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.target_combo.setMinimumWidth(200)
        self.target_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Fixed
        )
        
        # Add recent targets
        for target in self.recent_targets:
            self.target_combo.addItem(target)
        
        # Connect to enter pressed
        self.target_combo.lineEdit().returnPressed.connect(self._on_target_entered)
        self.target_combo.activated.connect(self._on_target_selected)
        
        layout.addWidget(self.target_combo)
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_button)
        
        # Pause button
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.pause_button.setEnabled(False)
        layout.addWidget(self.pause_button)
        
        # Interval selection
        layout.addWidget(QLabel("Interval:"))
        
        self.interval_spin = QDoubleSpinBox()
        self.interval_spin.setRange(1.0, 10.0)
        self.interval_spin.setValue(2.5)
        self.interval_spin.setSuffix(" s")
        self.interval_spin.setSingleStep(0.5)
        self.interval_spin.valueChanged.connect(self._on_interval_changed)
        layout.addWidget(self.interval_spin)
        
        # Focus mode (optional - for future implementation)
        layout.addWidget(QLabel("Focus:"))
        
        self.focus_combo = QComboBox()
        self.focus_combo.addItem("Auto")
        self.focus_combo.addItem("All Hops")
        self.focus_combo.addItem("Problem Hops")
        layout.addWidget(self.focus_combo)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_button)
    
    def _on_target_entered(self):
        """Handle target manually entered"""
        target = self.target_combo.currentText().strip()
        if not target:
            return
        
        self.target_entered.emit(target)
        self.add_recent_target(target)
    
    def _on_target_selected(self, index):
        """Handle target selected from dropdown"""
        target = self.target_combo.itemText(index).strip()
        if target:
            self.target_entered.emit(target)
    
    def _on_start_clicked(self):
        """Handle start button click"""
        # Ensure a target is set
        target = self.target_combo.currentText().strip()
        if not target:
            return
        
        self.target_entered.emit(target)
        self.add_recent_target(target)
        
        # Emit start signal
        self.start_clicked.emit()
        
        # Update button states
        self.start_button.setEnabled(False)
        self.pause_button.setEnabled(True)
    
    def _on_pause_clicked(self):
        """Handle pause button click"""
        self.pause_clicked.emit()
        
        # Update button states
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
    
    def _on_interval_changed(self, value):
        """Handle interval changed"""
        self.interval_changed.emit(value)
    
    def _on_save_clicked(self):
        """Handle save button click - pass to parent window"""
        # This will be handled by the main window's menu action
        pass
    
    def add_recent_target(self, target):
        """Add a target to recent targets list"""
        # Remove if exists (to move to top)
        for i in range(self.target_combo.count()):
            if self.target_combo.itemText(i) == target:
                self.target_combo.removeItem(i)
                break
        
        # Add to top
        self.target_combo.insertItem(0, target)
        self.target_combo.setCurrentIndex(0)
        
        # Keep only 10 most recent
        while self.target_combo.count() > 10:
            self.target_combo.removeItem(self.target_combo.count() - 1)
    
    def clear_target(self):
        """Clear the current target"""
        self.target_combo.setCurrentText("")
        
        # Reset button states
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
    
    def set_target(self, target):
        """Set the current target"""
        self.target_combo.setCurrentText(target)


class DataGrid(QTableWidget):
    """Table widget for displaying hop statistics"""
    
    def __init__(self):
        super().__init__()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the data grid UI"""
        # Set column headers
        headers = ["Hop", "Count", "IP", "Hostname", "Avg", "Min", "Cur", "PL%"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table properties
        self.setAlternatingRowColors(True)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.setSortingEnabled(False)  # Disable sorting initially
        
        # Set column widths
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setStretchLastSection(False)
        
        # Set column width hints
        col_widths = [50, 70, 120, 250, 70, 70, 70, 70]
        for col, width in enumerate(col_widths):
            self.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.setColumnWidth(col, width)
        
        # Set vertical header (row numbers) to minimal width
        self.verticalHeader().setVisible(False)
    
    def update_data(self, hop_stats):
        """
        Update the data grid with new hop statistics
        
        Args:
            hop_stats: List of hop statistics dictionaries
        """
        # Disable sorting temporarily for better performance
        was_sorting_enabled = self.isSortingEnabled()
        self.setSortingEnabled(False)
        
        # Set row count
        num_hops = len(hop_stats)
        self.setRowCount(num_hops)
        
        # Update data for each hop
        for row, hop in enumerate(hop_stats):
            # Hop number
            hop_item = QTableWidgetItem(str(hop.get("hop", "")))
            hop_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 0, hop_item)
            
            # Count
            count_item = QTableWidgetItem(str(hop.get("count", 0)))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 1, count_item)
            
            # IP address
            ip_item = QTableWidgetItem(hop.get("ip", ""))
            self.setItem(row, 2, ip_item)
            
            # Hostname
            hostname_item = QTableWidgetItem(hop.get("hostname", ""))
            self.setItem(row, 3, hostname_item)
            
            # Average latency
            avg_latency = hop.get("avg", 0)
            avg_item = QTableWidgetItem(f"{avg_latency:.1f}" if avg_latency is not None else "")
            avg_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            avg_item.setBackground(self._get_latency_color(avg_latency))
            self.setItem(row, 4, avg_item)
            
            # Minimum latency
            min_latency = hop.get("min", 0)
            min_item = QTableWidgetItem(f"{min_latency:.1f}" if min_latency is not None else "")
            min_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.setItem(row, 5, min_item)
            
            # Current latency
            cur_latency = hop.get("current", 0)
            cur_item = QTableWidgetItem(f"{cur_latency:.1f}" if cur_latency is not None else "")
            cur_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            cur_item.setBackground(self._get_latency_color(cur_latency))
            self.setItem(row, 6, cur_item)
            
            # Packet loss
            packet_loss = hop.get("packet_loss", 0)
            pl_item = QTableWidgetItem(f"{packet_loss:.1f}" if packet_loss is not None else "")
            pl_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            pl_item.setBackground(self._get_packet_loss_color(packet_loss))
            self.setItem(row, 7, pl_item)
        
        # Restore sorting if it was enabled
        self.setSortingEnabled(was_sorting_enabled)
    
    def clear_data(self):
        """Clear all data from the grid"""
        self.setRowCount(0)
    
    def _get_latency_color(self, latency):
        """
        Get background color based on latency value
        Green: < 50ms, Yellow: 50-100ms, Red: > 100ms
        """
        if latency is None or latency < 0:
            return QBrush(QColor(255, 255, 255))  # White for no data
        
        if latency < 50:
            return QBrush(QColor(144, 238, 144))  # Light green
        elif latency < 100:
            return QBrush(QColor(255, 255, 224))  # Light yellow
        else:
            return QBrush(QColor(255, 200, 200))  # Light red
    
    def _get_packet_loss_color(self, packet_loss):
        """
        Get background color based on packet loss value
        Green: 0%, Yellow: 0-5%, Orange: 5-20%, Red: > 20%
        """
        if packet_loss is None or packet_loss < 0:
            return QBrush(QColor(255, 255, 255))  # White for no data
        
        if packet_loss == 0:
            return QBrush(QColor(144, 238, 144))  # Light green
        elif packet_loss < 5:
            return QBrush(QColor(255, 255, 224))  # Light yellow
        elif packet_loss < 20:
            return QBrush(QColor(255, 200, 150))  # Light orange
        else:
            return QBrush(QColor(255, 150, 150))  # Light red


class LatencyBarGraph(QWidget):
    """Bar graph for displaying hop latencies"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data
        self.hop_numbers = []
        self.latencies = []
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the latency graph UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Configure plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)  # Transparent background
        self.plot_widget.setLabel('left', 'Hop')
        self.plot_widget.setLabel('bottom', 'Latency (ms)')
        self.plot_widget.setTitle('Hop Latency')
        
        # Setup bar graph
        self.bar_graph = pg.BarGraphItem(
            x0=0,
            y=[], 
            height=0.6, 
            width=[],
            brush='g'
        )
        self.plot_widget.addItem(self.bar_graph)
        
        # Set axes
        self.plot_widget.getAxis('left').setStyle(tickLength=0)
        self.plot_widget.setYRange(0, 10)  # Initial range
        self.plot_widget.setXRange(0, 100)  # Initial range
        
        # Add grid
        self.plot_widget.showGrid(x=True, y=False)
        
        layout.addWidget(self.plot_widget)
    
    def update_data(self, hop_stats):
        """
        Update the graph with new hop statistics
        
        Args:
            hop_stats: List of hop statistics dictionaries
        """
        if not hop_stats:
            return
        
        # Extract data
        self.hop_numbers = [hop.get("hop") for hop in hop_stats]
        self.latencies = [hop.get("current", 0) for hop in hop_stats]
        
        # Replace None values with 0
        self.latencies = [0 if lat is None else lat for lat in self.latencies]
        
        # Create colors based on latency thresholds
        colors = []
        for lat in self.latencies:
            if lat < 50:
                colors.append('g')  # Green
            elif lat < 100:
                colors.append('y')  # Yellow
            else:
                colors.append('r')  # Red
        
        # Update bar graph
        self.bar_graph.setOpts(
            x=self.latencies,
            y=self.hop_numbers,
            width=self.latencies,
            brushes=colors
        )
        
        # Adjust plot range
        max_latency = max(self.latencies) if self.latencies else 100
        self.plot_widget.setXRange(0, max(100, max_latency * 1.1))
        self.plot_widget.setYRange(
            min(self.hop_numbers) - 1 if self.hop_numbers else 0,
            max(self.hop_numbers) + 1 if self.hop_numbers else 10
        )
    
    def clear_data(self):
        """Clear all data from the graph"""
        self.hop_numbers = []
        self.latencies = []
        self.bar_graph.setOpts(x=[], y=[], width=[])
        self.plot_widget.setYRange(0, 10)
        self.plot_widget.setXRange(0, 100)


class TimeSeriesGraph(QWidget):
    """Time series graph for displaying latency over time"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data
        self.hop_data = {}  # dict of hop -> list of (timestamp, latency) tuples
        self.plot_items = {}  # dict of hop -> plot item
        
        # Color map for hops
        self.colors = [
            (0, 255, 0),      # Green
            (255, 0, 0),      # Red
            (0, 0, 255),      # Blue
            (255, 255, 0),    # Yellow
            (255, 0, 255),    # Magenta
            (0, 255, 255),    # Cyan
            (255, 128, 0),    # Orange
            (128, 0, 255),    # Purple
            (0, 128, 0),      # Dark Green
            (128, 128, 0),    # Olive
        ]
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the time series graph UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Configure plot
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground(None)  # Transparent background
        self.plot_widget.setLabel('left', 'Latency (ms)')
        self.plot_widget.setLabel('bottom', 'Time')
        self.plot_widget.setTitle('Latency Over Time')
        
        # Add grid
        self.plot_widget.showGrid(x=True, y=True)
        
        # Set Y axis range
        self.plot_widget.setYRange(0, 100)  # Initial range
        
        # Setup time axis
        self.plot_widget.setAxisItems({'bottom': pg.DateAxisItem()})
        
        # Add legend
        self.legend = self.plot_widget.addLegend()
        
        layout.addWidget(self.plot_widget)
    
    def update_data(self, hop_history):
        """
        Update the graph with new hop history data
        
        Args:
            hop_history: Dict of hop number -> list of (timestamp, latency) tuples
        """
        if not hop_history:
            return
        
        # Store hop data
        self.hop_data = hop_history
        
        # Track the max latency for Y axis scaling
        max_latency = 0
        
        # Update or create plot for each hop
        for hop_num, history in hop_history.items():
            # Skip if no data
            if not history:
                continue
            
            # Prepare data for plotting
            timestamps = [entry[0] * 1000 for entry in history]  # Convert to milliseconds for pyqtgraph
            latencies = [entry[1] for entry in history]
            
            # Update max latency
            hop_max = max(latencies) if latencies else 0
            max_latency = max(max_latency, hop_max)
            
            # Create or update plot
            if hop_num in self.plot_items:
                # Update existing plot
                self.plot_items[hop_num].setData(timestamps, latencies)
            else:
                # Create new plot with color from palette
                color_idx = (hop_num - 1) % len(self.colors)
                color = self.colors[color_idx]
                
                pen = pg.mkPen(color=color, width=1.5)
                plot_item = self.plot_widget.plot(
                    timestamps, 
                    latencies, 
                    pen=pen, 
                    name=f"Hop {hop_num}"
                )
                self.plot_items[hop_num] = plot_item
        
        # Remove plots for hops that no longer exist
        for hop_num in list(self.plot_items.keys()):
            if hop_num not in hop_history:
                self.plot_widget.removeItem(self.plot_items[hop_num])
                del self.plot_items[hop_num]
        
        # Adjust Y axis range with some padding
        if max_latency > 0:
            self.plot_widget.setYRange(0, max(100, max_latency * 1.1))
        
        # Auto-range X axis to show all data
        self.plot_widget.enableAutoRange(axis='x')
    
    def clear_data(self):
        """Clear all data from the graph"""
        # Remove all plots
        for plot_item in self.plot_items.values():
            self.plot_widget.removeItem(plot_item)
        
        # Clear data storage
        self.hop_data = {}
        self.plot_items = {}
        
        # Reset axes
        self.plot_widget.setYRange(0, 100)
        
        # Reset legend
        self.legend.clear()
        
        # Create a new legend
        self.legend = self.plot_widget.addLegend()


#------------------------------------------------------------------------------
# Main Window
#------------------------------------------------------------------------------

class MainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        
        # Set window properties
        self.setWindowTitle("Network Monitor")
        self.setMinimumSize(900, 600)
        
        # Initialize backend components
        self.network_monitor = NetworkMonitor()
        self.stats_processor = StatisticsProcessor()
        self.session_storage = SessionStorage()
        
        # Current target being monitored
        self.current_target = ""
        
        # Setup UI
        self._setup_ui()
        self._setup_menu()
        self._setup_connections()
        
        # Timer for updating UI
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(500)  # Update every 500ms
        
        # Try to load the last session
        self._load_auto_saved_session()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Control panel at the top
        self.control_panel = ControlPanel(recent_targets=self.session_storage.get_recent_targets())
        main_layout.addWidget(self.control_panel)
        
        # Main content splitter
        content_splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(content_splitter)
        
        # Upper section with data grid and latency bar graph
        upper_widget = QWidget()
        upper_layout = QHBoxLayout(upper_widget)
        upper_layout.setContentsMargins(0, 0, 0, 0)
        
        upper_splitter = QSplitter(Qt.Orientation.Horizontal)
        upper_layout.addWidget(upper_splitter)
        
        # Data grid on the left
        self.data_grid = DataGrid()
        upper_splitter.addWidget(self.data_grid)
        
        # Latency bar graph on the right
        self.latency_graph = LatencyBarGraph()
        upper_splitter.addWidget(self.latency_graph)
        
        # Set split sizes (70% grid, 30% graph)
        upper_splitter.setSizes([int(0.7 * self.width()), int(0.3 * self.width())])
        
        content_splitter.addWidget(upper_widget)
        
        # Time series graph at the bottom
        self.timeseries_graph = TimeSeriesGraph()
        content_splitter.addWidget(self.timeseries_graph)
        
        # Set split sizes (60% upper, 40% lower)
        content_splitter.setSizes([int(0.6 * self.height()), int(0.4 * self.height())])
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def _setup_menu(self):
        """Setup the menu bar"""
        # File menu
        file_menu = self.menuBar().addMenu("&File")
        
        # New target action
        new_action = QAction("&New Target", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._on_new_target)
        file_menu.addAction(new_action)
        
        # Load session action
        load_action = QAction("&Load Session", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_session)
        file_menu.addAction(load_action)
        
        # Save session action
        save_action = QAction("&Save Session", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._on_save_session)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        # Export menu
        export_menu = file_menu.addMenu("&Export")
        
        # Export CSV action
        export_csv_action = QAction("Export as &CSV", self)
        export_csv_action.triggered.connect(self._on_export_csv)
        export_menu.addAction(export_csv_action)
        
        # Export JSON action
        export_json_action = QAction("Export as &JSON", self)
        export_json_action.triggered.connect(self._on_export_json)
        export_menu.addAction(export_json_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = self.menuBar().addMenu("&Tools")
        
        # Clear history action
        clear_action = QAction("&Clear History", self)
        clear_action.triggered.connect(self._on_clear_history)
        tools_menu.addAction(clear_action)
        
        # Help menu
        help_menu = self.menuBar().addMenu("&Help")
        
        # About action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _setup_connections(self):
        """Connect UI signals to slots"""
        # Control panel connections
        self.control_panel.target_entered.connect(self._on_target_entered)
        self.control_panel.interval_changed.connect(self._on_interval_changed)
        self.control_panel.start_clicked.connect(self._on_start_clicked)
        self.control_panel.pause_clicked.connect(self._on_pause_clicked)
        
        # Process results from network monitor
        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._process_results)
        self._process_timer.start(100)  # Check for results every 100ms
    
    def _on_target_entered(self, target):
        """Handle new target entered"""
        self.current_target = target
        self.network_monitor.set_target(target)
        self.statusBar().showMessage(f"Target set to {target}")
    
    def _on_interval_changed(self, interval):
        """Handle interval change"""
        self.network_monitor.set_interval(interval)
        self.statusBar().showMessage(f"Interval set to {interval} seconds")
    
    def _on_start_clicked(self):
        """Handle start button click"""
        if not self.current_target:
            QMessageBox.warning(
                self, 
                "No Target", 
                "Please enter a target hostname or IP address."
            )
            return
        
        self.network_monitor.start_monitoring()
        self.statusBar().showMessage(f"Monitoring {self.current_target}")
    
    def _on_pause_clicked(self):
        """Handle pause button click"""
        self.network_monitor.stop_monitoring()
        self.statusBar().showMessage("Monitoring paused")
    
    def _on_new_target(self):
        """Handle new target menu action"""
        self.network_monitor.stop_monitoring()
        self.current_target = ""
        self.control_panel.clear_target()
        self.data_grid.clear_data()
        self.latency_graph.clear_data()
        self.timeseries_graph.clear_data()
        self.statusBar().showMessage("Ready for new target")
    
    def _on_load_session(self):
        """Handle load session menu action"""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Session",
            "",
            "JSON Files (*.json)"
        )
        
        if filepath:
            self._load_session(filepath)
    
    def _on_save_session(self):
        """Handle save session menu action"""
        if not self.current_target:
            QMessageBox.warning(
                self,
                "No Data",
                "No target is currently being monitored."
            )
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Session",
            f"{self.current_target.replace('.', '_')}.json",
            "JSON Files (*.json)"
        )
        
        if filepath:
            stats = self.stats_processor.get_current_stats(self.current_target)
            saved_path = self.session_storage.save_session(
                self.current_target, stats, filepath
            )
            
            if saved_path:
                self.statusBar().showMessage(f"Session saved to {saved_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Save Error",
                    "Failed to save session."
                )
    
    def _on_export_csv(self):
        """Handle export CSV menu action"""
        if not self.current_target:
            QMessageBox.warning(
                self,
                "No Data",
                "No target is currently being monitored."
            )
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            f"{self.current_target.replace('.', '_')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filepath:
            stats = self.stats_processor.get_current_stats(self.current_target)
            saved_path = self.session_storage.export_csv(
                self.current_target, stats, filepath
            )
            
            if saved_path:
                self.statusBar().showMessage(f"Data exported to {saved_path}")
            else:
                QMessageBox.warning(
                    self,
                    "Export Error",
                    "Failed to export data."
                )
    
    def _on_export_json(self):
        """Handle export JSON menu action"""
        # This is essentially the same as save session
        self._on_save_session()
    
    def _on_clear_history(self):
        """Handle clear history menu action"""
        reply = QMessageBox.question(
            self,
            "Clear History",
            "Are you sure you want to clear all history data?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.stats_processor.clear_history(self.current_target)
            self.data_grid.clear_data()
            self.latency_graph.clear_data()
            self.timeseries_graph.clear_data()
            self.statusBar().showMessage("History cleared")
    
    def _on_about(self):
        """Handle about menu action"""
        QMessageBox.about(
            self,
            "About Network Monitor",
            "Network Monitor v1.0\n\n"
            "A PingPlotter-style network monitoring tool\n"
            "Built with Python, PyQt6, and PyQtGraph"
        )
    
    def _process_results(self):
        """Process results from the network monitor"""
        while not self.network_monitor.results_queue.empty():
            result = self.network_monitor.results_queue.get()
            self.stats_processor.process_result(result)
    
    def _update_ui(self):
        """Update UI with current data"""
        if not self.current_target:
            return
        
        # Get current statistics
        stats = self.stats_processor.get_current_stats(self.current_target)
        if not stats:
            return
        
        # Update data grid
        self.data_grid.update_data(stats)
        
        # Update latency bar graph
        self.latency_graph.update_data(stats)
        
        # Update time series graph
        hop_history = self.stats_processor.get_all_hop_history(self.current_target)
        self.timeseries_graph.update_data(hop_history)
        
        # Auto-save session periodically
        self.session_storage.auto_save_session(self.current_target, stats)
    
    def _load_session(self, filepath):
        """Load a session from file"""
        session_data = self.session_storage.load_session(filepath)
        if not session_data:
            QMessageBox.warning(
                self,
                "Load Error",
                "Failed to load session."
            )
            return
        
        target = session_data.get("target")
        stats = session_data.get("stats", [])
        
        if target and stats:
            # Stop current monitoring
            self.network_monitor.stop_monitoring()
            
            # Set new target
            self.current_target = target
            self.control_panel.set_target(target)
            self.network_monitor.set_target(target)
            
            # Clear existing data
            self.stats_processor.clear_history()
            
            # Simply store the stats directly rather than trying to convert
            self.stats_processor.current_stats[target] = stats
            
            # Update UI
            self._update_ui()
            
            self.statusBar().showMessage(f"Loaded session for {target}")
    
    def _load_auto_saved_session(self):
        """Try to load the auto-saved session"""
        session_data = self.session_storage.load_auto_saved_session()
        if session_data:
            target = session_data.get("target")
            if target:
                self.control_panel.add_recent_target(target)
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Stop monitoring
        self.network_monitor.stop_monitoring()
        
        # Save current session
        if self.current_target:
            stats = self.stats_processor.get_current_stats(self.current_target)
            self.session_storage.auto_save_session(self.current_target, stats)
        
        # Accept the close event
        event.accept()


#------------------------------------------------------------------------------
# Application Entry Point
#------------------------------------------------------------------------------

def main():
    """Application entry point"""
    logger.info("Starting Network Monitoring Tool")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    app.setApplicationName("Network Monitor")
    app.setApplicationDisplayName("Network Monitor")
    
    # Set dark style
    app.setStyleSheet(DARK_STYLE)
    
    # Create and show the main window
    main_window = MainWindow()
    main_window.show()
    
    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()