"""
Bluetooth RFCOMM transport using the standard library's socket module
(AF_BLUETOOTH / BTPROTO_RFCOMM), which BlueZ exposes natively on Linux —
no pybluez or Android runtime needed.

SPP UUID used by the JLab app: 00001101-0000-1000-8000-00805f9b34fb
"""
from __future__ import annotations

import socket
import threading
from typing import Callable, Optional

SPP_UUID = "00001101-0000-1000-8000-00805f9b34fb"
RFCOMM_CHANNEL = 1  # TODO: confirm actual SDP-advertised channel for your device;
                    # 1 is a common default but should be looked up via
                    # `sdptool records <MAC>` against the paired earbuds.


class RfcommTransport:
    def __init__(self, mac_address: str, channel: int = RFCOMM_CHANNEL):
        self.mac_address = mac_address
        self.channel = channel
        self._sock: Optional[socket.socket] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._running = False
        self.on_data: Optional[Callable[[bytes], None]] = None

    def connect(self, timeout: float = 10.0) -> None:
        self._sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self._sock.settimeout(timeout)
        self._sock.connect((self.mac_address, self.channel))
        self._sock.settimeout(None)
        self._running = True
        self._reader_thread = threading.Thread(target=self._read_loop, daemon=True)
        self._reader_thread.start()

    def disconnect(self) -> None:
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def send(self, data: bytes) -> None:
        if not self._sock:
            raise RuntimeError("Not connected")
        self._sock.sendall(data)

    def _read_loop(self) -> None:
        buf = b""
        while self._running and self._sock:
            try:
                chunk = self._sock.recv(4096)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
            # RACE packets are self-length-prefixed; hand off whatever
            # arrived and let the device layer worry about framing/reassembly.
            if self.on_data:
                self.on_data(buf)
            buf = b""

    @property
    def is_connected(self) -> bool:
        return self._sock is not None
