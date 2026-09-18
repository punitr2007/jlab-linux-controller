"""Airoha RACE protocol packet framing and parser."""

import struct
from typing import Optional, Tuple
from ..constants import RACE_START_CHANNEL_BYTE, RaceType, RaceId

class RacePacket:
    """Represents an Airoha RACE Protocol Packet."""

    def __init__(
        self,
        race_type: int = RaceType.CMD_NEED_RESP,
        race_id: int = 0,
        payload: Optional[bytes] = None,
        channel_byte: int = RACE_START_CHANNEL_BYTE,
    ):
        self.channel_byte = channel_byte
        self.race_type = race_type
        self.race_id = race_id
        self.payload = payload or b""

    def encode(self) -> bytes:
        """Serialize packet into byte array for transmission."""
        # Length is RaceID (2 bytes) + payload length
        length = 2 + len(self.payload)
        header = struct.pack("<BBHH", self.channel_byte, self.race_type, length, self.race_id)
        return header + self.payload

    @classmethod
    def decode(cls, data: bytes) -> Tuple[Optional["RacePacket"], int]:
        """
        Parse raw bytes into a RacePacket.
        Returns (packet, consumed_bytes_count).
        If packet is incomplete, returns (None, 0).
        """
        if len(data) < 6:
            return None, 0

        # Look for valid start channel byte (0x05, 0x07, 0x15)
        start_idx = -1
        for i in range(len(data)):
            if data[i] in (0x05, 0x07, 0x15):
                start_idx = i
                break

        if start_idx == -1:
            return None, len(data)  # Discard all invalid bytes

        if len(data) - start_idx < 6:
            return None, start_idx  # Skip to start byte and wait for more data

        sub = data[start_idx:]
        channel_byte = sub[0]
        race_type = sub[1]
        length, race_id = struct.unpack_from("<HH", sub, 2)

        total_packet_len = 4 + length  # 4 bytes header (channel, type, len_lo, len_hi) + payload_len
        if len(sub) < total_packet_len:
            return None, start_idx  # Incomplete, wait for more data

        payload = sub[6:total_packet_len]
        packet = cls(race_type=race_type, race_id=race_id, payload=payload, channel_byte=channel_byte)
        return packet, start_idx + total_packet_len

    def __repr__(self) -> str:
        return (
            f"RacePacket(type=0x{self.race_type:02X}, "
            f"id=0x{self.race_id:04X} ({RaceId(self.race_id).name if self.race_id in RaceId._value2member_map_ else self.race_id}), "
            f"payload={self.payload.hex().upper()})"
        )
