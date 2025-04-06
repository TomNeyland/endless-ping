#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-platform ICMP ping implementation for network monitoring.
"""

import subprocess
import platform
import re
import socket
import time
import os
from typing import Dict, Any, Optional, Tuple, List

def ping_host(host: str, timeout: int = 1, count: int = 1) -> Dict[str, Any]:
    """
    Ping a host and return the result.
    
    Args:
        host: The hostname or IP address to ping
        timeout: Timeout in seconds
        count: Number of pings to send
    
    Returns:
        Dictionary with ping results:
            - success: Whether the ping was successful
            - latency: Round-trip time in milliseconds (if successful)
            - error: Error message (if not successful)
    """
    # Default result
    result = {
        'success': False,
        'latency': 0,
        'error': None
    }
    
    try:
        # Determine the platform-specific ping command
        os_name = platform.system().lower()
        
        if os_name == 'windows':
            output = _ping_windows(host, timeout, count)
        elif os_name in ('darwin', 'linux'):
            output = _ping_unix(host, timeout, count)
        else:
            raise OSError(f"Unsupported operating system: {os_name}")
        
        # Parse the output
        latency = _parse_ping_output(output, os_name)
        
        if latency is not None:
            result['success'] = True
            result['latency'] = latency
        else:
            result['error'] = "Could not parse ping output or ping timed out"
            
    except Exception as e:
        result['error'] = str(e)
    
    return result

def _ping_windows(host: str, timeout: int, count: int) -> str:
    """Run ping command on Windows"""
    cmd = ['ping', '-n', str(count), '-w', str(timeout * 1000), host]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, timeout=timeout+1)
        return output
    except subprocess.TimeoutExpired:
        return "Request timed out."
    except subprocess.CalledProcessError:
        return "Ping request could not find host."

def _ping_unix(host: str, timeout: int, count: int) -> str:
    """Run ping command on Unix-like systems (Linux/macOS)"""
    cmd = ['ping', '-c', str(count), host]
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, timeout=timeout+1)
        return output
    except subprocess.TimeoutExpired:
        return "Request timed out."
    except subprocess.CalledProcessError:
        return "Ping request could not find host."

def _parse_ping_output(output: str, os_name: str) -> Optional[float]:
    """
    Parse the ping command output to extract latency.
    
    Args:
        output: Output from the ping command
        os_name: Operating system name
    
    Returns:
        Latency in milliseconds or None if parsing failed
    """
    if "Request timed out" in output or "100% packet loss" in output:
        return None
    
    # Windows format: "Reply from 8.8.8.8: bytes=32 time=44ms TTL=113"
    if os_name == 'windows':
        match = re.search(r'time=(\d+)ms', output)
        if match:
            return float(match.group(1))
    
    # Unix format: "64 bytes from 8.8.8.8: icmp_seq=1 ttl=118 time=11.994 ms"
    else:
        match = re.search(r'time=(\d+\.\d+|\d+) ms', output)
        if match:
            return float(match.group(1))
    
    return None