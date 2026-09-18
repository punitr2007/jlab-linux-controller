#!/usr/bin/env python3
"""JLab Linux Controller - Main GUI Application Entry Point."""

import logging
import sys
from PyQt6.QtWidgets import QApplication
from jlab_controller.gui.main_window import MainWindow

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    )
    app = QApplication(sys.argv)
    app.setApplicationName("JLab Controller")
    app.setApplicationDisplayName("JLab Controller")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
