"""JieLi (JL) RCSP Protocol Encoder and Decoder.

Implements packet framing and commands for JieLi AC70xx/AC69xx chipsets used in
JLab headphones (e.g., JLab JBuds Lux ANC, JBuds Mini, Go Pop+, Studio Pro).
"""

from __future__ import annotations
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

PREFIX = bytes([0xFE, 0xDC, 0xBA])
SUFFIX = bytes([0xEF])

# JieLi RCSP OpCodes
OP_DATA = 0x01
OP_GET_TARGET_FEATURE = 0x02
OP_GET_TARGET_INFO = 0x03
OP_DISCONNECT_CLASSIC_BT = 0x06
OP_GET_SYS_INFO = 0x07
OP_SET_SYS_INFO = 0x08
OP_PHONE_CALL_REQUEST = 0x0A
OP_NOTIFY_COMMUNICATION_WAY = 0x0B
OP_FUNCTION = 0x0E
OP_SEARCH_DEV = 0x19
OP_QUERY_CONNECTED_PHONE_BT_INFO = 0x31
OP_PUBLIC_SETTINGS = 0x33
OP_ADV_SETTINGS = 0xC0
OP_ADV_GET_INFO = 0xC1
OP_ADV_DEVICE_NOTIFY = 0xC2
OP_ADV_NOTIFY_SETTINGS = 0xC3
OP_ADV_DEV_REQUEST_OPERATION = 0xC4
OP_GET_DEV_MD5 = 0xD4
OP_GET_LOW_LATENCY_SETTINGS = 0xD5
OP_GET_DEVICE_CONFIG_INFO = 0xD9
OP_CUSTOM = 0xF0
OP_EXTRA_CUSTOM = 0xFF

# Function types for SysInfo
FUNC_BT = 0x00
FUNC_MUSIC = 0x01
FUNC_RTC = 0x02
FUNC_LINEIN = 0x03
FUNC_FM = 0x04
FUNC_LIGHT = 0x08
FUNC_PC_SLAVE = 0x09
FUNC_PUBLIC = 0xFF

# Public SysInfo Attribute Types
ATTR_BATTERY = 0x01
ATTR_VOL = 0x02
ATTR_EQ = 0x04
ATTR_FILE_BROWSE = 0x05
ATTR_ALARM = 0x06
ATTR_EMITTER_MODE = 0x09
ATTR_EMITTER_STATUS = 0x0A
ATTR_EQ_PRESET = 0x0C
ATTR_CURRENT_VOICE_MODE = 0x0D
ATTR_ALL_VOICE_MODES = 0x0E
ATTR_FIXED_LEN_DATA = 0x10
ATTR_DOUBLE_CONNECTION = 0x1B
ATTR_HEARING_ASSIST = 0x14

# VoiceMode constants
VOICE_MODE_CLOSE = 0       # OFF
VOICE_MODE_DENOISE = 1     # ANC ON
VOICE_MODE_TRANSPARENT = 2 # Be Aware / Transparency

# EQ Mode constants
EQ_MODE_SIGNATURE = 0
EQ_MODE_BALANCED = 1
EQ_MODE_BASS_BOOST = 2
EQ_MODE_CUSTOM = 6


