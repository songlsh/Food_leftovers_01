from pathlib import Path
import tempfile

from demo_runtime import build_service


def main():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "runtime.db"
        tray_db = root / "tray.db"
        images = root / "images"

        service = build_service(str(db_path), str(tray_db), str(images))
        raw_present = {1: 300, 2: 182, 3: 252, 4: 103}
        event = None
        for _ in range(5):
            event = service.update(raw_present) or event

        assert event is not None
        assert event.status.value == "COMPLETED"
        saved = service.database.get_event(event.event_id)
        assert saved is not None
        assert len(saved.cells) == 4
        assert [c.food_id for c in saved.cells] == ["F001", "F002", "F003", "F004"]
        assert Path(saved.image_path).exists()
        assert len(service.database.get_events()) == 1

    print("Runtime demo test passed")
    print("V18 -> DetectionService -> Event -> SQLite -> readback: OK")


if __name__ == "__main__":
    main()
