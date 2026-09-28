from app.detection import DetectionService


def main():
    expected = {
        "WAITING",
        "TRAY_PRESENT",
        "STABILIZING",
        "READY",
        "TRIGGERED",
        "PROCESSING",
        "COMPLETED",
        "PARTIAL",
        "FAILED",
        "WAITING_FOR_REMOVAL",
        "STOPPED",
    }
    actual = {
        DetectionService.WAITING,
        DetectionService.TRAY_PRESENT,
        DetectionService.STABILIZING,
        DetectionService.READY,
        DetectionService.TRIGGERED,
        DetectionService.PROCESSING,
        DetectionService.COMPLETED,
        DetectionService.PARTIAL,
        DetectionService.FAILED,
        DetectionService.WAITING_FOR_REMOVAL,
        DetectionService.STOPPED,
    }
    assert actual == expected
    print("Detection state machine definitions test passed")
    print("States: " + " -> ".join([
        "WAITING", "TRAY_PRESENT", "STABILIZING", "READY",
        "PROCESSING", "COMPLETED/PARTIAL/FAILED", "WAITING_FOR_REMOVAL", "WAITING"
    ]))


if __name__ == "__main__":
    main()
