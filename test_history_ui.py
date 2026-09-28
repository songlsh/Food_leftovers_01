"""Non-visual tests for the V19 history UI data contract and date defaults."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.database import Database
from app.history import HistoryQuery, HistoryService
from app.models.enums import EventStatus, RecognitionStatus, WeightStatus
from app.models.event import Event, EventCell
from app.ui.history_window import HistoryWindow


def main():
    db_path = "data/test_v19_history_ui.db"
    Path(db_path).unlink(missing_ok=True)

    db = Database(db_path)
    db.initialize()
    db.save_event(Event(
        event_id="UI_EV000001",
        timestamp=datetime(2026, 9, 26, 10, 30),
        tray_config_id="TRAY_DEFAULT",
        image_path="images/UI_EV000001.jpg",
        status=EventStatus.COMPLETED,
        cells=[
            EventCell(cell_id=1, food_id="F001", net_weight=250.0, confidence=0.96,
                      weight_status=WeightStatus.OK, recognition_status=RecognitionStatus.OK),
            EventCell(cell_id=2, food_id="F002", net_weight=132.5, confidence=0.91,
                      weight_status=WeightStatus.OK, recognition_status=RecognitionStatus.OK),
        ],
    ))

    history = HistoryService(db)
    events = history.list_events(HistoryQuery(status=EventStatus.COMPLETED))
    assert events and events[0].event_id == "UI_EV000001"
    assert round(sum(c.net_weight or 0 for c in events[0].cells), 2) == 382.5

    app = QApplication.instance() or QApplication([])
    window = HistoryWindow(history)
    today = window.end_date.date()
    assert window.start_date.date() == today.addDays(-30)
    assert window.end_date.date() == today

    # Reset twice: the range must stay fixed instead of moving backward.
    window._reset_filters()
    first_start = window.start_date.date()
    first_end = window.end_date.date()
    window._reset_filters()
    assert window.start_date.date() == first_start
    assert window.end_date.date() == first_end

    print("V19 history UI data/date test passed")
    print(f"Events: {len(events)}")
    print(f"Total weight: {sum(c.net_weight or 0 for c in events[0].cells):.1f} g")
    print("Reset date range is idempotent")
    window.close()
    app.quit()


if __name__ == "__main__":
    main()
