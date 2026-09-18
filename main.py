#!/usr/bin/env python3
"""JLab Linux Controller - Main GUI Application Entry Point."""

import fcntl
import logging
import os
import sys

from PyQt6.QtWidgets import QApplication, QMessageBox
from jlab_controller.gui.main_window import MainWindow

_LOCK_FILE = "/tmp/jlab-controller.lock"
_lock_fh = None  # keep reference so lock is held until process exits


def _acquire_single_instance_lock() -> bool:
    """Returns True if this is the only running instance, False otherwise."""
    global _lock_fh
    _lock_fh = open(_LOCK_FILE, "w")
    try:
        fcntl.flock(_lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        _lock_fh.write(str(os.getpid()))
        _lock_fh.flush()
        return True
    except OSError:
        _lock_fh.close()
        _lock_fh = None
        return False


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
    )

    # Single-instance guard — prevents two copies fighting over the RFCOMM channel
    if not _acquire_single_instance_lock():
        # Need a minimal QApplication to show the dialog
        app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setWindowTitle("JLab Controller")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText("JLab Controller is already running.")
        msg.setInformativeText(
            "Only one instance can connect to the headphone at a time.\n"
            "Check your system tray for the existing window."
        )
        msg.exec()
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setApplicationName("JLab Controller")
    app.setApplicationDisplayName("JLab Controller")
    app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
