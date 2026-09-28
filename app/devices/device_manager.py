from __future__ import annotations

from typing import Iterable

from .device_base import DeviceBase, DeviceInfo


class DeviceManager:
    """Owns device lifecycle and exposes a stable status snapshot to the UI."""

    def __init__(self, devices: Iterable[DeviceBase] = ()):
        self.devices = list(devices)

    def connect_all(self) -> bool:
        ok = True
        for device in self.devices:
            try:
                ok = bool(device.connect()) and ok
            except Exception:
                ok = False
        return ok

    def disconnect_all(self) -> None:
        for device in self.devices:
            try:
                device.disconnect()
            except Exception:
                pass

    def get_info(self) -> list[DeviceInfo]:
        result = []
        for device in self.devices:
            try:
                result.append(device.get_info())
            except Exception as exc:
                result.append(DeviceInfo(device.name, device.mode, "ERROR", str(exc)))
        return result

    def get_info_map(self) -> dict[str, DeviceInfo]:
        return {info.name: info for info in self.get_info()}
