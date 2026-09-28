from pathlib import Path
import tempfile

from app.ai import AIRecognizer
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.models.enums import EventStatus, WeightStatus


class FailingAI(AIRecognizer):
    def recognize(self, image=None, regions=None):
        raise RuntimeError("simulated AI failure")


def build_service(tmp: str, ai=None):
    db = Database(str(Path(tmp) / "robustness.db"))
    db.initialize()
    mm = MeasurementManager(filter_window=3, stability_threshold=2.0, stability_samples=3)
    recognizer = ai or AIRecognizer()
    recognizer.load_model()
    return DetectionService(
        measurement_manager=mm,
        ai_recognizer=recognizer,
        database=db,
        tray_config_id="TRAY_DEFAULT",
        presence_threshold=100,
        removal_threshold=20,
    ), mm, db


def stable_samples(service, weights):
    event = None
    for _ in range(4):
        event = service.update(weights) or event
    return event


def main():
    # 1) Invalid/failed channels cannot become stable by reusing stale history.
    mm = MeasurementManager(filter_window=5, stability_threshold=2.0, stability_samples=3)
    good = {1: 300, 2: 180, 3: 250, 4: 100}
    for _ in range(3):
        mm.update(good)
    bad = mm.update({1: 300, 2: float("nan"), 3: 250, 4: 100})
    assert bad.stable is False
    assert bad.valid_cells == 3
    assert bad.status == "DEGRADED"
    assert bad.cells[1].status == WeightStatus.SENSOR_ERROR
    recovered = mm.update(good)
    assert recovered.stable is False, "recovered sensor must rebuild its stability history"

    # 2) A degraded sensor blocks automatic detection.
    with tempfile.TemporaryDirectory() as tmp:
        service, _, db = build_service(tmp)
        service.start()
        service.update({1: 300, 2: 180, 3: 250, 4: 100})
        service.update({1: 300, 2: "bad", 3: 250, 4: 100})
        for _ in range(5):
            service.update({1: 300, 2: "bad", 3: 250, 4: 100})
        assert service.get_state() in (DetectionService.TRAY_PRESENT, DetectionService.STABILIZING)
        assert db.get_events() == []

    # 3) Processing failures are recorded once and lock the same tray until removal.
    with tempfile.TemporaryDirectory() as tmp:
        service, _, db = build_service(tmp, FailingAI())
        service.start()
        weights = {1: 300, 2: 180, 3: 250, 4: 100}
        event = stable_samples(service, weights)
        assert event is not None
        assert event.status == EventStatus.FAILED
        assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL
        assert len(db.get_events()) == 1
        assert service.update(weights) is None
        assert len(db.get_events()) == 1
        for _ in range(5):
            service.update({1: 0, 2: 0, 3: 0, 4: 0})
        assert service.get_state() == DetectionService.WAITING

    # 4) Restarting monitoring clears stale measurement history.
    with tempfile.TemporaryDirectory() as tmp:
        service, mm, _ = build_service(tmp)
        service.start()
        for _ in range(3):
            mm.update({1: 300, 2: 180, 3: 250, 4: 100})
        assert mm.get_result().stable is True
        service.stop()
        service.start()
        assert mm.get_result().stable is False

    print("Software robustness test passed")
    print("- Invalid sensor data cannot produce a stable measurement")
    print("- Degraded measurements cannot trigger detection")
    print("- Processing failures are saved once and wait for tray removal")
    print("- Restart clears stale measurement history")


if __name__ == "__main__":
    main()
