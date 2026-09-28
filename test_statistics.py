from pathlib import Path

from app.ai import AIRecognizer
from app.config import seed_foods
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.statistics import StatisticsService


def create_event(service, samples):
    for sample in samples:
        service.measurement_manager.update(sample)

    return service.trigger()


def main():
    Path("data/test_statistics.db").unlink(missing_ok=True)
    db = Database("data/test_statistics.db")
    seed_foods(db)

    manager = MeasurementManager(
        filter_window=3,
        stability_threshold=2.0,
        stability_samples=3,
    )

    ai = AIRecognizer()
    ai.load_model()

    detection = DetectionService(
        measurement_manager=manager,
        ai_recognizer=ai,
        database=db,
        tray_config_id="TRAY_DEFAULT",
    )

    samples_1 = [
        {1: 100.0, 2: 200.0, 3: 300.0, 4: 400.0},
        {1: 101.0, 2: 199.0, 3: 301.0, 4: 399.0},
        {1: 100.0, 2: 200.0, 3: 300.0, 4: 400.0},
    ]

    samples_2 = [
        {1: 110.0, 2: 210.0, 3: 310.0, 4: 410.0},
        {1: 109.0, 2: 211.0, 3: 309.0, 4: 411.0},
        {1: 110.0, 2: 210.0, 3: 310.0, 4: 410.0},
    ]

    event_1 = create_event(detection, samples_1)

    manager.reset()

    event_2 = create_event(detection, samples_2)

    assert event_1.status.value == "COMPLETED"
    assert event_2.status.value == "COMPLETED"

    statistics = StatisticsService(db)

    summary = statistics.get_summary()

    assert summary.event_count == 2
    assert summary.total_remaining_weight > 0
    assert summary.average_remaining_weight > 0

    food_stats = statistics.get_food_statistics()

    assert len(food_stats) == 4
    assert all(item.count == 2 for item in food_stats)
    assert {item.food_name for item in food_stats} == {
        "米饭",
        "红烧肉",
        "青菜",
        "鸡蛋",
    }

    daily_stats = statistics.get_daily_statistics()

    assert len(daily_stats) == 1
    assert daily_stats[0].event_count == 2

    print("Statistics test passed")
    print(f"Event count: {summary.event_count}")
    print(
        "Total remaining: "
        f"{summary.total_remaining_weight}g"
    )
    print(
        "Average remaining: "
        f"{summary.average_remaining_weight}g"
    )

    print("Food statistics:")
    for item in food_stats:
        print(
            f"  {item.food_name}: "
            f"{item.count} events, "
            f"{item.total_remaining_weight}g"
        )

    print("Daily statistics:")
    for item in daily_stats:
        print(
            f"  {item.date}: "
            f"{item.event_count} events, "
            f"{item.total_remaining_weight}g"
        )


if __name__ == "__main__":
    main()
