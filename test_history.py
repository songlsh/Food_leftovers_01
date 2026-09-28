from datetime import datetime
from pathlib import Path

from app.database import Database
from app.history import HistoryQuery, HistoryService
from app.models.enums import EventStatus, RecognitionStatus, WeightStatus
from app.models.event import Event, EventCell


def main():
    Path("data/test_history.db").unlink(missing_ok=True)
    db = Database("data/test_history.db")
    db.initialize()

    events = [
        Event(
            event_id="EV000001",
            timestamp=datetime(2026, 9, 25, 10, 0, 0),
            tray_config_id="TRAY_DEFAULT",
            image_path="images/EV000001.jpg",
            status=EventStatus.COMPLETED,
            cells=[
                EventCell(
                    event_id="EV000001", cell_id=1, food_id="F001",
                    gross_weight=300.0, tare_weight=50.0, net_weight=250.0,
                    weight_status=WeightStatus.OK, confidence=0.96,
                    recognition_status=RecognitionStatus.OK,
                )
            ],
        ),
        Event(
            event_id="EV000002",
            timestamp=datetime(2026, 9, 25, 12, 0, 0),
            tray_config_id="TRAY_DEFAULT",
            image_path="images/EV000002.jpg",
            status=EventStatus.PARTIAL,
        ),
        Event(
            event_id="EV000003",
            timestamp=datetime(2026, 9, 26, 9, 0, 0),
            tray_config_id="TRAY_DEFAULT",
            image_path="images/EV000003.jpg",
            status=EventStatus.FAILED,
        ),
    ]

    for event in events:
        db.save_event(event)

    history = HistoryService(db)

    all_events = history.list_events()
    assert [event.event_id for event in all_events] == [
        "EV000003", "EV000002", "EV000001"
    ]

    completed = history.list_events(
        HistoryQuery(status=EventStatus.COMPLETED)
    )
    assert [event.event_id for event in completed] == ["EV000001"]
    assert len(completed[0].cells) == 1
    assert completed[0].cells[0].food_id == "F001"

    date_events = history.list_events(
        HistoryQuery(
            start_time=datetime(2026, 9, 25, 0, 0, 0),
            end_time=datetime(2026, 9, 25, 23, 59, 59),
        )
    )
    assert [event.event_id for event in date_events] == [
        "EV000002", "EV000001"
    ]

    single = history.get_event("EV000001")
    assert single is not None
    assert single.image_path == "images/EV000001.jpg"

    missing = history.get_event("EV999999")
    assert missing is None

    limited = history.list_events(HistoryQuery(limit=2))
    assert len(limited) == 2

    print("History service test passed")
    print(f"All events: {len(all_events)}")
    print(f"Completed events: {len(completed)}")
    print(f"2026-09-25 events: {len(date_events)}")
    print(f"Single event: {single.event_id}")


if __name__ == "__main__":
    main()
