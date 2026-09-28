from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.database import Database
from app.models.enums import EventStatus
from app.models.event import Event


@dataclass
class HistoryQuery:
    """Simple filters for historical detection records."""

    event_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[EventStatus] = None
    tray_config_id: Optional[str] = None
    limit: Optional[int] = None


class HistoryService:
    """Read historical Event records without changing stored data."""

    def __init__(self, database: Database):
        self.database = database

    def list_events(self, query: Optional[HistoryQuery] = None) -> list[Event]:
        query = query or HistoryQuery()

        filters = {
            "event_id": query.event_id,
            "start_time": query.start_time,
            "end_time": query.end_time,
            "status": query.status.value if isinstance(query.status, EventStatus) else query.status,
            "tray_config_id": query.tray_config_id,
            "limit": query.limit,
        }

        summaries = self.database.get_events(filters)
        result = []
        for summary in summaries:
            event = self.database.get_event(summary.event_id)
            if event is not None:
                result.append(event)
        return result

    def get_event(self, event_id: str) -> Optional[Event]:
        if not event_id:
            return None
        return self.database.get_event(event_id)
