#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ultimate Endless Ping Network Monitoring Tool
A PingPlotter-style desktop application to monitor and visualize network latency.
"""

import sys
import logging
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Create logger for the main module
logger = logging.getLogger('endless_ping')
logger.info("Starting Endless Ping application")

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application-wide properties
    app.setApplicationName("Endless Ping")
    app.setOrganizationName("NetworkTools")
    
    # Apply dark style
    try:
        import qdarkstyle
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    except ImportError:
        print("QDarkStyle not found. Using default style.")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    # Start the event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()