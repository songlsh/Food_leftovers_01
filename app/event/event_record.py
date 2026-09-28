from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

from app.models.event import Event

@dataclass
class EventRecordCell:
    cell_id: int
    food_id: Optional[str]
    net_weight: Optional[float]
    confidence: Optional[float]

@dataclass
class EventRecord:
    event_id: str
    time: str
    status: str
    image: Optional[str]
    total_weight: float
    cells: list[EventRecordCell]

    @classmethod
    def from_event(cls, event: Event):
        cells = [EventRecordCell(c.cell_id, c.food_id, c.net_weight, c.confidence) for c in event.cells]
        total = round(sum(c.net_weight or 0 for c in event.cells), 2)
        return cls(event.event_id or "", event.timestamp.strftime("%Y-%m-%d %H:%M:%S"), event.status.value, event.image_path, total, cells)

    def to_dict(self):
        return asdict(self)
