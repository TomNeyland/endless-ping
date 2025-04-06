#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DNS and IP lookup utilities for network monitoring.
"""

import socket
import ipaddress
from typing import Optional, Tuple, Dict, Any
import re

def is_valid_ip(ip: str) -> bool:
    """
    Check if the given string is a valid IP address.
    
    Args:
        ip: String to check
    
    Returns:
        True if valid IP address, False otherwise
    """
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def is_valid_hostname(hostname: str) -> bool:
    """
    Check if the given string is a valid hostname.
    
    Args:
        hostname: String to check
    
    Returns:
        True if valid hostname, False otherwise
    """
    # Simple hostname validation pattern
    pattern = r'^([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])(\.([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]{0,61}[a-zA-Z0-9]))*$'
    return bool(re.match(pattern, hostname))

def resolve_hostname(hostname: str) -> str:
    """
    Resolve a hostname to an IP address.
    
    Args:
        hostname: Hostname to resolve
    
    Returns:
        IP address as string, or empty string if resolution fails
    """
    try:
        # Check if input is already an IP address
        if is_valid_ip(hostname):
            return hostname
            
        # Try to resolve hostname
        ip = socket.gethostbyname(hostname)
        return ip
    except (socket.gaierror, socket.herror):
        return ""

def resolve_ip(ip: str) -> str:
    """
    Resolve an IP address to a hostname.
    
    Args:
        ip: IP address to resolve
    
    Returns:
        Hostname as string, or empty string if resolution fails
    """
    try:
        # Check if input is already a hostname
        if not is_valid_ip(ip):
            return ip
            
        # Try to resolve IP
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname
    except (socket.herror, socket.gaierror):
        return ""

def get_host_info(host: str) -> Dict[str, Any]:
    """
    Get comprehensive information about a host.
    
    Args:
        host: Hostname or IP address
    
    Returns:
        Dictionary containing host information:
            - input: Original input string
            - ip: Resolved IP address
            - hostname: Resolved hostname
            - is_valid: Whether the input is valid
    """
    result = {
        'input': host,
        'ip': '',
        'hostname': '',
        'is_valid': False
    }
    
    # Check if input is empty
    if not host:
        return result
    
    # Check if input is an IP address
    if is_valid_ip(host):
        result['ip'] = host
        result['is_valid'] = True
        
        # Try to resolve hostname
        hostname = resolve_ip(host)
        if hostname:
            result['hostname'] = hostname
    
    # Check if input is a hostname
    elif is_valid_hostname(host):
        result['hostname'] = host
        result['is_valid'] = True
        
        # Try to resolve IP
        ip = resolve_hostname(host)
        if ip:
            result['ip'] = ip
    
    return result