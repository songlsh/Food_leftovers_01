from pathlib import Path

from app.database import Database
from app.models.enums import EventStatus
from app.models.event import Event


def main():
    Path("data/test_database.db").unlink(missing_ok=True)
    db = Database("data/test_database.db")
    db.initialize()

    event = Event(
        event_id="EV000001",
        status=EventStatus.COMPLETED,
    )

    db.save_event(event)

    result = db.get_event("EV000001")

    if result is None:
        raise RuntimeError("Database test failed")

    print("Database test passed")
    print(f"Event ID: {result.event_id}")
    print(f"Status: {result.status.value}")


if __name__ == "__main__":
    main()