@dataclass
class JieLiPacket:
    """Represents a JieLi RCSP protocol frame."""
    op_code: int
    payload: bytes = field(default_factory=bytes)
    sn: int = 1
    has_response: bool = False
    is_command: bool = True
    status: int = 0

    def encode(self) -> bytes:
        """Serializes the JieLiPacket into raw frame bytes."""
        # Flag byte: bit 7 = is_command (1 for cmd, 0 for resp), bit 6 = has_response
        flag = 0
        if self.is_command:
            flag |= 0x80
        if self.has_response:
            flag |= 0x40

        # ParamLen includes 1 byte SN (+ status byte if response) + payload
        param_len = 1 + len(self.payload)
        if not self.is_command:
            param_len += 1  # status byte

        frame = bytearray()
        frame.extend(PREFIX)
        frame.append(flag)
        frame.append(self.op_code & 0xFF)
        frame.append((param_len >> 8) & 0xFF)
        frame.append(param_len & 0xFF)
        if not self.is_command:
            frame.append(self.status & 0xFF)
        frame.append(self.sn & 0xFF)
        frame.extend(self.payload)
        frame.extend(SUFFIX)
        return bytes(frame)

    @classmethod
    def decode(cls, data: bytes) -> Tuple[Optional[JieLiPacket], int]:
        """Parses a JieLi RCSP packet from buffer.
        
        Returns:
            Tuple of (packet or None, bytes_consumed).
        """
        if len(data) < 8:
            return None, 0

        idx = data.find(PREFIX)
        if idx < 0:
            return None, len(data)
        if idx > 0:
            return None, idx

        if len(data) < 7:
            return None, 0

        flag = data[3]
        op_code = data[4]
        param_len = (data[5] << 8) | data[6]

        total_expected = 7 + param_len + 1  # Prefix(3) + Flag(1) + Op(1) + Len(2) + Payload(param_len) + Suffix(1)
        if len(data) < total_expected:
            return None, 0

        if data[total_expected - 1] != 0xEF:
            # Framing error, skip prefix
            logger.warning(f"JieLi framing error: missing 0xEF footer at offset {total_expected - 1}")
            return None, 3

        is_command = bool(flag & 0x80)
        has_response = bool(flag & 0x40)

        offset = 7
        status = 0
        if not is_command:
            status = data[offset]
            offset += 1

        sn = data[offset]
        offset += 1

        payload_len = total_expected - 1 - offset
        payload = data[offset : offset + payload_len]

        pkt = cls(
            op_code=op_code,
            payload=payload,
            sn=sn,
            has_response=has_response,
            is_command=is_command,
            status=status,
        )
        return pkt, total_expected


