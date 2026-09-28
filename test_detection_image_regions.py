import os

from app.ai import AIRecognizer
from app.config import TrayConfigManager
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera
from app.models import TrayCellConfig, TrayConfig
from app.models.enums import EventStatus

DB_PATH = "data/test_detection_image_regions.db"
TRAY_DB_PATH = "data/test_detection_image_regions_tray.db"


def build_tray_config(manager):
    config = TrayConfig(
        tray_config_id="TRAY_A",
        name="标准四格托盘",
        description="Detection ImageRegion test",
        cell_count=4,
        enabled=True,
        cells=[
            TrayCellConfig("TRAY_A", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 50.0),
            TrayCellConfig("TRAY_A", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 50.0),
            TrayCellConfig("TRAY_A", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 45.0),
            TrayCellConfig("TRAY_A", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 45.0),
        ],
    )
    manager.save(config)


def main():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    if os.path.exists(TRAY_DB_PATH):
        os.remove(TRAY_DB_PATH)

    db = Database(DB_PATH)
    db.initialize()

    tray_manager = TrayConfigManager(TRAY_DB_PATH)
    build_tray_config(tray_manager)

    mm = MeasurementManager()
    for _ in range(5):
        mm.update({1: 300, 2: 182, 3: 252, 4: 103})

    ai = AIRecognizer()
    ai.load_model()
    camera = MockCamera()

    service = DetectionService(
        measurement_manager=mm,
        ai_recognizer=ai,
        database=db,
        camera=camera,
        tray_config_id="TRAY_A",
        tray_config_manager=tray_manager,
    )

    event = service.trigger()

    assert event is not None
    assert event.status == EventStatus.COMPLETED
    assert len(event.cells) == 4
    assert ai.last_regions is not None
    assert len(ai.last_regions) == 4
    assert ai.last_regions[1]["region"] == [[0, 0], [320, 0], [320, 240], [0, 240]]
    assert ai.last_regions[4]["region"] == [[320, 240], [640, 240], [640, 480], [320, 480]]

    print("Detection + ImageRegion integration test passed")
    print(f"Event ID: {event.event_id}")
    print(f"Status: {event.status.value}")
    for cell in event.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"food_id={cell.food_id}, "
            f"region={ai.last_regions[cell.cell_id]['region']}"
        )


if __name__ == "__main__":
    main()
