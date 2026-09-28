from pathlib import Path

from app.ai import AIRecognizer
from app.config import TrayConfigManager
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera
from app.models.tray import TrayConfig, TrayCellConfig


def main():
    db_path = "data/test_auto_detection_workflow.db"
    tray_db_path = "data/auto_detection_workflow_tray.db"
    Path(db_path).unlink(missing_ok=True)
    Path(tray_db_path).unlink(missing_ok=True)

    db = Database(db_path)
    db.initialize()

    tray_manager = TrayConfigManager(tray_db_path)
    tray_manager.initialize()
    tray_manager.save(
        TrayConfig(
            tray_config_id="TRAY_WORKFLOW",
            name="完整自动检测测试托盘",
            cell_count=4,
            cells=[
                TrayCellConfig("TRAY_WORKFLOW", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 50),
                TrayCellConfig("TRAY_WORKFLOW", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 50),
                TrayCellConfig("TRAY_WORKFLOW", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 45),
                TrayCellConfig("TRAY_WORKFLOW", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 45),
            ],
        )
    )

    measurement = MeasurementManager(
        filter_window=5,
        stability_threshold=2.0,
        stability_samples=3,
    )
    config = tray_manager.get("TRAY_WORKFLOW")
    measurement.apply_tray_config(config)

    ai = AIRecognizer()
    ai.load_model()
    camera = MockCamera("images")

    service = DetectionService(
        measurement_manager=measurement,
        ai_recognizer=ai,
        database=db,
        camera=camera,
        tray_config_id="TRAY_WORKFLOW",
        tray_config_manager=tray_manager,
        presence_threshold=100,
        removal_threshold=20,
    )

    raw_present = {1: 300, 2: 182, 3: 252, 4: 103}
    event = None
    for _ in range(5):
        event = service.update(raw_present) or event

    assert event is not None
    assert event.status.value == "COMPLETED"
    assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL
    assert Path(event.image_path).exists()

    # The full chain must reach AI with the four configured regions.
    assert ai.last_regions is not None
    assert len(ai.last_regions) == 4
    assert set(ai.last_regions) == {1, 2, 3, 4}

    # The event must be persisted with all four cells.
    saved = db.get_event(event.event_id)
    assert saved is not None
    assert saved.status.value == "COMPLETED"
    assert len(saved.cells) == 4
    assert [c.food_id for c in saved.cells] == ["F001", "F002", "F003", "F004"]

    # The same tray cannot trigger another event while it remains present.
    assert service.update(raw_present) is None
    assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL

    # Remove tray and return to WAITING.
    for _ in range(6):
        service.update({1: 0, 2: 0, 3: 0, 4: 0})
    assert service.get_state() == DetectionService.WAITING

    events = db.get_events()
    assert len(events) == 1

    print("Automatic full detection workflow test passed")
    print(f"Event ID: {event.event_id}")
    print(f"Status: {event.status.value}")
    print(f"Saved cells: {len(saved.cells)}")
    print(f"AI regions: {len(ai.last_regions)}")
    print("State after removal: WAITING")


if __name__ == "__main__":
    main()
