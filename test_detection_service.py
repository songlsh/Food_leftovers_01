from pathlib import Path

from app.ai import AIRecognizer
from app.database import Database
from app.detection import MeasurementManager
from app.detection.detection_service import DetectionService
from app.models.enums import EventStatus


def main():
    Path("data/test_detection.db").unlink(missing_ok=True)
    db = Database("data/test_detection.db")
    db.initialize()

    measurement_manager = MeasurementManager(
        tare_weights={
            1: 0.0,
            2: 0.0,
            3: 0.0,
            4: 0.0,
        },
        filter_window=3,
        stability_threshold=2.0,
        stability_samples=3,
    )

    # Feed stable simulated weights.
    samples = [
        {1: 298.0, 2: 181.0, 3: 251.0, 4: 102.0},
        {1: 299.0, 2: 180.5, 3: 250.5, 4: 102.5},
        {1: 298.5, 2: 181.2, 3: 251.2, 4: 101.8},
    ]

    for sample in samples:
        measurement_manager.update(sample)

    ai = AIRecognizer()
    ai.load_model()

    service = DetectionService(
        measurement_manager=measurement_manager,
        ai_recognizer=ai,
        database=db,
        tray_config_id="TRAY_DEFAULT",
    )

    event = service.trigger()

    assert event is not None
    assert event.event_id == "EV000001"
    assert event.status == EventStatus.COMPLETED
    assert len(event.cells) == 4
    assert event.cells[0].food_id == "F001"
    assert event.cells[0].net_weight is not None

    saved = db.get_event("EV000001")

    assert saved is not None
    assert saved.status == EventStatus.COMPLETED

    print("Detection service test passed")
    print(f"Event ID: {event.event_id}")
    print(f"Status: {event.status.value}")
    print(f"Image: {event.image_path}")

    for cell in event.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"food_id={cell.food_id}, "
            f"net_weight={cell.net_weight}g, "
            f"confidence={cell.confidence:.2f}"
        )


if __name__ == "__main__":
    main()
