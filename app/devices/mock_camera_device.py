from __future__ import annotations

from .camera import MockCamera
from .device_base import CameraDeviceBase


class MockCameraDevice(CameraDeviceBase):
    """Device-contract wrapper around the existing MockCamera."""

    name = "摄像头"
    mode = "MOCK"

    def __init__(self, image_dir: str = "images"):
        self._camera = MockCamera(image_dir)
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def capture(self, event_id: str) -> str:
        if not self._connected:
            raise RuntimeError("MockCameraDevice 未连接")
        return self._camera.capture(event_id)
