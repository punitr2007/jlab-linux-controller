"""Man-Machine Interface (MMI), Battery, and Hardware Sensor protocol encoders."""

from typing import Optional, Dict
from ..constants import RaceId, RaceType
from .race_packet import RacePacket

class MmiEncoder:
    """Handles battery queries, wear detection, latency modes, and touch controls."""

    @staticmethod
    def build_get_battery() -> RacePacket:
        """Queries battery percentage from the connected device."""
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.GET_BATTERY,
            payload=b"",
        )

    @staticmethod
    def build_set_wear_detection(enabled: bool) -> RacePacket:
        """Enables or disables auto-pause / in-ear wear detection sensor."""
        payload = bytes([0x01 if enabled else 0x00])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.SET_IN_EAR_ON_OFF,
            payload=payload,
        )

    @staticmethod
    def build_get_wear_detection() -> RacePacket:
        """Queries in-ear wear detection state."""
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.GET_IN_EAR_ON_OFF,
            payload=b"",
        )

    @staticmethod
    def build_set_low_latency_mode(enabled: bool) -> RacePacket:
        """Enables or disables low-latency movie / game mode."""
        payload = bytes([0x01 if enabled else 0x00])
        return RacePacket(
            race_type=RaceType.CMD_NEED_RESP,
            race_id=RaceId.SWITCH_POWER_MODE,
            payload=payload,
        )

    @staticmethod
    def parse_battery_response(packet: RacePacket) -> Optional[Dict[str, int]]:
        """Parses battery status packet."""
        if packet.race_id in (RaceId.GET_BATTERY, RaceId.BLUETOOTH_TWS_GET_BATTERY):
            if len(packet.payload) >= 1:
                return {
                    "level": packet.payload[0],
                    "is_charging": packet.payload[1] != 0 if len(packet.payload) > 1 else False,
                }
        return None
