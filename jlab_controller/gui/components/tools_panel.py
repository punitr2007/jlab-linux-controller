"""Burn-In Tool and Ambient Noise Generator Component."""

from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from ...core.audio_tools import NoisePlayer

class ToolsPanel(QFrame):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.player = NoisePlayer()
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("Audio Tools & Burn-In")
        title.setProperty("class", "title")
        subtitle = QLabel("Burn-in audio drivers and play background relaxation noise")
        subtitle.setProperty("class", "subtitle")
        layout.addWidget(title)
        layout.addWidget(subtitle)

        # Ambient / Relaxation Noise Row
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_pink = QPushButton("🌸 Pink Noise (Burn-In)")
        self.btn_pink.clicked.connect(lambda: self._toggle_play("pink", self.btn_pink))

        self.btn_white = QPushButton("⚪ White Noise")
        self.btn_white.clicked.connect(lambda: self._toggle_play("white", self.btn_white))

        self.btn_sweep = QPushButton("🌊 Sine Sweep")
        self.btn_sweep.clicked.connect(lambda: self._toggle_play("sweep", self.btn_sweep))

        btn_layout.addWidget(self.btn_pink)
        btn_layout.addWidget(self.btn_white)
        btn_layout.addWidget(self.btn_sweep)
        layout.addLayout(btn_layout)

        # Status text
        self.status_label = QLabel("Playback stopped")
        self.status_label.setProperty("class", "subtitle")
        layout.addWidget(self.status_label)

    def _toggle_play(self, noise_type: str, btn: QPushButton) -> None:
        if self.player.active_mode == noise_type:
            self.player.stop()
            self.status_label.setText("Playback stopped")
            self._update_btn_styles(None)
        else:
            self.player.play(noise_type)
            self.status_label.setText(f"Playing {noise_type.title()} noise...")
            self._update_btn_styles(btn)

    def _update_btn_styles(self, active_btn: QPushButton | None) -> None:
        for b in [self.btn_pink, self.btn_white, self.btn_sweep]:
            b.setProperty("class", "preset-active" if b == active_btn else "")
            b.style().unpolish(b)
            b.style().polish(b)

    def closeEvent(self, event) -> None:
        self.player.stop()
        super().closeEvent(event)
