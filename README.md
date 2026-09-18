# 🎧 JLab Linux Controller

[![Arch Linux](https://img.shields.io/badge/Platform-Arch%20Linux%20%7C%20Linux-blue?logo=archlinux)](https://archlinux.org/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen?logo=python)](https://python.org/)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-darkblue?logo=qt)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A native Linux desktop application and command-line controller for **JLab Headphones and Earbuds** (including *JLab JBuds Lux ANC*, *JBuds Mini*, *Epic Air ANC*, *Epic Lab Edition*, *Go Air Pop*, *Studio Pro*, and more).

Reverse-engineered directly from the official JLab Android application to provide native control over ANC, Ambient Transparency, 10-band Parametric EQ, low-latency mode, and audio tools without requiring an Android/iOS device.

---

## ✨ Features

- 🔇 **Active Noise Control**:
  - **ANC ON**: Full Active Noise Cancellation.
  - **Be Aware**: Ambient transparency mode with live volume slider (0%–100%).
  - **OFF**: Standard passive isolation.
- 🎚️ **10-Band Parametric Equalizer (PEQ)**:
  - 10 frequency sliders: `32Hz`, `64Hz`, `125Hz`, `250Hz`, `500Hz`, `1kHz`, `2kHz`, `4kHz`, `8kHz`, `16kHz` (`-12 dB` to `+12 dB`).
  - Hardware sound presets: **JLab Signature**, **Balanced**, **Bass Boost**, and **Custom**.
  - One-click *Reset Flat* and persistent custom curve tuning.
- 🔄 **Multi-Protocol Engine**:
  - **JieLi (JL) RCSP Protocol**: Native packet framing for *JBuds Lux ANC*, *JBuds Mini*, *Go Pop+*, *Studio Pro*, and all AC70xx/AC69xx models.
  - **Airoha RACE Protocol**: Native RACE packets for *Epic Air ANC*, *Epic Lab Edition*, and AB156x models.
- ⚡ **Device Settings & Sensors**:
  - In-ear wear detection (auto-pause sensor).
  - Low-latency Movie / Game mode.
  - Live battery percentage and charging status via BlueZ / RFCOMM.
- 🎵 **Audio Utilities**:
  - Proprietary burn-in audio runner.
  - Ambient soundscapes (Rain, White Noise, Ocean, Forest).
- 🖥️ **Seamless Linux Integration**:
  - Modern dark-themed GUI designed with responsive Qt styling.
  - Auto-detection of paired JLab Bluetooth devices via BlueZ D-Bus.
  - Standalone CLI for headless scripts and terminal control.
  - FreeDesktop `.desktop` entry for system application menus.

---

## 🚀 Quick Start

### 1. Prerequisites

Make sure Bluetooth and BlueZ are running on your system:
```bash
# On Arch Linux:
sudo pacman -S bluez bluez-utils python-pip

# On Debian/Ubuntu:
sudo apt install bluez python3-pip python3-venv
```

### 2. Pair Your Headphones

Ensure your JLab headphones are paired and connected to your Linux machine via standard Bluetooth settings or `bluetoothctl`:
```bash
bluetoothctl connect <YOUR_MAC_ADDRESS>
```

### 3. Installation & Setup

Clone the repository and run the automated setup:
```bash
git clone https://github.com/punitr2007/jlab-linux-controller.git
cd jlab-linux-controller

# Create virtual environment and install dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Running the Controller

#### Launch the GUI
```bash
./jlab-controller
```
*(Or `python3 main.py` with the virtual environment activated)*

#### Launch the Command Line Interface (CLI)
```bash
# List paired JLab devices
./.venv/bin/python cli.py scan

# Switch noise control mode
./.venv/bin/python cli.py anc on
./.venv/bin/python cli.py anc be_aware --level 80
./.venv/bin/python cli.py anc off

# Switch EQ preset
./.venv/bin/python cli.py eq signature
./.venv/bin/python cli.py eq bass_boost
./.venv/bin/python cli.py eq custom --gains "2,2,1,0,-1,-2,-2,-1,0,1"

# Query device status
./.venv/bin/python cli.py status
```

---

## 📁 Project Architecture

```
jlab-linux-controller/
├── jlab_controller/
│   ├── bluetooth/
│   │   ├── connection.py     # RFCOMM / SPP Bluetooth socket manager
│   │   └── scanner.py        # BlueZ D-Bus device discovery
│   ├── core/
│   │   └── device.py         # Device state manager & protocol routing
│   ├── gui/
│   │   ├── main_window.py    # Main PyQt6 Controller Window
│   │   └── widgets/          # EQ sliders, Noise Control, Header, Audio Tools
│   ├── protocol/
│   │   ├── jieli_rcsp.py     # JieLi RCSP protocol framing & commands
│   │   ├── race_packet.py    # Airoha RACE protocol framing
│   │   ├── anc.py            # Airoha ANC encoders
│   │   ├── peq.py            # Airoha PEQ encoders
│   │   └── mmi.py            # MMI & sensor controls
│   └── constants.py          # Enums, PID mappings, EQ curves
├── tests/                    # Protocol and framing unit tests
├── cli.py                    # Standalone terminal CLI
├── main.py                   # GUI Application Entrypoint
├── jlab-controller           # Executable launcher script
└── jlab-controller.desktop   # FreeDesktop application launcher
```

---

## 🧪 Testing

Run the test suite to verify packet encoders and decoders:
```bash
./.venv/bin/python -m unittest discover tests
```

---

## 🤝 Contributing

Contributions, bug reports, and feature requests for additional JLab models are welcome! Feel free to open an issue or submit a pull request.

---

## 📄 License

Distributed under the [MIT License](LICENSE).
