"""Parametric Equalizer (PEQ) protocol encoder and decoders."""

import struct
from typing import List, Optional, Tuple
from ..constants import EQ_FREQUENCIES, EqPreset, RaceId, RaceType
from .race_packet import RacePacket

class PeqEncoder:
    """Handles generating and parsing JLab / Airoha Equalizer packets."""

    @staticmethod
    def build_set_eq_preset(preset_idx: int) -> RacePacket:
        """
        Builds the packet to switch the active EQ preset.
        preset_idx: 1 (Signature), 2 (Balanced), 3 (Bass Boost), 4 (Custom)
        """
        # Module 0 is PEQ module in Airoha HostAudio MMI
        payload = struct.pack("<HB", 0, preset_idx)
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.HOSTAUDIO_MMI_SET_ENUM,
            payload=payload,
        )

    @staticmethod
    def build_get_eq_preset() -> RacePacket:
        """Builds the packet to query current active EQ preset."""
        payload = struct.pack("<H", 0)  # Module 0
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.HOSTAUDIO_MMI_GET_ENUM,
            payload=payload,
        )

    @staticmethod
    def build_custom_10band_gains(gains: List[float]) -> RacePacket:
        """
        Builds a custom 10-band EQ gain packet.
        gains: list of 10 floats in range [-12.0, +12.0] dB
        """
        assert len(gains) == 10, "10 gain values required for 10-band EQ"
        # Format: 10 gain bytes (signed int8 or float)
        clamped_gains = [max(-12, min(12, int(round(g)))) for g in gains]
        gain_bytes = bytes([g & 0xFF for g in clamped_gains])
        
        # Real-time PEQ update command
        payload = struct.pack("<BB", 0x01, 10) + gain_bytes
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.DSP_REALTIME_PEQ,
            payload=payload,
        )

    @staticmethod
    def parse_eq_indication(packet: RacePacket) -> Optional[int]:
        """
        Parses unsolicited EQ switch indications (e.g. user tapped headset).
        Returns preset index (1..4) or None.
        """
        # Packet format from hardware: 05 5D 06 00 01 09 00 00 00 <idx>
        if packet.race_type == RaceType.INDICATION and packet.race_id == RaceId.HOSTAUDIO_MMI_GET_ENUM:
            if len(packet.payload) >= 4:
                # payload starts with module (2 bytes), status (1 byte), preset_idx (1 byte)
                module = struct.unpack_from("<H", packet.payload, 0)[0]
                if module == 0 and len(packet.payload) >= 4:
                    return packet.payload[3]
        return None
