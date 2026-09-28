from dataclasses import dataclass, field
from typing import Optional

from .enums import WeightStatus


@dataclass
class MeasurementCell:
    cell_id: int
    weight: Optional[float] = None
    status: WeightStatus = WeightStatus.INVALID


@dataclass
class MeasurementResult:
    cells: list[MeasurementCell] = field(default_factory=list)
    stable: bool = False
    valid_cells: int = 0
    status: str = "FAILED"
