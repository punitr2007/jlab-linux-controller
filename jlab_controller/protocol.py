"""
Airoha RACE protocol framing, scoped to legitimate device-control commands
(EQ, ANC, battery, sleep timer, button mapping) — the same feature set the
vendor's own companion app exposes. No flash/memory access or key-extraction
primitives are implemented here; those are the exploit-relevant parts of the
RACE protocol (CVE-2025-20700/701/702) and are intentionally out of scope.

Packet layout (from prior APK analysis of JLab_2.0.1.5):
    byte 0      : HEADER        (0x05)
    byte 1      : PACKET_TYPE   (0x5A request / 0x5B response / 0x5D indication)
    bytes 2-3   : LENGTH        (uint16, little-endian) — length of RACE_ID + payload
    bytes 4-5   : RACE_ID       (uint16, little-endian)
    bytes 6..N  : PAYLOAD
    [checksum]  : TODO — unconfirmed. Some Airoha RACE variants append a
                  trailing checksum byte/word; the decompiled sources didn't
                  show one for this device's transport, but that needs
                  re-verifying against either the xapk or a live HCI snoop
                  (`btmon`/`hcidump` while running the official JLab app).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from enum import IntEnum


HEADER = 0x05


class PacketType(IntEnum):
    REQUEST = 0x5A
    RESPONSE = 0x5B
    INDICATION = 0x5D


class RaceId(IntEnum):
    # Confirmed from decompiled APK strings/constants.
    GET_BATTERY = 0x0C02
    ANC_ON = 0x1200
    ANC_OFF = 0x1201
    ANC_SET_GAIN = 0x1203

    # TODO: not directly confirmed in this session — plausible neighbors of
    # ANC_* based on typical Airoha RaceId grouping, but verify against
    # RaceId.java / RaceType.java from the decompiled sources before relying
    # on them against real hardware.
    ANC_TRANSPARENCY_ON = 0x1202
    EQ_GET_MODE = 0x0900
    EQ_SET_MODE = 0x0901
    EQ_GET_CUSTOM_BANDS = 0x0902
    EQ_SET_CUSTOM_BANDS = 0x0903
    BUTTON_CONFIG_GET = 0x1400
    BUTTON_CONFIG_SET = 0x1401
    SLEEP_TIMER_SET = 0x1500
    GET_FIRMWARE_VERSION = 0x0001


class EQMode(IntEnum):
    SIGNATURE = 0x01
    BALANCED = 0x02
    BASS_BOOST = 0x03
    CUSTOM = 0x04


# 10-band custom EQ center frequencies (Hz), per APK analysis.
EQ_BANDS_HZ = [30, 60, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
EQ_GAIN_MIN_DB = -12
EQ_GAIN_MAX_DB = 12


@dataclass
class RacePacket:
    packet_type: PacketType
    race_id: int
    payload: bytes = b""

    def encode(self) -> bytes:
        body = struct.pack("<H", self.race_id) + self.payload
        length = len(body)
        return struct.pack("<BBH", HEADER, self.packet_type, length) + body

    @classmethod
    def decode(cls, data: bytes) -> "RacePacket":
        if len(data) < 6 or data[0] != HEADER:
            raise ValueError(f"Not a RACE packet: {data!r}")
        packet_type = PacketType(data[1])
        length = struct.unpack_from("<H", data, 2)[0]
        race_id = struct.unpack_from("<H", data, 4)[0]
        payload = data[6:4 + length + 2]
        return cls(packet_type=packet_type, race_id=race_id, payload=payload)


def build_anc_on() -> bytes:
    return RacePacket(PacketType.REQUEST, RaceId.ANC_ON).encode()


def build_anc_off() -> bytes:
    return RacePacket(PacketType.REQUEST, RaceId.ANC_OFF).encode()


def build_anc_set_gain(level: int) -> bytes:
    """level: 0-100 or a small enum range — TODO confirm exact scale."""
    return RacePacket(PacketType.REQUEST, RaceId.ANC_SET_GAIN, bytes([level])).encode()


def build_get_battery() -> bytes:
    return RacePacket(PacketType.REQUEST, RaceId.GET_BATTERY).encode()


def build_eq_set_mode(mode: EQMode) -> bytes:
    return RacePacket(PacketType.REQUEST, RaceId.EQ_SET_MODE, bytes([mode])).encode()


def build_eq_set_custom_bands(gains_db: list[float]) -> bytes:
    """
    gains_db: 10 values in dB, one per EQ_BANDS_HZ entry.
    TODO: confirm exact wire encoding. Assuming a signed byte per band,
    scaled by 2 (i.e. 0.5 dB steps) based on common Airoha PEQ conventions —
    this is the piece most worth re-verifying with a live capture before
    trusting it against real hardware.
    """
    if len(gains_db) != len(EQ_BANDS_HZ):
        raise ValueError(f"Expected {len(EQ_BANDS_HZ)} band gains, got {len(gains_db)}")
    payload = bytearray()
    for g in gains_db:
        g = max(EQ_GAIN_MIN_DB, min(EQ_GAIN_MAX_DB, g))
        payload.append(int(round(g * 2)) & 0xFF)
    return RacePacket(PacketType.REQUEST, RaceId.EQ_SET_CUSTOM_BANDS, bytes(payload)).encode()


def parse_battery_response(payload: bytes) -> dict:
    """TODO: confirm field order/units; placeholder single-byte percentage per channel."""
    if len(payload) >= 2:
        return {"left_pct": payload[0], "right_pct": payload[1]}
    if len(payload) == 1:
        return {"pct": payload[0]}
    return {}
