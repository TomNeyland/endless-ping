#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Cross-platform ICMP ping implementation using Python's socket module for network monitoring.
"""

import socket
import struct
import select
import time
import random
import os
import platform
from typing import Dict, Any, Optional, Tuple, List

class ICMPSocket:
    """Helper class for creating and sending ICMP packets."""
    
    ICMP_ECHO_REQUEST = 8  # ICMP type code for echo request
    
    def __init__(self, timeout: int):
        """Initialize ICMP socket."""
        self.timeout = timeout
        if platform.system().lower() == "windows":
            # On Windows, we need to use ICMP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        else:
            # On Unix, we use raw socket (requires root privileges)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            
        self.socket.settimeout(timeout)
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.socket.close()
    
    def checksum(self, data: bytes) -> int:
        """Calculate the checksum of a packet."""
        if len(data) % 2:
            data += b'\x00'
        
        s = sum(struct.unpack('!{}H'.format(len(data) // 2), data))
        s = (s >> 16) + (s & 0xffff)
        s += s >> 16
        return ~s & 0xffff
    
    def create_packet(self, id: int = None) -> bytes:
        """Create an ICMP echo request packet."""
        # If id is not provided, use a random ID
        if id is None:
            id = os.getpid() & 0xFFFF
            
        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        header = struct.pack('!BBHHH', self.ICMP_ECHO_REQUEST, 0, 0, id, 1)
        
        # Create some data for the packet
        data = b'abcdefghijklmnopqrstuvwxyz'
        
        # Calculate the checksum on the data and the header
        checksum = self.checksum(header + data)
        
        # Insert the checksum into the header
        header = struct.pack('!BBHHH', self.ICMP_ECHO_REQUEST, 0, checksum, id, 1)
        
        # Return the complete packet
        return header + data
    
    def send_packet(self, dest_addr: str, packet: bytes) -> Tuple[float, Optional[bytes]]:
        """Send an ICMP packet and get a response."""
        start_time = time.time()
        
        try:
            self.socket.sendto(packet, (dest_addr, 1))
            
            ready = select.select([self.socket], [], [], self.timeout)
            if ready[0]:
                recv_packet, addr = self.socket.recvfrom(1024)
                return time.time() - start_time, recv_packet
            else:
                return time.time() - start_time, None
        except socket.gaierror:
            raise socket.gaierror("Name or service not known")
        except socket.error as e:
            if "No route to host" in str(e):
                raise socket.error("No route to host")
            elif "Permission denied" in str(e):
                raise PermissionError("Root privileges required for raw socket on Unix systems")
            else:
                raise e


def ping_host(host: str, timeout: int = 1, count: int = 1) -> Dict[str, Any]:
    """
    Ping a host using Python's socket module and return the result.
    
    Args:
        host: The hostname or IP address to ping
        timeout: Timeout in seconds
        count: Number of pings to send
    
    Returns:
        Dictionary with ping results:
            - success: Whether the ping was successful
            - latency: Round-trip time in milliseconds (if successful)
            - error: Error message (if not successful)
            - error_type: Type of error (e.g., "timeout", "no_route", "unknown")
    """
    # Default result
    result = {
        'success': False,
        'latency': 0,
        'error': None,
        'error_type': None
    }
    
    try:
        # Resolve hostname to IP address
        try:
            dest_addr = socket.gethostbyname(host)
        except socket.gaierror:
            result['error'] = "Name or service not known"
            result['error_type'] = "unknown"
            return result
        
        # Make sure we have permissions to create raw sockets
        if platform.system().lower() != "windows" and os.geteuid() != 0:
            result['error'] = "Root privileges required for raw socket on Unix systems"
            result['error_type'] = "permission"
            return result
            
        # Create socket and ping
        try:
            with ICMPSocket(timeout) as icmp:
                packet = icmp.create_packet()
                
                latencies = []
                for i in range(count):
                    elapsed_time, recv_packet = icmp.send_packet(dest_addr, packet)
                    
                    if recv_packet:
                        latencies.append(elapsed_time * 1000)  # Convert to ms
                    
                    # If we're sending multiple pings, add a small delay between them
                    if i < count - 1:
                        time.sleep(0.1)
                
                if latencies:
                    # Calculate average latency
                    avg_latency = sum(latencies) / len(latencies)
                    result['success'] = True
                    result['latency'] = avg_latency
                else:
                    result['error'] = "Request timed out"
                    result['error_type'] = "timeout"
        
        except PermissionError as e:
            result['error'] = str(e)
            result['error_type'] = "permission"
        
        except socket.error as e:
            result['error'] = str(e)
            
            if "No route to host" in str(e):
                result['error_type'] = "no_route"
            elif "Permission denied" in str(e):
                result['error_type'] = "permission"
            else:
                result['error_type'] = "unknown"
                
    except Exception as e:
        result['error'] = str(e)
        
        if "No route to host" in str(e):
            result['error_type'] = "no_route"
        elif "timed out" in str(e).lower():
            result['error_type'] = "timeout"
        else:
            result['error_type'] = "unknown"
    
    return result


# Example usage
if __name__ == "__main__":
    # Try to ping Google's DNS server
    result = ping_host("8.8.8.8", timeout=2, count=3)
    print(f"Ping result: {result}")
    
    # Try to ping a non-existent host
    result = ping_host("non.existent.host", timeout=2)
    print(f"Failed ping result: {result}")