#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Statistical calculations for network monitoring data.
"""

import statistics
from typing import List, Dict, Any, Union

def calculate_statistics(data_points: List[Dict[str, Any]]) -> Dict[str, Union[float, int]]:
    """
    Calculate network statistics from a series of data points.
    
    Args:
        data_points: List of data point dictionaries with keys:
            - timestamp: Datetime of the measurement
            - latency: Latency in ms (or None for timeouts)
            - success: Boolean indicating if the ping was successful
    
    Returns:
        Dictionary of statistics:
            - avg: Average latency
            - loss: Packet loss percentage
            - jitter: Jitter (variation in latency)
    """
    # Filter out None latencies (timeouts)
    latencies = [point['latency'] for point in data_points if point['success'] and point['latency'] is not None]
    
    # Calculate packet loss
    total_points = len(data_points)
    successful_points = len(latencies)
    loss_percentage = 0 if total_points == 0 else (1 - (successful_points / total_points)) * 100
    
    # Calculate average latency
    avg_latency = 0
    if successful_points > 0:
        avg_latency = sum(latencies) / successful_points
    
    # Calculate jitter (standard deviation of latencies)
    jitter = 0
    if successful_points > 1:
        try:
            jitter = statistics.stdev(latencies)
        except:
            # Handle potential errors in stdev calculation
            jitter = 0
    
    return {
        'avg': avg_latency,
        'loss': loss_percentage,
        'jitter': jitter
    }