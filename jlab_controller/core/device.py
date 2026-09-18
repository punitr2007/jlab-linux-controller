"""JLab Device State Controller and High-Level Operations."""

import logging
from typing import Callable, Dict, List, Optional, Union
from ..constants import (
    EQ_FREQUENCIES,
    EQ_PRESET_GAINS,
    AncMode,
    EqPreset,
    RaceId,
    RaceType,
)
from ..protocol.anc import AncEncoder
from ..protocol.mmi import MmiEncoder
from ..protocol.peq import PeqEncoder
from ..protocol.race_packet import RacePacket
from ..protocol.jieli_rcsp import (
    JieLiPacket,
    JieLiEncoder,
    OP_GET_SYS_INFO,
    OP_SET_SYS_INFO,
    OP_ADV_GET_INFO,
    ATTR_BATTERY,
    ATTR_EQ,
    ATTR_CURRENT_VOICE_MODE,
    ATTR_ALL_VOICE_MODES,
    VOICE_MODE_CLOSE,
    VOICE_MODE_DENOISE,
    VOICE_MODE_TRANSPARENT,
    EQ_MODE_SIGNATURE,
    EQ_MODE_BALANCED,
    EQ_MODE_BASS_BOOST,
    EQ_MODE_CUSTOM,
)
from ..bluetooth.connection import BluetoothConnection

logger = logging.getLogger(__name__)


class ProtocolType:
    JIELI = "jieli"
    AIROHA = "airoha"


