from collections import deque
import math
from typing import Dict, Optional

from app.models.enums import WeightStatus
from app.models.measurement import MeasurementCell, MeasurementResult
from app.models.tray import TrayConfig


class MeasurementManager:
    """Convert raw multi-channel weights into stable net-weight measurements."""

    def __init__(self, cell_channels: Optional[Dict[int, int]] = None,
                 tare_weights: Optional[Dict[int, float]] = None,
                 filter_window: int = 5, stability_threshold: float = 2.0,
                 stability_samples: int = 3, tray_config: Optional[TrayConfig] = None):
        self.filter_window = max(1, int(filter_window))
        self.stability_threshold = float(stability_threshold)
        self.stability_samples = max(1, int(stability_samples))
        if not math.isfinite(self.stability_threshold) or self.stability_threshold < 0:
            raise ValueError("stability_threshold must be a finite non-negative number")
        self.cell_channels = cell_channels or {1: 1, 2: 2, 3: 3, 4: 4}
        self.tare_weights = tare_weights or {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
        self._reset_history()
        self._result = MeasurementResult()
        if tray_config is not None:
            self.apply_tray_config(tray_config)

    def apply_tray_config(self, tray_config: TrayConfig):
        if not tray_config.enabled:
            raise ValueError(f"Tray config is disabled: {tray_config.tray_config_id}")
        if tray_config.cell_count <= 0:
            raise ValueError("Tray config cell_count must be greater than 0")
        channels, tares, seen = {}, {}, set()
        for cell in tray_config.cells:
            if cell.cell_id in channels:
                raise ValueError(f"Duplicate cell_id: {cell.cell_id}")
            if cell.weight_channel in seen:
                raise ValueError(f"Duplicate weight_channel: {cell.weight_channel}")
            if cell.weight_channel <= 0:
                raise ValueError(f"Invalid weight_channel: {cell.weight_channel}")
            if cell.tare_weight < 0:
                raise ValueError(f"Invalid tare_weight for cell {cell.cell_id}")
            channels[cell.cell_id] = cell.weight_channel
            tares[cell.cell_id] = float(cell.tare_weight)
            seen.add(cell.weight_channel)
        if len(channels) != tray_config.cell_count:
            raise ValueError(f"Tray config expects {tray_config.cell_count} cells, but received {len(channels)}")
        self.cell_channels, self.tare_weights = channels, tares
        self.reset()

    def update(self, raw_data: Dict[int, float]) -> MeasurementResult:
        cells = []
        for cell_id, channel in self.cell_channels.items():
            raw_weight = raw_data.get(channel) if isinstance(raw_data, dict) else None
            if not self._is_valid_raw_weight(raw_weight):
                # A failed channel must not keep stale samples from making the
                # whole tray appear stable after the sensor recovers.
                self._history[cell_id].clear()
                cells.append(MeasurementCell(cell_id, None, WeightStatus.SENSOR_ERROR))
                continue
            net_weight = max(0.0, float(raw_weight) - self.tare_weights.get(cell_id, 0.0))
            self._history[cell_id].append(net_weight)
            filtered = sum(self._history[cell_id]) / len(self._history[cell_id])
            cells.append(MeasurementCell(cell_id, round(filtered, 2), WeightStatus.OK))
        valid_cells = sum(c.status == WeightStatus.OK for c in cells)
        stable = self._is_stable()
        if valid_cells == 0:
            status = "FAILED"
        elif valid_cells < len(self.cell_channels):
            status = "DEGRADED"
        elif stable:
            status = "OK"
        else:
            status = "UNSTABLE"
        self._result = MeasurementResult(cells, stable, valid_cells, status)
        return self._result

    def get_result(self): return self._result
    def is_stable(self): return self._is_stable()
    def reset(self):
        self._reset_history()
        self._result = MeasurementResult()

    def _reset_history(self):
        self._history = {cell_id: deque(maxlen=self.filter_window) for cell_id in self.cell_channels}

    def _is_stable(self):
        histories = [h for h in self._history.values() if len(h) >= self.stability_samples]
        if len(histories) != len(self.cell_channels): return False
        return all(max(list(h)[-self.stability_samples:]) - min(list(h)[-self.stability_samples:]) <= self.stability_threshold for h in histories)

    @staticmethod
    def _is_valid_raw_weight(value):
        if value is None or isinstance(value, bool):
            return False
        try:
            value = float(value)
        except (TypeError, ValueError):
            return False
        return math.isfinite(value) and value >= 0
