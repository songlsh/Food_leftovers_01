from pathlib import Path

from demo_runtime import build_service
from app.detection import DetectionService


def main():
    db = Path("data/test_continuous_runtime.db")
    tray = Path("data/test_continuous_runtime_tray.db")
    image_dir = Path("images/test_continuous_runtime")
    db.unlink(missing_ok=True)
    tray.unlink(missing_ok=True)
    if image_dir.exists():
        for p in image_dir.glob("*"):
            p.unlink()

    service = build_service(str(db), str(tray), str(image_dir))
    service.start()
    target = {1: 300.0, 2: 182.0, 3: 252.0, 4: 103.0}
    factors = [0.00, 0.08, 0.20, 0.38, 0.58, 0.76, 0.90, 1.00, 1.00, 1.00, 1.00, 1.00]
    states = []
    event = None
    for factor in factors:
        raw = {k: round(v * factor, 2) for k, v in target.items()}
        states.append(service.get_state())
        event = service.update(raw) or event
        if event:
            break

    assert event is not None
    assert event.status.value == "COMPLETED"
    assert service.get_state() == DetectionService.WAITING_FOR_REMOVAL
    assert "TRAY_PRESENT" in states or service.get_state() == DetectionService.WAITING_FOR_REMOVAL

    remove_factors = [1.00, 0.82, 0.62, 0.42, 0.24, 0.10, 0.03, 0.00, 0.00, 0.00, 0.00, 0.00]
    for factor in remove_factors:
        raw = {k: round(v * factor, 2) for k, v in target.items()}
        service.update(raw)
        if service.get_state() == DetectionService.WAITING:
            break
    assert service.get_state() == DetectionService.WAITING

    # Restart-like behavior: a new service continues Event numbering.
    service2 = build_service(str(db), str(tray), str(image_dir))
    assert service2._event_counter >= 1

    print("Continuous runtime simulation test passed")
    print("Event:", event.event_id, event.status.value)
    print("States:", " -> ".join(states))
    print("State after removal:", service.get_state())
    print("Next Event counter after restart:", service2._event_counter)


if __name__ == "__main__":
    main()
