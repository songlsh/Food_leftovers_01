from dataclasses import dataclass, field
from typing import Optional

from .enums import RecognitionStatus


@dataclass
class RecognitionCell:
    cell_id: int
    food_id: Optional[str] = None
    food_name: Optional[str] = None
    confidence: Optional[float] = None
    status: RecognitionStatus = RecognitionStatus.UNKNOWN
    result_type: str = "FOOD"  # FOOD / EMPTY / UNKNOWN


@dataclass
class RecognitionResult:
    cells: list[RecognitionCell] = field(default_factory=list)
    status: str = "FAILED"
