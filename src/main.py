#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ultimate Python Network Monitoring Tool
A PingPlotter-style desktop application to monitor and visualize network latency.
"""

import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import MainWindow

def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application-wide properties
    app.setApplicationName("Python Network Monitor")
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