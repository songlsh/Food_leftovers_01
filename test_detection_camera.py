import os

from app.ai import AIRecognizer
from app.database import Database
from app.devices import MockCamera
from app.detection import DetectionService, MeasurementManager


DB_PATH = "data/test_detection_camera.db"
IMAGE_DIR = "images"


def main():
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    database = Database(DB_PATH)
    database.initialize()

    measurement_manager = MeasurementManager()
    raw_data = {1: 300.0, 2: 182.0, 3: 252.0, 4: 103.0}

    # Fill the stability window.
    for _ in range(5):
        measurement_manager.update(raw_data)

    ai = AIRecognizer()
    ai.load_model()

    camera = MockCamera(IMAGE_DIR)

    service = DetectionService(
        measurement_manager=measurement_manager,
        ai_recognizer=ai,
        database=database,
        camera=camera,
        tray_config_id="TRAY_A",
    )

    event = service.trigger()

    assert event is not None
    assert event.status.value == "COMPLETED"
    assert event.image_path is not None
    assert os.path.exists(event.image_path)
    assert len(event.cells) == 4

    saved_event = database.get_event(event.event_id)
    assert saved_event is not None
    assert saved_event.image_path == event.image_path
    assert saved_event.status.value == "COMPLETED"
    assert len(saved_event.cells) == 4

    print("Detection + Camera integration test passed")
    print(f"Event ID: {event.event_id}")
    print(f"Status: {event.status.value}")
    print(f"Image: {event.image_path}")

    for cell in event.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"food_id={cell.food_id}, "
            f"net_weight={cell.net_weight}g, "
            f"confidence={cell.confidence}"
        )


if __name__ == "__main__":
    main()
