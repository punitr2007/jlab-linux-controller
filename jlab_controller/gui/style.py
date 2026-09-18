"""Modern Dark Theme stylesheet for JLab Controller."""

DARK_THEME = """
QWidget {
    background-color: #0E1116;
    color: #E2E8F0;
    font-family: 'Inter', 'Segoe UI', 'Ubuntu', sans-serif;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background: transparent;
}

QScrollBar:vertical {
    background: #0E1116;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2D3748;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #00AEEF;
}

QFrame.card {
    background-color: #171B22;
    border: 1px solid #232936;
    border-radius: 12px;
    padding: 16px;
}

QFrame.card:hover {
    border: 1px solid #2E384D;
}

QLabel.title {
    font-size: 16px;
    font-weight: 700;
    color: #FFFFFF;
}

QLabel.subtitle {
    font-size: 12px;
    color: #718096;
}

QLabel.badge {
    background-color: #1E293B;
    color: #00AEEF;
    font-size: 11px;
    font-weight: 600;
    padding: 3px 8px;
    border-radius: 6px;
    border: 1px solid #00AEEF33;
}

QPushButton {
    background-color: #1E2530;
    color: #E2E8F0;
    border: 1px solid #2D3748;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #283344;
    border-color: #00AEEF;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #00AEEF;
    color: #0E1116;
}

QPushButton.primary {
    background-color: #00AEEF;
    color: #0E1116;
    border: none;
    font-weight: 700;
}

QPushButton.primary:hover {
    background-color: #38BDF8;
}

QPushButton.primary:pressed {
    background-color: #0284C7;
}

QPushButton.preset-active {
    background-color: #00AEEF22;
    border: 2px solid #00AEEF;
    color: #00AEEF;
    font-weight: 700;
}

QSlider::groove:vertical {
    background: #232936;
    width: 6px;
    border-radius: 3px;
}

QSlider::sub-page:vertical {
    background: #232936;
    border-radius: 3px;
}

QSlider::add-page:vertical {
    background: #00AEEF;
    border-radius: 3px;
}

QSlider::handle:vertical {
    background: #FFFFFF;
    border: 2px solid #00AEEF;
    height: 16px;
    margin: 0 -5px;
    border-radius: 8px;
}

QSlider::handle:vertical:hover {
    background: #00AEEF;
    border-color: #FFFFFF;
}

QSlider::groove:horizontal {
    background: #232936;
    height: 6px;
    border-radius: 3px;
}

QSlider::sub-page:horizontal {
    background: #00AEEF;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #FFFFFF;
    border: 2px solid #00AEEF;
    width: 16px;
    margin: -5px 0;
    border-radius: 8px;
}

QCheckBox {
    spacing: 8px;
    color: #E2E8F0;
    font-weight: 500;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #2D3748;
    background: #171B22;
}

QCheckBox::indicator:checked {
    background: #00AEEF;
    border-color: #00AEEF;
}

QTabWidget::pane {
    border: none;
    background: transparent;
}

QTabBar::tab {
    background: #171B22;
    color: #A0AEC0;
    padding: 10px 20px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    margin-right: 4px;
    font-weight: 600;
}

QTabBar::tab:selected {
    background: #1E2530;
    color: #00AEEF;
    border-bottom: 2px solid #00AEEF;
}
"""
