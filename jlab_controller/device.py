from __future__ import annotations

from PyQt6.QtCore import QObject, pyqtSignal

from . import protocol
from .transport import RfcommTransport


class JLabDevice(QObject):
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    battery_updated = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, mac_address: str):
        super().__init__()
        self.mac_address = mac_address
        self._transport = RfcommTransport(mac_address)
        self._transport.on_data = self._handle_data

    def connect_device(self) -> None:
        try:
            self._transport.connect()
            self.connected.emit()
            self.request_battery()
        except OSError as e:
            self.error.emit(f"Connection failed: {e}")

    def disconnect_device(self) -> None:
        self._transport.disconnect()
        self.disconnected.emit()

    @property
    def is_connected(self) -> bool:
        return self._transport.is_connected

    # --- Commands -----------------------------------------------------

    def set_anc(self, mode: str) -> None:
        """mode: 'on' | 'off'"""
        if mode == "on":
            self._send(protocol.build_anc_on())
        elif mode == "off":
            self._send(protocol.build_anc_off())
        else:
            raise ValueError(f"Unknown ANC mode: {mode}")

    def set_anc_gain(self, level: int) -> None:
        self._send(protocol.build_anc_set_gain(level))

    def set_eq_mode(self, mode: protocol.EQMode) -> None:
        self._send(protocol.build_eq_set_mode(mode))

    def set_eq_custom_bands(self, gains_db: list[float]) -> None:
        self._send(protocol.build_eq_set_custom_bands(gains_db))

    def request_battery(self) -> None:
        self._send(protocol.build_get_battery())

    # --- Internals ------------------------------------------------------

    def _send(self, data: bytes) -> None:
        if not self._transport.is_connected:
            self.error.emit("Not connected")
            return
        try:
            self._transport.send(data)
        except OSError as e:
            self.error.emit(f"Send failed: {e}")

    def _handle_data(self, data: bytes) -> None:
        try:
            packet = protocol.RacePacket.decode(data)
        except ValueError:
            return
        if packet.race_id == protocol.RaceId.GET_BATTERY:
            self.battery_updated.emit(protocol.parse_battery_response(packet.payload))
