#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Session storage and management for the network monitoring application.
"""

import json
import csv
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

class SessionManager:
    """Manages saving and loading monitoring sessions"""
    
    def __init__(self, base_dir: Optional[str] = None):
        """
        Initialize the session manager
        
        Args:
            base_dir: Base directory for session storage. Defaults to user home directory.
        """
        if base_dir is None:
            # Use user's home directory
            home = os.path.expanduser("~")
            base_dir = os.path.join(home, ".network_monitor")
        
        self.base_dir = base_dir
        self.sessions_dir = os.path.join(base_dir, "sessions")
        
        # Create directories if they don't exist
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def save_session(self, target: str, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        Save a monitoring session to a file.
        
        Args:
            target: Target host that was monitored
            data: Session data to save
            filename: Optional filename for the session. If None, one is generated.
        
        Returns:
            The path to the saved session file
        """
        if filename is None:
            # Generate filename based on target and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_target = target.replace(".", "_").replace(":", "_")
            filename = f"{safe_target}_{timestamp}.json"
        
        # Ensure extension
        if not filename.endswith(".json"):
            filename += ".json"
        
        file_path = os.path.join(self.sessions_dir, filename)
        
        # Prepare data for serialization
        session_data = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        # Save to file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
        
        return file_path
    
    def load_session(self, file_path: str) -> Dict[str, Any]:
        """
        Load a monitoring session from a file.
        
        Args:
            file_path: Path to the session file
        
        Returns:
            The loaded session data
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        return session_data
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.
        
        Returns:
            List of session information dictionaries
        """
        sessions = []
        
        for filename in os.listdir(self.sessions_dir):
            if filename.endswith(".json"):
                file_path = os.path.join(self.sessions_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    sessions.append({
                        "filename": filename,
                        "path": file_path,
                        "target": data.get("target", "Unknown"),
                        "timestamp": data.get("timestamp", "Unknown")
                    })
                except Exception as e:
                    # Skip invalid session files
                    continue
        
        # Sort by timestamp (most recent first)
        return sorted(sessions, key=lambda x: x["timestamp"], reverse=True)
    
    def export_csv(self, session_data: Dict[str, Any], file_path: str) -> None:
        """
        Export session data to CSV format.
        
        Args:
            session_data: Session data to export
            file_path: Path to the CSV file to create
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Extract the hop data
        data = session_data.get("data", {})
        history = data.get("history", {})
        
        # Prepare data for CSV
        rows = []
        
        # Create header row
        header = ["timestamp"]
        for hop in sorted(history.keys()):
            header.append(f"hop_{hop}_latency")
            header.append(f"hop_{hop}_success")
        
        rows.append(header)
        
        # Find all unique timestamps across all hops
        all_timestamps = set()
        for hop_data in history.values():
            for point in hop_data:
                all_timestamps.add(point["timestamp"])
        
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps)
        
        # Create a row for each timestamp
        for timestamp in sorted_timestamps:
            row = [timestamp]
            
            # Add data for each hop
            for hop in sorted(history.keys()):
                # Find the data point for this timestamp
                hop_data = history[hop]
                point = next((p for p in hop_data if p["timestamp"] == timestamp), None)
                
                if point:
                    row.append(point.get("latency", ""))
                    row.append("1" if point.get("success", False) else "0")
                else:
                    row.append("")
                    row.append("")
            
            rows.append(row)
        
        # Write to CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(rows)
    
    def export_json(self, session_data: Dict[str, Any], file_path: str) -> None:
        """
        Export session data to JSON format.
        
        Args:
            session_data: Session data to export
            file_path: Path to the JSON file to create
        """
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
    
    def get_auto_save_path(self) -> str:
        """
        Get the path for auto-saving the current session.
        
        Returns:
            Path to the auto-save file
        """
        return os.path.join(self.base_dir, "autosave.json")
    
    def auto_save(self, target: str, data: Dict[str, Any]) -> None:
        """
        Auto-save the current session.
        
        Args:
            target: Target host being monitored
            data: Current session data
        """
        file_path = self.get_auto_save_path()
        
        session_data = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2)
    
    def load_auto_save(self) -> Optional[Dict[str, Any]]:
        """
        Load the auto-saved session if available.
        
        Returns:
            The auto-saved session data if available, None otherwise
        """
        file_path = self.get_auto_save_path()
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                return None
        
        return None