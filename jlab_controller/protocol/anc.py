"""Active Noise Cancellation (ANC) & Ambient / Be Aware protocol encoder and decoder."""

import struct
from typing import Optional, Tuple
from ..constants import AncMode, RaceId, RaceType
from .race_packet import RacePacket

class AncEncoder:
    """Handles generating and parsing JLab / Airoha ANC and Be Aware packets."""

    @staticmethod
    def build_set_anc_on(filter_id: int = 1) -> RacePacket:
        """
        Builds the packet to enable Active Noise Cancellation (ANC ON).
        Filter 1..8: ANC filters.
        """
        # [0x00, 0x0A (turn on), filter_id, 0x01 (syncMode)]
        payload = bytes([0x00, 0x0A, filter_id, 0x01])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.MMI_ANC_CONTROL,
            payload=payload,
        )

    @staticmethod
    def build_set_be_aware(filter_id: int = 9) -> RacePacket:
        """
        Builds the packet to enable Be Aware (Transparency / Ambient) mode.
        Filter 9..11: Pass-through / Be Aware filters.
        """
        payload = bytes([0x00, 0x0A, filter_id, 0x01])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.MMI_ANC_CONTROL,
            payload=payload,
        )

    @staticmethod
    def build_set_anc_off() -> RacePacket:
        """Builds the packet to turn OFF ANC and Be Aware."""
        # [0x00, 0x0B (turn off), 0x01 (syncMode)]
        payload = bytes([0x00, 0x0B, 0x01])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.MMI_ANC_CONTROL,
            payload=payload,
        )

    @staticmethod
    def build_set_awareness_gain(gain: int) -> RacePacket:
        """
        Sets the Be Aware ambient transparency volume level.
        gain: 0 to 100
        """
        clamped_gain = max(0, min(100, int(gain)))
        gain_lo = clamped_gain & 0xFF
        gain_hi = (clamped_gain >> 8) & 0xFF
        # [0x00, 0x0F (set pass-thru gain), gain_lo, gain_hi, 0x01 (syncMode)]
        payload = bytes([0x00, 0x0F, gain_lo, gain_hi, 0x01])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.MMI_ANC_CONTROL,
            payload=payload,
        )

    @staticmethod
    def build_get_anc_status() -> RacePacket:
        """Queries the current ANC/Ambient mode and level."""
        payload = struct.pack("<H", 5)  # Module 5 = ANC in Airoha HostAudio MMI
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.HOSTAUDIO_MMI_GET_ENUM,
            payload=payload,
        )

    @staticmethod
    def parse_anc_response(packet: RacePacket) -> Optional[Tuple[AncMode, int]]:
        """
        Parses an ANC response or indication.
        Returns (AncMode, awareness_level) or None.
        """
        if packet.race_id == RaceId.HOSTAUDIO_MMI_GET_ENUM and len(packet.payload) >= 4:
            module = struct.unpack_from("<H", packet.payload, 0)[0]
            if module == 5:
                status_byte = packet.payload[2]
                mode_byte = packet.payload[3] if len(packet.payload) > 3 else 0
                gain = packet.payload[4] if len(packet.payload) > 4 else 100
                if mode_byte == 0:
                    return AncMode.OFF, gain
                elif mode_byte in (1, 2, 3, 4, 5, 6, 7, 8):
                    return AncMode.ANC_ON, gain
                else:
                    return AncMode.BE_AWARE, gain
        return None
