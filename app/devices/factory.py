from __future__ import annotations

from dataclasses import dataclass

from .device_manager import DeviceManager
from .mock_camera_device import MockCameraDevice
from .mock_weight_device import MockWeightDevice


@dataclass
class MockDeviceBundle:
    weight: MockWeightDevice
    camera: MockCameraDevice
    manager: DeviceManager


def build_mock_devices(image_dir: str) -> MockDeviceBundle:
    weight = MockWeightDevice(4)
    camera = MockCameraDevice(image_dir)
    manager = DeviceManager([weight, camera])
    manager.connect_all()
    return MockDeviceBundle(weight=weight, camera=camera, manager=manager)
