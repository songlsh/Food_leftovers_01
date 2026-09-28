import json
import os
from datetime import date

from app.ai import DemoModelBackend, ModelFoodRecognizer
from app.config import DailyMenuProvider, TrayConfigManager
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera
from app.models import TrayCellConfig, TrayConfig
from app.models.enums import EventStatus, RecognitionStatus

DB_PATH = "data/test_v30_menu.db"
TRAY_DB_PATH = "data/test_v30_menu_tray.db"


def build_tray_config(manager):
    config = TrayConfig(
        tray_config_id="TRAY_V30",
        name="V30测试四格托盘",
        description="V30 menu constrained AI test",
        cell_count=4,
        enabled=True,
        cells=[
            TrayCellConfig("TRAY_V30", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 0.0),
            TrayCellConfig("TRAY_V30", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 0.0),
            TrayCellConfig("TRAY_V30", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 0.0),
            TrayCellConfig("TRAY_V30", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 0.0),
        ],
    )
    manager.save(config)


def main():
    os.makedirs("data", exist_ok=True)
    for path in (DB_PATH, TRAY_DB_PATH):
        if os.path.exists(path):
            os.remove(path)

    provider = DailyMenuProvider("config/weekly_menu.json")
    menu = provider.get_menu(date(2026, 9, 28))  # Monday
    assert menu.weekday == "monday"
    assert menu.food_ids() == ["F001", "F002", "F003", "F004"]

    # Candidate restriction: a prediction outside the menu must be forced into the menu.
    recognizer = ModelFoodRecognizer(
        DemoModelBackend(), confidence_threshold=0.80
    )
    recognizer.load_model()
    image = "images/v30_menu_test.jpg"
    os.makedirs("images", exist_ok=True)
    with open(image, "wb") as f:
        f.write(b"demo")

    regions = {i: {"cell_id": i, "region": [[0, 0], [10, 0], [10, 10], [0, 10]]} for i in range(1, 5)}
    result = recognizer.recognize(image=image, regions=regions, daily_menu=menu)
    assert result.status == "OK"
    assert all(cell.food_id in menu.food_ids() for cell in result.cells)

    # Use a one-item menu to prove the candidate space is actually restricted.
    from app.models.menu import DailyMenu, FoodClass
    one_food_menu = DailyMenu(
        date="2026-09-28",
        weekday="monday",
        foods=[FoodClass("F002", "红烧肉", "一份红烧肉")],
        version="test-1",
    )
    restricted = recognizer.recognize(image=image, regions=regions, daily_menu=one_food_menu)
    assert all(cell.food_id == "F002" for cell in restricted.cells)

    class FixedMenuProvider(DailyMenuProvider):
        def get_today_menu(self):
            return menu

    db = Database(DB_PATH)
    db.initialize()
    tray_manager = TrayConfigManager(TRAY_DB_PATH)
    build_tray_config(tray_manager)

    mm = MeasurementManager()
    for _ in range(5):
        mm.update({1: 300, 2: 182, 3: 252, 4: 103})

    service = DetectionService(
        measurement_manager=mm,
        ai_recognizer=recognizer,
        database=db,
        camera=MockCamera("images"),
        tray_config_id="TRAY_V30",
        tray_config_manager=tray_manager,
        daily_menu_provider=FixedMenuProvider("config/weekly_menu.json"),
    )

    event = service.trigger()
    assert event is not None
    assert event.status == EventStatus.COMPLETED
    assert event.menu_date == menu.date
    assert event.menu_weekday == menu.weekday
    assert event.menu_version == menu.version
    snapshot = json.loads(event.menu_snapshot)
    assert [item["food_id"] for item in snapshot["foods"]] == menu.food_ids()
    assert all(cell.food_id in menu.food_ids() for cell in event.cells)

    saved = db.get_event(event.event_id)
    assert saved is not None
    assert saved.menu_snapshot == event.menu_snapshot
    assert all(cell.recognition_result_type == "FOOD" for cell in saved.cells)

    print("V30 menu-constrained AI test passed")
    print(f"Menu: {menu.date} / {menu.weekday} / {len(menu.foods)} foods")
    print("Candidate restriction: OK")
    print(f"Event: {event.event_id} / {event.status.value}")
    print("Menu snapshot persistence: OK")


if __name__ == "__main__":
    main()
