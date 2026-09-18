"""Device Status & Connection Header Component."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from ...core.device import JLabDevice

class HeaderComponent(QFrame):
    refresh_requested = pyqtSignal()
    reconnect_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Left: Device Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        self.name_label = QLabel("JLab Headphone")
        self.name_label.setProperty("class", "title")

        self.addr_label = QLabel("Disconnected")
        self.addr_label.setProperty("class", "subtitle")

        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.addr_label)
        layout.addLayout(info_layout, stretch=1)

        # Middle: Battery Badge & Connection Badge
        badge_layout = QHBoxLayout()
        badge_layout.setSpacing(8)

        self.conn_badge = QLabel("Offline")
        self.conn_badge.setProperty("class", "badge")
        self.conn_badge.setStyleSheet("color: #EF4444; border-color: #EF444433;")

        self.battery_badge = QLabel("🔋 --%")
        self.battery_badge.setProperty("class", "badge")

        badge_layout.addWidget(self.conn_badge)
        badge_layout.addWidget(self.battery_badge)
        layout.addLayout(badge_layout)

        # Right: Reconnect & Refresh Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.refresh_btn = QPushButton("↻ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_requested.emit)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setProperty("class", "primary")
        self.connect_btn.clicked.connect(self.reconnect_requested.emit)

        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.connect_btn)
        layout.addLayout(btn_layout)

    def update_device(self, device: JLabDevice) -> None:
        self.name_label.setText(device.name)
        self.addr_label.setText(f"MAC: {device.address}")

        if device.is_connected:
            self.conn_badge.setText("● Connected")
            self.conn_badge.setStyleSheet("color: #10B981; border-color: #10B98133;")
            self.connect_btn.setText("Disconnect")
            self.battery_badge.setText(f"🔋 {device.battery_level}%{' ⚡' if device.is_charging else ''}")
        else:
            self.conn_badge.setText("○ Disconnected")
            self.conn_badge.setStyleSheet("color: #EF4444; border-color: #EF444433;")
            self.connect_btn.setText("Connect")
            self.battery_badge.setText("🔋 --%")