class JLabDevice:
    """Manages active device state, settings, and hardware commands."""

    def __init__(self, address: str, name: str = "JLab Headphone"):
        self.address = address
        self.name = name
        self.connection = BluetoothConnection(address)
        
        # Detect chipset protocol family
        self.protocol_type = self._detect_protocol(name)
        logger.info(f"Initialized device {name} ({address}) with protocol '{self.protocol_type}'")

        # State
        self.eq_preset: int = EqPreset.SIGNATURE
        self.custom_eq_gains: List[float] = list(EQ_PRESET_GAINS[EqPreset.CUSTOM])
        self.anc_mode: AncMode = AncMode.ANC_ON
        self.awareness_level: int = 75  # 0..100%
        self.battery_level: int = 100
        self.is_charging: bool = False
        self.wear_detection: bool = True
        self.low_latency_mode: bool = False
        
        self._is_connected = False
        
        # Event callbacks
        self._on_update_callbacks: List[Callable[["JLabDevice"], None]] = []

        # Register packet listener
        self.connection.add_packet_listener(self._handle_packet)
        self.connection.add_state_listener(self._handle_connection_state)

    def _detect_protocol(self, name: str) -> str:
        """Determines if headphone uses JieLi RCSP or Airoha RACE protocol."""
        n = name.lower()
        if "epic air anc" in n or "epic lab" in n or "airoha" in n:
            return ProtocolType.AIROHA
        # JBuds Lux ANC, Go Air Pop, JBuds Mini, Studio, etc. use JieLi
        return ProtocolType.JIELI

    def add_update_listener(self, callback: Callable[["JLabDevice"], None]) -> None:
        if callback not in self._on_update_callbacks:
            self._on_update_callbacks.append(callback)

    def remove_update_listener(self, callback: Callable[["JLabDevice"], None]) -> None:
        if callback in self._on_update_callbacks:
            self._on_update_callbacks.remove(callback)

    def _notify_update(self) -> None:
        for cb in self._on_update_callbacks:
            try:
                cb(self)
            except Exception as e:
                logger.error(f"Error in device update callback: {e}")

    def connect(self) -> bool:
        """Establishes connection and queries initial device state."""
        success = self.connection.connect()
        if success:
            self._is_connected = True
            self.refresh_status()
        return success

    def disconnect(self) -> None:
        self._is_connected = False
        self.connection.disconnect()

    @property
    def is_connected(self) -> bool:
        return self._is_connected or self.connection.is_connected

    @is_connected.setter
    def is_connected(self, val: bool) -> None:
        self._is_connected = val

    def set_eq_preset(self, preset: int) -> bool:
        """Switches active EQ preset (1=Signature, 2=Balanced, 3=Bass Boost, 4=Custom)."""
        self.eq_preset = preset
        
        if self.protocol_type == ProtocolType.JIELI:
            jl_mode_map = {
                EqPreset.SIGNATURE: (EQ_MODE_SIGNATURE, EQ_PRESET_GAINS[EqPreset.SIGNATURE]),
                EqPreset.BALANCED: (EQ_MODE_BALANCED, EQ_PRESET_GAINS[EqPreset.BALANCED]),
                EqPreset.BASS_BOOST: (EQ_MODE_BASS_BOOST, EQ_PRESET_GAINS[EqPreset.BASS_BOOST]),
                EqPreset.CUSTOM: (EQ_MODE_CUSTOM, self.custom_eq_gains),
            }
            mode, gains = jl_mode_map.get(preset, (EQ_MODE_SIGNATURE, EQ_PRESET_GAINS[EqPreset.SIGNATURE]))
            pkt = JieLiEncoder.build_set_eq(mode, gains)
            res = self.connection.send_packet(pkt)
        else:
            pkt = PeqEncoder.build_set_eq_preset(preset)
            res = self.connection.send_packet(pkt)

        self._notify_update()
        return res

    def set_custom_eq_gains(self, gains: List[float]) -> bool:
        """Sets custom 10-band EQ gains (-12dB to +12dB) and activates Custom EQ."""
        self.custom_eq_gains = list(gains)
        self.eq_preset = EqPreset.CUSTOM
        
        if self.protocol_type == ProtocolType.JIELI:
            pkt = JieLiEncoder.build_set_eq(EQ_MODE_CUSTOM, gains)
            res = self.connection.send_packet(pkt)
        else:
            pkt = PeqEncoder.build_custom_10band_gains(gains)
            res = self.connection.send_packet(pkt)

        self._notify_update()
        return res

    def set_anc_mode(self, mode: AncMode) -> bool:
        """Switches noise control mode (ANC ON, Be Aware, OFF)."""
        self.anc_mode = mode
        
        if self.protocol_type == ProtocolType.JIELI:
            if mode == AncMode.ANC_ON:
                jl_mode = VOICE_MODE_DENOISE
            elif mode == AncMode.BE_AWARE:
                jl_mode = VOICE_MODE_TRANSPARENT
            else:
                jl_mode = VOICE_MODE_CLOSE
            
            pkt = JieLiEncoder.build_set_voice_mode(
                mode=jl_mode,
                awareness_level=self.awareness_level,
                left_max=100,
                right_max=100,
            )
            res = self.connection.send_packet(pkt)
        else:
            if mode == AncMode.ANC_ON:
                pkt = AncEncoder.build_set_anc_on(1)
            elif mode == AncMode.BE_AWARE:
                pkt = AncEncoder.build_set_be_aware(9)
            else:
                pkt = AncEncoder.build_set_anc_off()
            res = self.connection.send_packet(pkt)

        self._notify_update()
        return res

    def set_awareness_level(self, level: int) -> bool:
        """Sets Be Aware ambient volume percentage (0..100%)."""
        self.awareness_level = max(0, min(100, level))
        
        if self.protocol_type == ProtocolType.JIELI:
            if self.anc_mode == AncMode.ANC_ON:
                jl_mode = VOICE_MODE_DENOISE
            elif self.anc_mode == AncMode.BE_AWARE:
                jl_mode = VOICE_MODE_TRANSPARENT
            else:
                jl_mode = VOICE_MODE_CLOSE

            pkt = JieLiEncoder.build_set_voice_mode(
                mode=jl_mode,
                awareness_level=self.awareness_level,
                left_max=100,
                right_max=100,
            )
            res = self.connection.send_packet(pkt)
        else:
            pkt = AncEncoder.build_set_awareness_gain(self.awareness_level)
            res = self.connection.send_packet(pkt)

        self._notify_update()
        return res

    def set_wear_detection(self, enabled: bool) -> bool:
        """Toggles in-ear auto-pause sensor."""
        self.wear_detection = enabled
        pkt = MmiEncoder.build_set_wear_detection(enabled)
        res = self.connection.send_packet(pkt)
        self._notify_update()
        return res

    def set_low_latency_mode(self, enabled: bool) -> bool:
        """Toggles low-latency movie / game mode."""
        self.low_latency_mode = enabled
        if self.protocol_type == ProtocolType.JIELI:
            pkt = JieLiEncoder.build_set_low_latency(enabled)
            res = self.connection.send_packet(pkt)
        else:
            pkt = MmiEncoder.build_set_low_latency_mode(enabled)
            res = self.connection.send_packet(pkt)

        self._notify_update()
        return res

    def refresh_status(self) -> None:
        """Queries battery, EQ preset, and ANC status from device."""
        if not self.is_connected:
            return
            
        if self.protocol_type == ProtocolType.JIELI:
            # Query Voice Mode, EQ, Battery, Target Info
            self.connection.send_packet(JieLiEncoder.build_get_current_voice_mode())
            self.connection.send_packet(JieLiEncoder.build_get_eq_preset_and_value())
            self.connection.send_packet(JieLiEncoder.build_get_battery())
            self.connection.send_packet(JieLiEncoder.build_get_adv_info())
        else:
            self.connection.send_packet(MmiEncoder.build_get_battery())
            self.connection.send_packet(PeqEncoder.build_get_eq_preset())
            self.connection.send_packet(AncEncoder.build_get_anc_status())

    def _handle_connection_state(self, connected: bool) -> None:
        if connected:
            self.refresh_status()
        self._notify_update()

    def _handle_packet(self, packet: Union[RacePacket, JieLiPacket]) -> None:
        """Dispatches incoming packets from Bluetooth socket."""
        try:
            if isinstance(packet, JieLiPacket):
                self._handle_jieli_packet(packet)
            elif isinstance(packet, RacePacket):
                self._handle_race_packet(packet)
        except Exception as e:
            logger.error(f"Error handling packet {packet}: {e}")

    def _handle_jieli_packet(self, packet: JieLiPacket) -> None:
        """Decodes incoming JieLi RCSP response/notification packets."""
        payload = packet.payload
        if not payload:
            return

        # Handle SysInfo responses (OpCode 0x07 or 0x08)
        if packet.op_code in (OP_GET_SYS_INFO, OP_SET_SYS_INFO):
            func = payload[0]
            if len(payload) > 1:
                attrs_data = payload[1:]
                offset = 0
                while offset < len(attrs_data):
                    attr_len = attrs_data[offset]
                    if attr_len < 1 or offset + attr_len + 1 > len(attrs_data):
                        break
                    attr_type = attrs_data[offset + 1]
                    attr_body = attrs_data[offset + 2 : offset + 1 + attr_len]
                    offset += 1 + attr_len

                    # Attr 1: Battery
                    if attr_type == ATTR_BATTERY and len(attr_body) >= 1:
                        self.battery_level = min(100, max(0, attr_body[0]))
                        logger.info(f"JieLi: Battery updated to {self.battery_level}%")
                        self._notify_update()

                    # Attr 13 (0x0D): VoiceMode
                    elif attr_type == ATTR_CURRENT_VOICE_MODE and len(attr_body) >= 1:
                        mode = attr_body[0]
                        if mode == VOICE_MODE_DENOISE:
                            self.anc_mode = AncMode.ANC_ON
                        elif mode == VOICE_MODE_TRANSPARENT:
                            self.anc_mode = AncMode.BE_AWARE
                        else:
                            self.anc_mode = AncMode.OFF

                        if len(attr_body) >= 7:
                            self.awareness_level = (attr_body[5] << 8) | attr_body[6]
                        logger.info(f"JieLi: VoiceMode updated to {self.anc_mode.name}, Awareness={self.awareness_level}%")
                        self._notify_update()

                    # Attr 4: EQ
                    elif attr_type == ATTR_EQ and len(attr_body) >= 1:
                        mode = attr_body[0] & 0x7F
                        if mode == EQ_MODE_SIGNATURE:
                            self.eq_preset = EqPreset.SIGNATURE
                        elif mode == EQ_MODE_BALANCED:
                            self.eq_preset = EqPreset.BALANCED
                        elif mode == EQ_MODE_BASS_BOOST:
                            self.eq_preset = EqPreset.BASS_BOOST
                        elif mode == EQ_MODE_CUSTOM:
                            self.eq_preset = EqPreset.CUSTOM

                        if len(attr_body) >= 11:
                            # 10 signed byte gains
                            gains = [float(int.from_bytes(bytes([b]), "big", signed=True)) for b in attr_body[1:11]]
                            self.custom_eq_gains = gains
                        logger.info(f"JieLi: EQ updated to mode {self.eq_preset}")
                        self._notify_update()

    def _handle_race_packet(self, packet: RacePacket) -> None:
        """Decodes incoming Airoha RACE packet responses."""
        if packet.race_type != RaceType.RESPONSE:
            return

        if packet.race_id == RaceId.BATTERY_STATUS:
            if len(packet.payload) >= 2:
                self.battery_level = packet.payload[0]
                self.is_charging = bool(packet.payload[1])
                logger.info(f"Race: Battery: {self.battery_level}%, Charging: {self.is_charging}")
                self._notify_update()

        elif packet.race_id == RaceId.PEQ_GET_PRESET:
            if len(packet.payload) >= 1:
                self.eq_preset = packet.payload[0]
                logger.info(f"Race: Active EQ Preset: {self.eq_preset}")
                self._notify_update()

        elif packet.race_id == RaceId.ANC_GET_STATUS:
            if len(packet.payload) >= 2:
                status = packet.payload[0]
                gain = packet.payload[1]
                if status == 1:
                    self.anc_mode = AncMode.ANC_ON
                elif status == 9:
                    self.anc_mode = AncMode.BE_AWARE
                    self.awareness_level = gain
                else:
                    self.anc_mode = AncMode.OFF
                logger.info(f"Race: ANC Status: {self.anc_mode}, Gain: {self.awareness_level}")
                self._notify_update()
