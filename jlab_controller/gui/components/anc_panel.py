"""Active Noise Control & Be Aware Mode Panel."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from ...constants import AncMode
from ...core.device import JLabDevice

class AncPanel(QFrame):
    anc_mode_changed = pyqtSignal(object)  # AncMode
    awareness_changed = pyqtSignal(int)    # 0..100

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Header
        title = QLabel("Noise Control")
        title.setProperty("class", "title")
        subtitle = QLabel("Control Active Noise Cancellation and Be Aware transparency")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # 3 Mode Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_anc_on = QPushButton("🔇 ANC ON")
        self.btn_anc_on.clicked.connect(lambda: self.anc_mode_changed.emit(AncMode.ANC_ON))

        self.btn_be_aware = QPushButton("👂 Be Aware")
        self.btn_be_aware.clicked.connect(lambda: self.anc_mode_changed.emit(AncMode.BE_AWARE))

        self.btn_off = QPushButton("○ OFF")
        self.btn_off.clicked.connect(lambda: self.anc_mode_changed.emit(AncMode.OFF))

        btn_layout.addWidget(self.btn_anc_on)
        btn_layout.addWidget(self.btn_be_aware)
        btn_layout.addWidget(self.btn_off)
        layout.addLayout(btn_layout)

        # Awareness Level Slider (Active when Be Aware is selected)
        slider_box = QVBoxLayout()
        slider_box.setSpacing(6)

        slider_label_layout = QHBoxLayout()
        self.slider_title = QLabel("Be Aware Ambient Level")
        self.slider_title.setProperty("class", "subtitle")
        self.slider_value_label = QLabel("75%")
        self.slider_value_label.setProperty("class", "badge")

        slider_label_layout.addWidget(self.slider_title)
        slider_label_layout.addStretch()
        slider_label_layout.addWidget(self.slider_value_label)
        slider_box.addLayout(slider_label_layout)

        self.awareness_slider = QSlider(Qt.Orientation.Horizontal)
        self.awareness_slider.setRange(0, 100)
        self.awareness_slider.setValue(75)
        self.awareness_slider.valueChanged.connect(self._on_slider_changed)
        slider_box.addWidget(self.awareness_slider)

        layout.addLayout(slider_box)

    def _on_slider_changed(self, val: int) -> None:
        self.slider_value_label.setText(f"{val}%")
        self.awareness_changed.emit(val)

    def update_device(self, device: JLabDevice) -> None:
        # Update mode buttons highlighting
        self.btn_anc_on.setProperty("class", "preset-active" if device.anc_mode == AncMode.ANC_ON else "")
        self.btn_be_aware.setProperty("class", "preset-active" if device.anc_mode == AncMode.BE_AWARE else "")
        self.btn_off.setProperty("class", "preset-active" if device.anc_mode == AncMode.OFF else "")

        self.btn_anc_on.style().unpolish(self.btn_anc_on)
        self.btn_anc_on.style().polish(self.btn_anc_on)
        self.btn_be_aware.style().unpolish(self.btn_be_aware)
        self.btn_be_aware.style().polish(self.btn_be_aware)
        self.btn_off.style().unpolish(self.btn_off)
        self.btn_off.style().polish(self.btn_off)

        # Slider state
        self.awareness_slider.setEnabled(device.anc_mode == AncMode.BE_AWARE)
        self.awareness_slider.blockSignals(True)
        self.awareness_slider.setValue(device.awareness_level)
        self.slider_value_label.setText(f"{device.awareness_level}%")
        self.awareness_slider.blockSignals(False)
