from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .enums import EventStatus, RecognitionStatus, WeightStatus


@dataclass
class EventCell:
    event_cell_id: Optional[str] = None
    event_id: Optional[str] = None
    cell_id: int = 0
    food_id: Optional[str] = None
    gross_weight: Optional[float] = None
    tare_weight: Optional[float] = None
    net_weight: Optional[float] = None
    initial_weight: Optional[float] = None
    weight_status: WeightStatus = WeightStatus.INVALID
    confidence: Optional[float] = None
    recognition_status: RecognitionStatus = RecognitionStatus.UNKNOWN
    recognition_result_type: str = "FOOD"


@dataclass
class Event:
    event_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    tray_config_id: Optional[str] = None
    image_path: Optional[str] = None
    status: EventStatus = EventStatus.CREATED
    error_message: Optional[str] = None
    menu_date: Optional[str] = None
    menu_weekday: Optional[str] = None
    menu_version: Optional[str] = None
    menu_snapshot: Optional[str] = None
    cells: list[EventCell] = field(default_factory=list)
