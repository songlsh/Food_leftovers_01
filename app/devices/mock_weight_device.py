from __future__ import annotations

from .device_base import WeightDeviceBase


class MockWeightDevice(WeightDeviceBase):
    """Four-channel weight device used by V24 demos and tests."""

    name = "称重设备"
    mode = "MOCK"

    def __init__(self, cell_count: int = 4):
        self._weights = {i: 0.0 for i in range(1, cell_count + 1)}
        self._connected = False

    def connect(self) -> bool:
        self._connected = True
        return True

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def set_weights(self, weights: dict[int, float]) -> None:
        if not self._connected:
            raise RuntimeError("MockWeightDevice 未连接")
        self._weights = {int(k): float(v) for k, v in weights.items()}

    def read(self) -> dict[int, float]:
        if not self._connected:
            raise RuntimeError("MockWeightDevice 未连接")
        return dict(self._weights)
