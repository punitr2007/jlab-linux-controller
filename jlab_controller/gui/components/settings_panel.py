"""Hardware Tweaks & Features Panel."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)
from ...core.device import JLabDevice

class SettingsPanel(QFrame):
    wear_detection_toggled = pyqtSignal(bool)
    low_latency_toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Hardware Tweaks & Controls")
        title.setProperty("class", "title")
        subtitle = QLabel("Configure smart sensors and playback preferences")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # In-Ear Wear Detection / Auto Pause
        wear_box = QHBoxLayout()
        wear_info = QVBoxLayout()
        wear_title = QLabel("Auto-Pause / Wear Detection")
        wear_title.setStyleSheet("font-weight: 600; color: #FFFFFF;")
        wear_desc = QLabel("Automatically pauses audio when you take the headphones off")
        wear_desc.setProperty("class", "subtitle")
        wear_info.addWidget(wear_title)
        wear_info.addWidget(wear_desc)

        self.wear_cb = QCheckBox()
        self.wear_cb.toggled.connect(self.wear_detection_toggled.emit)
        wear_box.addLayout(wear_info, stretch=1)
        wear_box.addWidget(self.wear_cb)
        layout.addLayout(wear_box)

        # Low Latency Mode / Movie Mode
        latency_box = QHBoxLayout()
        latency_info = QVBoxLayout()
        latency_title = QLabel("Movie / Low-Latency Mode")
        latency_title.setStyleSheet("font-weight: 600; color: #FFFFFF;")
        latency_desc = QLabel("Reduces audio delay for watching videos and gaming")
        latency_desc.setProperty("class", "subtitle")
        latency_info.addWidget(latency_title)
        latency_info.addWidget(latency_desc)

        self.latency_cb = QCheckBox()
        self.latency_cb.toggled.connect(self.low_latency_toggled.emit)
        latency_box.addLayout(latency_info, stretch=1)
        latency_box.addWidget(self.latency_cb)
        layout.addLayout(latency_box)

    def update_device(self, device: JLabDevice) -> None:
        self.wear_cb.blockSignals(True)
        self.wear_cb.setChecked(device.wear_detection)
        self.wear_cb.blockSignals(False)

        self.latency_cb.blockSignals(True)
        self.latency_cb.setChecked(device.low_latency_mode)
        self.latency_cb.blockSignals(False)
