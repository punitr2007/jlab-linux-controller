from __future__ import annotations

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSlider,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from . import protocol
from .device import JLabDevice

DEFAULT_MAC = "DC:A8:00:60:77:F7"  # your JBuds Lux ANC, from prior pairing


class EQBandSlider(QVBoxLayout):
    def __init__(self, freq_hz: int):
        super().__init__()
        self.freq_hz = freq_hz
        label_text = f"{freq_hz}" if freq_hz < 1000 else f"{freq_hz // 1000}k"
        self.top_label = QLabel("0.0 dB")
        self.top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slider = QSlider(Qt.Orientation.Vertical)
        self.slider.setMinimum(protocol.EQ_GAIN_MIN_DB * 2)
        self.slider.setMaximum(protocol.EQ_GAIN_MAX_DB * 2)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self._on_change)
        self.bottom_label = QLabel(f"{label_text} Hz")
        self.bottom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.addWidget(self.top_label)
        self.addWidget(self.slider, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.addWidget(self.bottom_label)

    def _on_change(self, raw_value: int) -> None:
        self.top_label.setText(f"{raw_value / 2:+.1f} dB")

    def value_db(self) -> float:
        return self.slider.value() / 2


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JLab Linux Controller")
        self.setMinimumSize(720, 480)

        self.device: JLabDevice | None = None

        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)

        layout.addLayout(self._build_connection_bar())
        layout.addWidget(self._build_anc_group())
        layout.addWidget(self._build_eq_group())

        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Not connected")

    # --- UI construction --------------------------------------------------

    def _build_connection_bar(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel("Device MAC:"))
        self.mac_input = QLineEdit(DEFAULT_MAC)
        row.addWidget(self.mac_input)
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.clicked.connect(self._toggle_connection)
        row.addWidget(self.connect_btn)
        self.battery_label = QLabel("Battery: —")
        row.addWidget(self.battery_label)
        row.addStretch()
        return row

    def _build_anc_group(self) -> QGroupBox:
        group = QGroupBox("Noise Control")
        row = QHBoxLayout(group)
        self.anc_combo = QComboBox()
        self.anc_combo.addItems(["ANC Off", "ANC On"])
        self.anc_combo.currentIndexChanged.connect(self._on_anc_changed)
        row.addWidget(self.anc_combo)
        row.addStretch()
        return group

    def _build_eq_group(self) -> QGroupBox:
        group = QGroupBox("10-Band Equalizer")
        outer = QVBoxLayout(group)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.eq_preset_combo = QComboBox()
        self.eq_preset_combo.addItems(["Signature", "Balanced", "Bass Boost", "Custom"])
        self.eq_preset_combo.currentIndexChanged.connect(self._on_eq_preset_changed)
        preset_row.addWidget(self.eq_preset_combo)
        preset_row.addStretch()
        apply_btn = QPushButton("Apply Custom Bands")
        apply_btn.clicked.connect(self._on_apply_custom_eq)
        preset_row.addWidget(apply_btn)
        outer.addLayout(preset_row)

        sliders_row = QHBoxLayout()
        self.eq_sliders: list[EQBandSlider] = []
        for freq in protocol.EQ_BANDS_HZ:
            band = EQBandSlider(freq)
            self.eq_sliders.append(band)
            sliders_row.addLayout(band)
        outer.addLayout(sliders_row)

        return group

    # --- Actions ------------------------------------------------------------

    def _toggle_connection(self) -> None:
        if self.device and self.device.is_connected:
            self.device.disconnect_device()
            return
        mac = self.mac_input.text().strip()
        self.device = JLabDevice(mac)
        self.device.connected.connect(self._on_connected)
        self.device.disconnected.connect(self._on_disconnected)
        self.device.battery_updated.connect(self._on_battery_updated)
        self.device.error.connect(self._on_error)
        self.statusBar().showMessage(f"Connecting to {mac}…")
        self.device.connect_device()

    def _on_connected(self) -> None:
        self.connect_btn.setText("Disconnect")
        self.statusBar().showMessage(f"Connected to {self.mac_input.text().strip()}")

    def _on_disconnected(self) -> None:
        self.connect_btn.setText("Connect")
        self.statusBar().showMessage("Not connected")
        self.battery_label.setText("Battery: —")

    def _on_battery_updated(self, info: dict) -> None:
        if "pct" in info:
            self.battery_label.setText(f"Battery: {info['pct']}%")
        elif "left_pct" in info:
            self.battery_label.setText(f"Battery: L {info['left_pct']}% / R {info['right_pct']}%")

    def _on_error(self, message: str) -> None:
        self.statusBar().showMessage(message)

    def _on_anc_changed(self, index: int) -> None:
        if not (self.device and self.device.is_connected):
            return
        self.device.set_anc("on" if index == 1 else "off")

    def _on_eq_preset_changed(self, index: int) -> None:
        if not (self.device and self.device.is_connected):
            return
        mode = [protocol.EQMode.SIGNATURE, protocol.EQMode.BALANCED,
                 protocol.EQMode.BASS_BOOST, protocol.EQMode.CUSTOM][index]
        self.device.set_eq_mode(mode)

    def _on_apply_custom_eq(self) -> None:
        if not (self.device and self.device.is_connected):
            self.statusBar().showMessage("Connect to a device first")
            return
        gains = [s.value_db() for s in self.eq_sliders]
        self.device.set_eq_custom_bands(gains)
        self.statusBar().showMessage("Custom EQ sent")


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
