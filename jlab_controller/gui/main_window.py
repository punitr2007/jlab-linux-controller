"""Main Application Window with Thread-Safe Qt Signals and System Tray Integration."""

import logging
import os
import threading
from PyQt6.QtCore import QObject, Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QMenu,
    QScrollArea,
    QSystemTrayIcon,
    QVBoxLayout,
    QWidget,
)
from ..bluetooth.discovery import BluetoothScanner
from ..constants import AncMode, EqPreset
from ..core.device import JLabDevice
from .components.anc_panel import AncPanel
from .components.eq_panel import EqPanel
from .components.header import HeaderComponent
from .components.settings_panel import SettingsPanel
from .components.tools_panel import ToolsPanel
from .style import DARK_THEME

logger = logging.getLogger(__name__)

class DeviceSignalBridge(QObject):
    """Bridge to safely marshal device events from background threads to Qt main thread."""
    updated = pyqtSignal()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JLab Headphone Controller")
        self.setMinimumSize(700, 780)
        self.setStyleSheet(DARK_THEME)

        self.bridge = DeviceSignalBridge()
        self.bridge.updated.connect(self._on_bridge_updated)

        icon_path = os.path.join(os.path.dirname(__file__), "assets", "icon.png")
        if os.path.exists(icon_path):
            self.app_icon = QIcon(icon_path)
            self.setWindowIcon(self.app_icon)
        else:
            self.app_icon = self.style().standardIcon(QApplication.style().StandardPixmap.SP_MediaVolume)

        self.device: JLabDevice | None = None

        self._init_ui()
        self._init_tray()
        self._auto_discover_and_connect()

    def _init_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 1. Header
        self.header = HeaderComponent()
        self.header.refresh_requested.connect(self._on_refresh)
        self.header.reconnect_requested.connect(self._on_reconnect)
        layout.addWidget(self.header)

        # 2. ANC Panel
        self.anc_panel = AncPanel()
        self.anc_panel.anc_mode_changed.connect(self._on_anc_mode_changed)
        self.anc_panel.awareness_changed.connect(self._on_awareness_changed)
        layout.addWidget(self.anc_panel)

        # 3. EQ Panel
        self.eq_panel = EqPanel()
        self.eq_panel.preset_selected.connect(self._on_eq_preset_selected)
        self.eq_panel.custom_gains_changed.connect(self._on_custom_gains_changed)
        layout.addWidget(self.eq_panel)

        # 4. Settings Panel
        self.settings_panel = SettingsPanel()
        self.settings_panel.wear_detection_toggled.connect(self._on_wear_detection_toggled)
        self.settings_panel.low_latency_toggled.connect(self._on_low_latency_toggled)
        layout.addWidget(self.settings_panel)

        # 5. Tools Panel
        self.tools_panel = ToolsPanel()
        layout.addWidget(self.tools_panel)

        layout.addStretch()
        scroll.setWidget(container)

    def _init_tray(self) -> None:
        """Initializes Linux system tray icon."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.app_icon)
        
        tray_menu = QMenu()
        show_action = QAction("Open JLab Controller", self)
        show_action.triggered.connect(self.showNormal)
        tray_menu.addAction(show_action)

        tray_menu.addSeparator()
        anc_on_action = QAction("Set ANC: ON", self)
        anc_on_action.triggered.connect(lambda: self._on_anc_mode_changed(AncMode.ANC_ON))
        tray_menu.addAction(anc_on_action)

        be_aware_action = QAction("Set ANC: Be Aware", self)
        be_aware_action.triggered.connect(lambda: self._on_anc_mode_changed(AncMode.BE_AWARE))
        tray_menu.addAction(be_aware_action)

        anc_off_action = QAction("Set ANC: OFF", self)
        anc_off_action.triggered.connect(lambda: self._on_anc_mode_changed(AncMode.OFF))
        tray_menu.addAction(anc_off_action)

        tray_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(QApplication.quit)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def _auto_discover_and_connect(self) -> None:
        devices = BluetoothScanner.get_paired_jlab_devices()
        if devices:
            target = devices[0]
            logger.info(f"Auto-selected device: {target.name} ({target.address})")
            self.device = JLabDevice(target.address, target.name)
            self.device.is_connected = target.connected
            if target.battery is not None:
                self.device.battery_level = target.battery

            self.device.add_update_listener(lambda _: self.bridge.updated.emit())
            self._render_device()

            # Connect asynchronously in background thread so GUI never blocks
            threading.Thread(target=self.device.connect, daemon=True, name="JLab-Connect").start()

    @pyqtSlot()
    def _on_bridge_updated(self) -> None:
        self._render_device()

    def _render_device(self) -> None:
        if not self.device:
            return
        self.header.update_device(self.device)
        self.anc_panel.update_device(self.device)
        self.eq_panel.update_device(self.device)
        self.settings_panel.update_device(self.device)

    def _on_refresh(self) -> None:
        if self.device:
            threading.Thread(target=self.device.refresh_status, daemon=True).start()

    def _on_reconnect(self) -> None:
        if self.device:
            if self.device.is_connected:
                threading.Thread(target=self.device.disconnect, daemon=True).start()
            else:
                threading.Thread(target=self.device.connect, daemon=True).start()

    def _on_anc_mode_changed(self, mode: AncMode) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_anc_mode(mode), daemon=True).start()

    def _on_awareness_changed(self, level: int) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_awareness_level(level), daemon=True).start()

    def _on_eq_preset_selected(self, preset: int) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_eq_preset(preset), daemon=True).start()

    def _on_custom_gains_changed(self, gains: list) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_custom_eq_gains(gains), daemon=True).start()

    def _on_wear_detection_toggled(self, enabled: bool) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_wear_detection(enabled), daemon=True).start()

    def _on_low_latency_toggled(self, enabled: bool) -> None:
        if self.device:
            threading.Thread(target=lambda: self.device.set_low_latency_mode(enabled), daemon=True).start()

    def closeEvent(self, event) -> None:
        if self.tray_icon.isVisible():
            self.hide()
            event.ignore()
        else:
            if self.device:
                self.device.disconnect()
            event.accept()
