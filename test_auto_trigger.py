from pathlib import Path

from app.ai import AIRecognizer
from app.config import TrayConfigManager
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera


def main():
    db_path = "data/test_auto_trigger.db"
    Path(db_path).unlink(missing_ok=True)
    Path("data/auto_trigger_tray.db").unlink(missing_ok=True)

    db = Database(db_path)
    db.initialize()

    tray_manager = TrayConfigManager("data/auto_trigger_tray.db")
    tray_manager.initialize()

    from app.models.tray import TrayConfig, TrayCellConfig
    tray_manager.save(
        TrayConfig(
            tray_config_id="TRAY_AUTO",
            name="自动触发测试托盘",
            cell_count=4,
            cells=[
                TrayCellConfig("TRAY_AUTO", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 50),
                TrayCellConfig("TRAY_AUTO", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 50),
                TrayCellConfig("TRAY_AUTO", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 45),
                TrayCellConfig("TRAY_AUTO", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 45),
            ],
        )
    )

    mm = MeasurementManager(filter_window=5, stability_threshold=2.0, stability_samples=3)
    config = tray_manager.get("TRAY_AUTO")
    mm.apply_tray_config(config)

    ai = AIRecognizer()
    ai.load_model()
    camera = MockCamera("images")

    service = DetectionService(
        measurement_manager=mm,
        ai_recognizer=ai,
        database=db,
        camera=camera,
        tray_config_id="TRAY_AUTO",
        tray_config_manager=tray_manager,
        presence_threshold=100,
        removal_threshold=20,
    )

    raw_present = {1: 300, 2: 182, 3: 252, 4: 103}
    event = None
    for _ in range(5):
        event = service.update(raw_present) or event

    assert event is not None, "Automatic trigger did not create an event"
    assert event.status.value == "COMPLETED"
    assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL

    # The same tray must not create another event while it remains present.
    assert service.update(raw_present) is None
    assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL

    # Removing the tray returns the service to WAITING.
    for _ in range(6):
        service.update({1: 0, 2: 0, 3: 0, 4: 0})
    assert service.get_state() == DetectionService.WAITING

    print("Automatic trigger test passed")
    print(f"Event ID: {event.event_id}")
    print(f"Status: {event.status.value}")
    print("State after removal: WAITING")


if __name__ == "__main__":
    main()
