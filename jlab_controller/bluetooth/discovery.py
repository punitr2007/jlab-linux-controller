"""Bluetooth device discovery and BlueZ integration for JLab devices."""

import logging
from typing import Dict, List, Optional
import dbus

logger = logging.getLogger(__name__)

class JLabDeviceInfo:
    def __init__(
        self,
        address: str,
        name: str,
        connected: bool = False,
        battery: Optional[int] = None,
        modalias: Optional[str] = None,
        uuids: Optional[List[str]] = None,
    ):
        self.address = address
        self.name = name
        self.connected = connected
        self.battery = battery
        self.modalias = modalias or ""
        self.uuids = uuids or []

    @property
    def is_airoha(self) -> bool:
        return "05D6" in self.modalias.upper() or "05D6" in self.modalias

    def __repr__(self) -> str:
        return f"<JLabDevice {self.name} [{self.address}] connected={self.connected} battery={self.battery}%>"

class BluetoothScanner:
    """Discovers paired and connected Bluetooth devices using BlueZ D-Bus."""

    @staticmethod
    def get_paired_jlab_devices() -> List[JLabDeviceInfo]:
        """Returns all paired JLab devices found in BlueZ."""
        devices: List[JLabDeviceInfo] = []
        try:
            bus = dbus.SystemBus()
            manager = dbus.Interface(bus.get_object("org.bluez", "/"), "org.freedesktop.DBus.ObjectManager")
            objects = manager.GetManagedObjects()

            for path, interfaces in objects.items():
                if "org.bluez.Device1" in interfaces:
                    dev_props = interfaces["org.bluez.Device1"]
                    name = str(dev_props.get("Name", dev_props.get("Alias", "Unknown")))
                    addr = str(dev_props.get("Address", ""))
                    connected = bool(dev_props.get("Connected", False))
                    modalias = str(dev_props.get("Modalias", ""))
                    uuids = [str(u) for u in dev_props.get("UUIDs", [])]

                    # Battery interface
                    battery = None
                    if "org.bluez.Battery1" in interfaces:
                        battery = int(interfaces["org.bluez.Battery1"].get("Percentage", 0))

                    # Filter for JLab devices
                    is_jlab = (
                        "jlab" in name.lower()
                        or "jbuds" in name.lower()
                        or "epic" in name.lower()
                        or "05D6" in modalias
                    )

                    if is_jlab or connected:
                        device_info = JLabDeviceInfo(
                            address=addr,
                            name=name,
                            connected=connected,
                            battery=battery,
                            modalias=modalias,
                            uuids=uuids,
                        )
                        if is_jlab:
                            devices.insert(0, device_info)
                        else:
                            devices.append(device_info)

        except Exception as e:
            logger.error(f"Error scanning BlueZ devices: {e}")

        return devices
