from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DeviceInfo:
    """Small, UI-safe description of a hardware/service device."""

    name: str
    mode: str
    status: str
    detail: str = ""


class DeviceBase:
    """Common lifecycle contract for replaceable devices.

    V24 deliberately keeps this contract small. Real serial/camera drivers can
    implement the same methods later without changing DetectionService or UI.
    """

    name = "Device"
    mode = "UNKNOWN"

    def connect(self) -> bool:
        return True

    def disconnect(self) -> None:
        return None

    def is_connected(self) -> bool:
        return True

    def get_info(self) -> DeviceInfo:
        return DeviceInfo(self.name, self.mode, "OK" if self.is_connected() else "DISCONNECTED")


class WeightDeviceBase(DeviceBase):
    name = "Weight"

    def read(self) -> dict[int, float]:
        raise NotImplementedError


class CameraDeviceBase(DeviceBase):
    name = "Camera"

    def capture(self, event_id: str) -> str:
        raise NotImplementedError
