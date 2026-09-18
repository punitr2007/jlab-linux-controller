"""Bluetooth RFCOMM socket connection manager for JLab devices."""

import errno
import logging
import socket
import threading
import time
from typing import Callable, List, Optional, Union
from ..protocol.race_packet import RacePacket
from ..protocol.jieli_rcsp import JieLiPacket

logger = logging.getLogger(__name__)

PacketType = Union[RacePacket, JieLiPacket]

class BluetoothConnection:
    """Manages RFCOMM communication with the headphone."""

    def __init__(self, target_address: str, channel: int = 1):
        self.target_address = target_address
        self.channel = channel
        self.sock: Optional[socket.socket] = None
        self._running = False
        self._rx_thread: Optional[threading.Thread] = None
        self._listeners: List[Callable[[PacketType], None]] = []
        self._state_listeners: List[Callable[[bool], None]] = []
        self._lock = threading.RLock()
        self.is_connected = False

    def add_packet_listener(self, listener: Callable[[PacketType], None]) -> None:
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_packet_listener(self, listener: Callable[[PacketType], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def add_state_listener(self, listener: Callable[[bool], None]) -> None:
        if listener not in self._state_listeners:
            self._state_listeners.append(listener)

    def remove_state_listener(self, listener: Callable[[bool], None]) -> None:
        if listener in self._state_listeners:
            self._state_listeners.remove(listener)

    def _notify_state(self, connected: bool) -> None:
        self.is_connected = connected
        for l in list(self._state_listeners):
            try:
                l(connected)
            except Exception as e:
                logger.error(f"Error in state listener: {e}")

    def connect(self, timeout: float = 3.0) -> bool:
        """Connects to the headphone via Bluetooth RFCOMM."""
        with self._lock:
            if self.is_connected and self.sock:
                return True

            s = None
            # Try specified channel first, then fallback to other common RFCOMM channels
            channels_to_try = [self.channel] + [c for c in range(1, 6) if c != self.channel]
            connected_channel = None

            for ch in channels_to_try:
                try:
                    logger.info(f"Connecting to {self.target_address} on RFCOMM channel {ch}...")
                    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
                    s.settimeout(timeout)
                    s.connect((self.target_address, ch))
                    connected_channel = ch
                    break
                except OSError as err:
                    if s:
                        try:
                            s.close()
                        except Exception:
                            pass
                    s = None
                    if err.errno == errno.EBUSY:  # Device or resource busy
                        logger.warning(f"RFCOMM channel {ch} is busy, waiting briefly...")
                        time.sleep(0.5)
                    else:
                        logger.debug(f"RFCOMM channel {ch} connect failed: {err}")

            if not s or not connected_channel:
                logger.warning(f"Could not open RFCOMM channel to {self.target_address}.")
                self._notify_state(False)
                return False

            self.channel = connected_channel
            self.sock = s
            self._running = True
            self.is_connected = True
            self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True, name="JLab-RFCOMM-Rx")
            self._rx_thread.start()
            logger.info(f"Bluetooth connection established on channel {connected_channel}.")

        # Notify state outside of lock to avoid recursive lock starvation
        self._notify_state(True)
        return True

    def disconnect(self) -> None:
        """Disconnects and tears down RFCOMM socket."""
        self._running = False
        with self._lock:
            if self.sock:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    self.sock.close()
                except Exception:
                    pass
                self.sock = None
            self.is_connected = False

        self._notify_state(False)
        logger.info("Disconnected from Bluetooth device.")

    def send_packet(self, packet: Union[RacePacket, JieLiPacket, bytes]) -> bool:
        """Sends a packet or raw bytes over the RFCOMM link."""
        with self._lock:
            if not self.sock or not self.is_connected:
                logger.warning("Cannot send packet: Not connected.")
                return False

            try:
                if isinstance(packet, bytes):
                    raw_bytes = packet
                else:
                    raw_bytes = packet.encode()
                logger.debug(f"TX -> {raw_bytes.hex().upper()} ({packet})")
                self.sock.sendall(raw_bytes)
                return True
            except Exception as e:
                logger.error(f"Error sending packet: {e}")
                self.disconnect()
                return False

    def _rx_loop(self) -> None:
        """Continuous background thread for receiving and decoding incoming packets."""
        rx_buffer = bytearray()
        while self._running:
            try:
                if not self.sock:
                    break
                data = self.sock.recv(1024)
                if not data:
                    logger.warning("Remote closed connection.")
                    break

                rx_buffer.extend(data)
                while len(rx_buffer) >= 6:
                    # Check if it starts with JieLi prefix (0xFE 0xDC 0xBA)
                    if rx_buffer.startswith(b"\xfe\xdc\xba"):
                        pkt, consumed = JieLiPacket.decode(bytes(rx_buffer))
                        if consumed > 0:
                            del rx_buffer[:consumed]
                        if pkt:
                            logger.debug(f"RX JieLi <- {pkt}")
                            for l in list(self._listeners):
                                try:
                                    l(pkt)
                                except Exception as e:
                                    logger.error(f"Error in packet listener: {e}")
                        else:
                            break
                    elif rx_buffer[0] == 0x05:  # RacePacket header
                        pkt, consumed = RacePacket.decode(bytes(rx_buffer))
                        if consumed > 0:
                            del rx_buffer[:consumed]
                        if pkt:
                            logger.debug(f"RX Race <- {pkt}")
                            for l in list(self._listeners):
                                try:
                                    l(pkt)
                                except Exception as e:
                                    logger.error(f"Error in packet listener: {e}")
                        else:
                            break
                    else:
                        # Drop unknown leading byte
                        del rx_buffer[0]
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    logger.error(f"Rx loop error: {e}")
                break

        self.disconnect()
