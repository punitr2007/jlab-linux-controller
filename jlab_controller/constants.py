"""Constants and definitions for JLab Headphone Controller."""

from enum import Enum, IntEnum
from typing import Dict, List

# RACE Packet Constants
RACE_START_CHANNEL_BYTE = 0x05

class RaceType(IntEnum):
    CMD_NEED_RESP = 0x5A   # 90
    RESPONSE = 0x5B        # 91
    CMD_NO_RESP = 0x5C     # 92
    INDICATION = 0x5D      # 93

class RaceId(IntEnum):
    # Host Audio & MMI
    HOSTAUDIO_MMI_SET_ENUM = 0x0900    # 2304 (Module 0=PEQ, Module 5=ANC)
    HOSTAUDIO_MMI_GET_ENUM = 0x0901    # 2305
    HOSTAUDIO_PEQ_SAVE_STATUS = 0x09FD # 2557
    SYNC_PEQ_UI_WITH_FW = 0x0E2B       # 3627
    DSP_REALTIME_PEQ = 0x0E00          # 3584

    # Anc & Ambient Control
    MMI_ANC_CONTROL = 0x0E06           # 3590 (Turn On/Off/PassThru/Gain)
    ANC_ON = 0x1200                    # 4608
    ANC_OFF = 0x1201                   # 4609
    ANC_GET_STATUS = 0x1202            # 4610
    ANC_SET_GAIN = 0x1203              # 4611

    # Battery & Telemetry
    GET_BATTERY = 0x0C02               # 3074
    BLUETOOTH_TWS_GET_BATTERY = 0x0CD6 # 3286

    # NVKey
    NVKEY_READFULLKEY = 0x0A00         # 2560
    NVKEY_WRITEFULLKEY = 0x0A01        # 2561

    # Hardware & Sensors
    SET_IN_EAR_ON_OFF = 0x2C10         # 11280 (Wear detection)
    GET_IN_EAR_ON_OFF = 0x2C11         # 11281
    SET_MMI_COMMON_CONFIG = 0x2C82     # 11394
    GET_MMI_COMMON_CONFIG = 0x2C83     # 11395
    JLAB_TOUCH_ACTIVATE = 0x000E       # 14
    SWITCH_POWER_MODE = 0x020D         # 525 (Low latency / Game mode)
    GET_POWER_MODE = 0x020C            # 524

# Standard Bluetooth UUIDs
UUID_AIROHA_SPP = "00000000-0000-0000-0099-aabbccddeeff"
UUID_SERIAL_PORT = "00001101-0000-1000-8000-00805f9b34fb"
UUID_AIROHA_GATT_SERVICE = "5052494d-2dab-0341-6972-6f6861424c45"
UUID_AIROHA_GATT_TX = "43484152-2dab-3241-6972-6f6861424c45"
UUID_AIROHA_GATT_RX = "43484152-2dab-3141-6972-6f6861424c45"

# Equalizer Frequencies (10 bands in Hz)
EQ_FREQUENCIES: List[int] = [30, 60, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]

# Default EQ Presets
class EqPreset(IntEnum):
    SIGNATURE = 1
    BALANCED = 2
    BASS_BOOST = 3
    CUSTOM = 4

EQ_PRESET_NAMES: Dict[int, str] = {
    EqPreset.SIGNATURE: "JLab Signature",
    EqPreset.BALANCED: "Balanced",
    EqPreset.BASS_BOOST: "Bass Boost",
    EqPreset.CUSTOM: "Custom",
}

EQ_PRESET_GAINS: Dict[int, List[float]] = {
    EqPreset.SIGNATURE: [1.0, 1.0, 0.0, -2.0, -3.0, -4.0, -4.0, -2.0, -1.0, -2.0],
    EqPreset.BALANCED: [-1.0, 0.0, -1.0, -2.0, -2.0, -2.0, -2.0, -1.0, -1.0, -2.0],
    EqPreset.BASS_BOOST: [3.0, 3.0, 2.0, 0.0, -2.0, -3.0, -3.0, -4.0, -3.0, -1.0],
    EqPreset.CUSTOM: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
}

# Noise Control Modes
class AncMode(str, Enum):
    ANC_ON = "anc_on"
    BE_AWARE = "be_aware"
    OFF = "off"

# Known JLab Bluetooth Vendor IDs / Prefixes
JLAB_OUI_PREFIXES = ["DC:A8:00", "00:0A:F5", "3C:A6:F6", "84:D3:52"]
JLAB_MODALIAS_VENDOR = "05D6"  # Airoha
