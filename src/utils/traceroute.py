#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-platform traceroute implementation for network monitoring.
"""

import subprocess
import re
import platform
import socket
import time
from typing import List, Dict, Any, Optional

def perform_traceroute(target: str, max_hops: int = 30, timeout: int = 5) -> List[Dict[str, Any]]:
    """
    Perform a traceroute to the target and return the result.
    
    Args:
        target: The hostname or IP address to trace to
        max_hops: Maximum number of hops to trace
        timeout: Timeout in seconds
    
    Returns:
        List of dictionaries, one per hop, containing:
            - hop: Hop number
            - ip: IP address of the hop
            - hostname: Hostname of the hop (if resolved)
            - rtt: List of round-trip times (ms)
    """
    os_name = platform.system().lower()
    
    if os_name == 'windows':
        return _traceroute_windows(target, max_hops, timeout)
    elif os_name in ('darwin', 'linux'):
        return _traceroute_unix(target, max_hops, timeout, os_name)
    else:
        raise OSError(f"Unsupported operating system: {os_name}")

def _traceroute_windows(target: str, max_hops: int, timeout: int) -> List[Dict[str, Any]]:
    """Perform traceroute on Windows using 'tracert'"""
    # Build command
    cmd = ['tracert', '-d', '-h', str(max_hops), '-w', str(timeout * 1000), target]
    
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, timeout=timeout * max_hops)
        return _parse_windows_traceroute(output)
    except subprocess.TimeoutExpired:
        return [{'hop': 1, 'ip': '*', 'hostname': '', 'rtt': []}]
    except subprocess.CalledProcessError:
        return [{'hop': 1, 'ip': '*', 'hostname': '', 'rtt': []}]

def _traceroute_unix(target: str, max_hops: int, timeout: int, os_name: str) -> List[Dict[str, Any]]:
    """Perform traceroute on Unix-like systems"""
    # Determine the appropriate command
    if os_name == 'darwin':  # macOS
        cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), target]
    else:  # Linux
        cmd = ['traceroute', '-m', str(max_hops), '-w', str(timeout), '-n', target]
    
    try:
        output = subprocess.check_output(cmd, universal_newlines=True, timeout=timeout * max_hops)
        return _parse_unix_traceroute(output, os_name)
    except subprocess.TimeoutExpired:
        return [{'hop': 1, 'ip': '*', 'hostname': '', 'rtt': []}]
    except subprocess.CalledProcessError:
        return [{'hop': 1, 'ip': '*', 'hostname': '', 'rtt': []}]

def _parse_windows_traceroute(output: str) -> List[Dict[str, Any]]:
    """Parse Windows tracert output"""
    hops = []
    
    # Regular expression to match tracert lines
    # Examples:
    # "  1     1 ms     1 ms     1 ms  192.168.1.1"
    # "  2    14 ms    14 ms    14 ms  10.0.0.1"
    # "  3     *        *        *     Request timed out."
    hop_pattern = re.compile(r'^\s*(\d+)(?:\s+(<?\d+\s*ms|\*)\s+(<?\d+\s*ms|\*)\s+(<?\d+\s*ms|\*))\s+([\d\.]+|[a-zA-Z0-9\.\-]+|\*)')
    
    lines = output.splitlines()
    for line in lines:
        match = hop_pattern.match(line)
        if match:
            hop_num = int(match.group(1))
            
            # Extract RTTs
            rtt_values = []
            for i in range(2, 5):
                rtt_str = match.group(i).strip()
                if rtt_str != '*':
                    try:
                        # Extract just the number from strings like "14 ms" or "<1 ms"
                        rtt_value = float(re.search(r'(<?)(\d+)', rtt_str).group(2))
                        rtt_values.append(rtt_value)
                    except (AttributeError, ValueError):
                        pass
            
            # Get IP/hostname
            ip_or_host = match.group(5)
            
            # Check if it's an IP address or hostname
            is_ip = re.match(r'^[\d\.]+$', ip_or_host) is not None
            
            hop_entry = {
                'hop': hop_num,
                'ip': ip_or_host if is_ip or ip_or_host == '*' else '',
                'hostname': '' if is_ip or ip_or_host == '*' else ip_or_host,
                'rtt': rtt_values
            }
            
            hops.append(hop_entry)
    
    return hops

def _parse_unix_traceroute(output: str, os_name: str) -> List[Dict[str, Any]]:
    """Parse Unix traceroute output"""
    hops = []
    
    # Skip the header line
    lines = output.splitlines()[1:]
    
    for line in lines:
        # Match hop number at the start of the line
        hop_match = re.match(r'^\s*(\d+)\s+', line)
        if not hop_match:
            continue
            
        hop_num = int(hop_match.group(1))
        
        # Extract IP addresses or timeouts (*)
        # Example patterns:
        # macOS: "1  192.168.1.1 (192.168.1.1)  1.170 ms  1.018 ms  0.946 ms"
        # Linux: "1  192.168.1.1  0.876 ms  0.875 ms  0.832 ms"
        
        # Find all IP addresses in parentheses (macOS) or without (Linux)
        if os_name == 'darwin':
            ip_pattern = r'\(([^\)]+)\)'
        else:
            ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
            
        ip_match = re.search(ip_pattern, line)
        ip = ip_match.group(1) if ip_match else '*'
        
        # Find hostname (before the IP in parentheses on macOS)
        hostname = ''
        if os_name == 'darwin' and ip_match:
            hostname_pattern = r'(\S+)\s+\(' + re.escape(ip) + r'\)'
            hostname_match = re.search(hostname_pattern, line)
            if hostname_match:
                hostname = hostname_match.group(1)
                # If hostname is an IP address, just leave it as IP
                if re.match(r'^\d+\.\d+\.\d+\.\d+$', hostname):
                    hostname = ''
        
        # Extract RTT values
        rtt_pattern = r'(\d+\.\d+|\d+) ms'
        rtt_values = [float(x) for x in re.findall(rtt_pattern, line)]
        
        hop_entry = {
            'hop': hop_num,
            'ip': ip,
            'hostname': hostname,
            'rtt': rtt_values
        }
        
        hops.append(hop_entry)
    
    return hops