"""10-Band Equalizer and Preset Manager Panel."""

from typing import List
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)
from ...constants import (
    EQ_FREQUENCIES,
    EQ_PRESET_GAINS,
    EQ_PRESET_NAMES,
    EqPreset,
)
from ...core.device import JLabDevice

class EqPanel(QFrame):
    preset_selected = pyqtSignal(int)      # EqPreset
    custom_gains_changed = pyqtSignal(list) # List[float]

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.preset_buttons: dict[int, QPushButton] = {}
        self.sliders: List[QSlider] = []
        self.gain_labels: List[QLabel] = []
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Header & Actions
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title = QLabel("Equalizer (PEQ)")
        title.setProperty("class", "title")
        subtitle = QLabel("10-Band Parametric Equalizer & Tuning Presets")
        subtitle.setProperty("class", "subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.reset_btn = QPushButton("Reset Flat")
        self.reset_btn.clicked.connect(self._on_flat_reset)
        self.save_btn = QPushButton("Save Custom")
        self.save_btn.setProperty("class", "primary")
        self.save_btn.clicked.connect(self._on_save_custom)

        header_layout.addWidget(self.reset_btn)
        header_layout.addWidget(self.save_btn)
        layout.addLayout(header_layout)

        # Presets Buttons Row
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(8)

        for preset_idx in [EqPreset.SIGNATURE, EqPreset.BALANCED, EqPreset.BASS_BOOST, EqPreset.CUSTOM]:
            name = EQ_PRESET_NAMES[preset_idx]
            btn = QPushButton(name)
            btn.clicked.connect(lambda checked, p=preset_idx: self.preset_selected.emit(p))
            self.preset_buttons[preset_idx] = btn
            preset_layout.addWidget(btn)

        layout.addLayout(preset_layout)

        # 10-Band Sliders Grid
        eq_box = QHBoxLayout()
        eq_box.setSpacing(12)

        for i, freq in enumerate(EQ_FREQUENCIES):
            band_box = QVBoxLayout()
            band_box.setSpacing(6)
            band_box.setAlignment(Qt.AlignmentFlag.AlignHCenter)

            # Gain label (+0dB)
            gain_lbl = QLabel("0dB")
            gain_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            gain_lbl.setStyleSheet("font-size: 11px; color: #718096; min-width: 36px;")
            self.gain_labels.append(gain_lbl)
            band_box.addWidget(gain_lbl)

            # Vertical Slider (-12dB to +12dB)
            slider = QSlider(Qt.Orientation.Vertical)
            slider.setRange(-12, 12)
            slider.setValue(0)
            slider.setMinimumHeight(150)
            slider.valueChanged.connect(lambda val, idx=i: self._on_slider_moved(idx, val))
            self.sliders.append(slider)
            band_box.addWidget(slider, alignment=Qt.AlignmentFlag.AlignHCenter)

            # Frequency Label
            freq_str = f"{freq}Hz" if freq < 1000 else f"{freq // 1000}kHz"
            freq_lbl = QLabel(freq_str)
            freq_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            freq_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #A0AEC0;")
            band_box.addWidget(freq_lbl)

            eq_box.addLayout(band_box)

        layout.addLayout(eq_box)

    def _on_slider_moved(self, band_idx: int, val: int) -> None:
        self.gain_labels[band_idx].setText(f"{val:+d}dB" if val != 0 else "0dB")
        self.gain_labels[band_idx].setStyleSheet(
            "font-size: 11px; font-weight: 600; color: #00AEEF;" if val != 0 else "font-size: 11px; color: #718096;"
        )
        # Emit custom gains
        gains = [float(s.value()) for s in self.sliders]
        self.custom_gains_changed.emit(gains)

    def _on_flat_reset(self) -> None:
        for s in self.sliders:
            s.setValue(0)
        self.preset_selected.emit(EqPreset.CUSTOM)

    def _on_save_custom(self) -> None:
        gains = [float(s.value()) for s in self.sliders]
        self.custom_gains_changed.emit(gains)

    def update_device(self, device: JLabDevice) -> None:
        # Update preset button styles
        for preset_idx, btn in self.preset_buttons.items():
            is_active = device.eq_preset == preset_idx
            btn.setProperty("class", "preset-active" if is_active else "")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        # Update sliders if not on custom or during sync
        gains = (
            EQ_PRESET_GAINS.get(device.eq_preset, device.custom_eq_gains)
            if device.eq_preset != EqPreset.CUSTOM
            else device.custom_eq_gains
        )

        for i, (slider, gain_lbl) in enumerate(zip(self.sliders, self.gain_labels)):
            val = int(round(gains[i])) if i < len(gains) else 0
            slider.blockSignals(True)
            slider.setValue(val)
            slider.blockSignals(False)
            gain_lbl.setText(f"{val:+d}dB" if val != 0 else "0dB")
            gain_lbl.setStyleSheet(
                "font-size: 11px; font-weight: 600; color: #00AEEF;" if val != 0 else "font-size: 11px; color: #718096;"
            )
