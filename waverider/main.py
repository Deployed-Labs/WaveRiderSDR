#!/usr/bin/env python3
"""
Main entry point for WaveRiderSDR application
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from waverider.ui.main_window import MainWindow


def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application metadata
    app.setApplicationName("WaveRiderSDR")
    app.setOrganizationName("WaveRiderSDR")
    app.setApplicationVersion("0.1.0")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