class JieLiEncoder:
    """Helper methods for generating JieLi RCSP command packets."""

    _sn_counter = 0

    @classmethod
    def _next_sn(cls) -> int:
        cls._sn_counter = (cls._sn_counter + 1) & 0xFF
        if cls._sn_counter == 0:
            cls._sn_counter = 1
        return cls._sn_counter

    # Native device scale for voice mode intensity (from JLab AncView4Jieli: leftMax defaults to 16384)
    _VOICE_MODE_MAX_NATIVE = 16384

    @classmethod
    def build_set_voice_mode(
        cls,
        mode: int,
        awareness_level: int = 75,
    ) -> JieLiPacket:
        """Builds SetSysInfo command for Noise Control (ANC ON=1, Be Aware=2, OFF=0).
        
        awareness_level: 0..100 (percentage). Internally scaled to 0..16384 (native device scale).
        SetSysInfoCmd extends CommandWithParamAndResponse so has_response MUST be True.
        
        VoiceMode 9-byte layout (from VoiceMode.java getBytes()):
          [0]   = mode
          [1,2] = leftMax  (BE uint16, native max = 16384)
          [3,4] = rightMax (BE uint16, native max = 16384)
          [5,6] = leftCurVal  (BE uint16, scaled from 0..100%)
          [7,8] = rightCurVal (BE uint16, same as leftCurVal for mono channel)
        """
        # Scale 0..100% -> 0..16384 native device range
        pct = max(0, min(100, awareness_level))
        cur_val = int(pct / 100.0 * cls._VOICE_MODE_MAX_NATIVE)
        left_max = cls._VOICE_MODE_MAX_NATIVE
        right_max = cls._VOICE_MODE_MAX_NATIVE

        attr_data = bytes([
            mode & 0xFF,
            (left_max >> 8) & 0xFF, left_max & 0xFF,    # leftMax
            (right_max >> 8) & 0xFF, right_max & 0xFF,  # rightMax
            (cur_val >> 8) & 0xFF, cur_val & 0xFF,      # leftCurVal
            (cur_val >> 8) & 0xFF, cur_val & 0xFF,      # rightCurVal
        ])

        # AttrBean.toData(): [attrData.len + 1, type, attrData...]
        attr_len = len(attr_data) + 1  # = 10
        attr_bean = bytes([attr_len, ATTR_CURRENT_VOICE_MODE]) + attr_data

        # SetSysInfoParam.getParamData(): [function=0xFF] + AttrBeans
        payload = bytes([FUNC_PUBLIC]) + attr_bean

        return JieLiPacket(
            op_code=OP_SET_SYS_INFO,
            payload=payload,
            sn=cls._next_sn(),
            has_response=True,   # SetSysInfoCmd extends CommandWithParamAndResponse
            is_command=True,
        )

    @classmethod
    def build_set_eq(
        cls,
        mode: int,
        gains: Optional[List[Union[int, float]]] = None,
    ) -> JieLiPacket:
        """Builds SetSysInfo command for 10-band Equalizer presets or custom gains.
        
        Modes: 0=Signature, 1=Balanced, 2=Bass Boost, 6=Custom.
        Gains: 10 signed integers in dB range (-12 to +12).
        SetSysInfoCmd extends CommandWithParamAndResponse so has_response MUST be True.
        """
        gain_bytes = bytearray(10)
        if gains and len(gains) == 10:
            for i, g in enumerate(gains):
                val = int(round(g))
                # Clamp to -12..+12 dB signed byte
                val = max(-12, min(12, val))
                gain_bytes[i] = val & 0xFF

        # AttrData: [mode, gain0, gain1, ..., gain9] (11 bytes)
        attr_data = bytes([mode & 0xFF]) + bytes(gain_bytes)

        # AttrBean.toData(): [attrData.len + 1, type, attrData...]
        attr_len = len(attr_data) + 1  # = 12
        attr_bean = bytes([attr_len, ATTR_EQ]) + attr_data

        # SetSysInfoParam.getParamData(): [function=0xFF] + AttrBeans
        payload = bytes([FUNC_PUBLIC]) + attr_bean

        return JieLiPacket(
            op_code=OP_SET_SYS_INFO,
            payload=payload,
            sn=cls._next_sn(),
            has_response=True,   # SetSysInfoCmd extends CommandWithParamAndResponse
            is_command=True,
        )

    @classmethod
    def build_get_sys_info(cls, mask: int, func: int = FUNC_PUBLIC) -> JieLiPacket:
        """Builds GetSysInfo command for specified bitmask."""
        payload = bytes([
            func & 0xFF,
            (mask >> 24) & 0xFF,
            (mask >> 16) & 0xFF,
            (mask >> 8) & 0xFF,
            mask & 0xFF,
        ])
        return JieLiPacket(
            op_code=OP_GET_SYS_INFO,
            payload=payload,
            sn=cls._next_sn(),
            has_response=True,
            is_command=True,
        )

    @classmethod
    def build_get_current_voice_mode(cls) -> JieLiPacket:
        """Queries active ANC / Be Aware voice mode."""
        return cls.build_get_sys_info(mask=8192)  # Bit 13 (0x2000)

    @classmethod
    def build_get_all_voice_modes(cls) -> JieLiPacket:
        """Queries voice mode capabilities."""
        return cls.build_get_sys_info(mask=16384)  # Bit 14 (0x4000)

    @classmethod
    def build_get_eq_preset_and_value(cls) -> JieLiPacket:
        """Queries active EQ preset and gain values."""
        return cls.build_get_sys_info(mask=4112)  # 0x1010

    @classmethod
    def build_get_battery(cls) -> JieLiPacket:
        """Queries battery level."""
        return cls.build_get_sys_info(mask=1)

    @classmethod
    def build_get_target_info(cls, mask: int = 0xFFFFFFFF) -> JieLiPacket:
        """Queries target device hardware and firmware info."""
        payload = bytes([
            (mask >> 24) & 0xFF,
            (mask >> 16) & 0xFF,
            (mask >> 8) & 0xFF,
            mask & 0xFF,
        ])
        return JieLiPacket(
            op_code=OP_GET_TARGET_INFO,
            payload=payload,
            sn=cls._next_sn(),
            has_response=True,
            is_command=True,
        )

    @classmethod
    def build_get_adv_info(cls, mask: int = 0xFFFFFFFF) -> JieLiPacket:
        """Queries ADV info (VID, PID, UID, settings)."""
        payload = bytes([
            (mask >> 24) & 0xFF,
            (mask >> 16) & 0xFF,
            (mask >> 8) & 0xFF,
            mask & 0xFF,
        ])
        return JieLiPacket(
            op_code=OP_ADV_GET_INFO,
            payload=payload,
            sn=cls._next_sn(),
            has_response=True,
            is_command=True,
        )

    @classmethod
    def build_set_low_latency(cls, enabled: bool) -> JieLiPacket:
        """Toggles low-latency game mode on JieLi."""
        # OpCode 0x19 / Custom command or SYS_INFO
        payload = bytes([0x01 if enabled else 0x00])
        return JieLiPacket(
            op_code=OP_GET_LOW_LATENCY_SETTINGS,
            payload=payload,
            sn=cls._next_sn(),
            has_response=False,
            is_command=True,
        )
