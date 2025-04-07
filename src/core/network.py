#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Network monitoring functionality including ping and traceroute operations.
"""

import time
import threading
import queue
from collections import deque
from datetime import datetime

from utils.ping import ping_host
from utils.traceroute import perform_traceroute
from utils.ip_lookup import resolve_hostname
from core.statistics import calculate_statistics
from concurrent.futures import ThreadPoolExecutor

class EndlessPingMonitor:
    """Manages network monitoring operations and data collection"""
    
    def __init__(self):
        self.target = ""
        self.interval = 2.5  # Default interval in seconds
        self.running = False
        self.thread = None
        self.stop_event = threading.Event()
        
        # Data structures to store monitoring results
        self.current_hops = []  # Current hop data
        self.history = {}  # Historical data by hop
        # Increase max_points to store 24 hours of data at 1-second intervals (86400 seconds per day)
        self.history_max_points = 86400  # Store up to 24 hours of data at 1s intervals
        
        # Queue for async operations
        self.data_queue = queue.Queue()
    
    def set_target(self, target):
        """Set the target host to monitor"""
        self.target = target
        # Reset data when target changes
        self.current_hops = []
        self.history = {}
    
    def set_interval(self, interval_seconds):
        """Set the monitoring interval in seconds"""
        self.interval = interval_seconds
    
    def start(self):
        """Start the monitoring thread"""
        if not self.running and self.target:
            self.stop_event.clear()
            self.running = True
            self.thread = threading.Thread(target=self._monitoring_loop)
            self.thread.daemon = True
            self.thread.start()
    
    def pause(self):
        """Pause the monitoring thread"""
        self.running = False
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def _monitoring_loop(self):
        """Main monitoring loop that runs in a separate thread"""
        # First, perform traceroute to get the path
        self._perform_initial_traceroute()
        
        # Then start continuous ping monitoring
        while not self.stop_event.is_set() and self.running:
            start_time = time.time()
            
            # Perform ping on each hop
            self._ping_all_hops()
            
            # Calculate statistics
            self._update_statistics()
            
            # Wait for the next interval
            elapsed = time.time() - start_time
            sleep_time = max(0, self.interval - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)
    
    def _perform_initial_traceroute(self):
        """Perform initial traceroute to discover the path"""
        if not self.target:
            return
            
        # Perform traceroute
        traceroute_result = perform_traceroute(self.target)
        
        # Initialize hops list
        self.current_hops = []
        for hop_num, hop_data in enumerate(traceroute_result, 1):
            if hop_data.get('ip') == '*':  # Skip timeouts
                continue
                
            # Resolve hostname if needed
            if not hop_data.get('hostname'):
                try:
                    hostname = resolve_hostname(hop_data.get('ip'))
                    hop_data['hostname'] = hostname
                except:
                    hop_data['hostname'] = ''
            
            # Create hop entry
            hop_entry = {
                'hop': hop_num,
                'ip': hop_data.get('ip', ''),
                'hostname': hop_data.get('hostname', ''),
                'count': 0,
                'current': 0,
                'min': float('inf'),
                'max': 0,
                'avg': 0,
                'loss': 0,
                'jitter': 0,
                'error_type': None,
                'timestamps': []
            }
            
            self.current_hops.append(hop_entry)
            self.history[hop_num] = deque(maxlen=self.history_max_points)

    def _ping_all_hops(self):
        """Ping all hops in the current path in parallel"""
        timestamp = datetime.now()
        
        def ping_and_process(hop):
            # Ping the hop
            result = ping_host(hop['ip'])
            
            # Update hop data
            hop['count'] += 1
            
            if result['success']:
                latency = result['latency']
                hop['current'] = latency
                hop['min'] = min(hop['min'], latency)
                hop['max'] = max(hop['max'], latency)
                hop['error_type'] = None
                
                # Add to history
                self.history[hop['hop']].append({
                    'timestamp': timestamp,
                    'latency': latency,
                    'success': True,
                    'error_type': None
                })
            else:
                # Record error
                hop['current'] = 0  # No latency for errors
                hop['error_type'] = result.get('error_type', 'unknown')
                
                # Add to history
                self.history[hop['hop']].append({
                    'timestamp': timestamp,
                    'latency': None,
                    'success': False,
                    'error_type': result.get('error_type', 'unknown')
                })
            
            return hop
        
        # Use a thread pool to ping all hops in parallel
        with ThreadPoolExecutor(max_workers=min(32, len(self.current_hops))) as executor:
            # Submit all ping tasks and process results as they complete
            future_to_hop = {executor.submit(ping_and_process, hop): hop for hop in self.current_hops}
            
            # Wait for all tasks to complete (optional, depending on your needs)
            for future in future_to_hop:
                try:
                    future.result()
                except Exception as exc:
                    print(f'Hop generated an exception: {exc}')
    
    def _update_statistics(self):
        """Update statistics for all hops"""
        for hop in self.current_hops:
            hop_history = self.history.get(hop['hop'], [])
            if hop_history:
                stats = calculate_statistics(hop_history)
                hop['avg'] = stats['avg']
                hop['loss'] = stats['loss']
                hop['jitter'] = stats['jitter']
    
    def get_current_data(self):
        """Get the current monitoring data"""
        return self.current_hops.copy()
    
    def get_history_data(self, hop_num=None):
        """Get historical data for visualization"""
        if hop_num is not None and hop_num in self.history:
            return list(self.history[hop_num])
        return {hop: list(data) for hop, data in self.history.items()}