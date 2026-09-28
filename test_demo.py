"""V25 一键演示：生成测试数据、打印统计、自动打开完整运行界面。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from app.ai import AIRecognizer
from app.config import seed_foods
from app.config.paths import BASE_DIR
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera
from app.statistics import StatisticsService

DB_PATH = BASE_DIR / "data" / "v25_demo.db"
TRAY_DB_PATH = BASE_DIR / "data" / "v25_demo_tray.db"
IMAGE_DIR = BASE_DIR / "images" / "v25_demo"


def _reset():
    DB_PATH.unlink(missing_ok=True)
    TRAY_DB_PATH.unlink(missing_ok=True)
    if IMAGE_DIR.exists():
        for p in IMAGE_DIR.glob("*"):
            if p.is_file():
                p.unlink()
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


def _build_service(db: Database) -> DetectionService:
    manager = MeasurementManager(filter_window=5, stability_threshold=2.0, stability_samples=3)
    ai = AIRecognizer()
    ai.load_model()
    return DetectionService(
        measurement_manager=manager,
        ai_recognizer=ai,
        database=db,
        camera=MockCamera(str(IMAGE_DIR)),
        tray_config_id="TRAY_DEFAULT",
        presence_threshold=100,
        removal_threshold=20,
    )


def _create_events(service: DetectionService) -> list:
    targets = [
        {1: 300, 2: 182, 3: 252, 4: 103},
        {1: 260, 2: 150, 3: 220, 4: 90},
        {1: 340, 2: 210, 3: 180, 4: 120},
        {1: 220, 2: 240, 3: 160, 4: 80},
        {1: 280, 2: 170, 3: 230, 4: 110},
    ]
    events = []
    for target in targets:
        event = None
        for _ in range(8):
            event = service.update(target) or event
        if event is None:
            raise RuntimeError("测试数据生成失败：没有触发 Event")
        events.append(event)
        for _ in range(8):
            service.update({1: 0, 2: 0, 3: 0, 4: 0})
        if service.get_state() != DetectionService.WAITING:
            raise RuntimeError("测试数据生成失败：状态机没有回到 WAITING")
    return events


def main() -> int:
    print("=" * 52)
    print("V25 一键测试演示")
    print("生成测试数据 → 校验 → 打印统计 → 打开完整运行界面")
    print("=" * 52)

    _reset()
    db = Database(str(DB_PATH))
    db.initialize()
    seed_foods(db)
    service = _build_service(db)
    events = _create_events(service)

    saved = db.get_events()
    assert len(saved) == 5
    assert all(event.status.value == "COMPLETED" for event in saved)

    statistics = StatisticsService(db)
    summary = statistics.get_summary()
    food_stats = statistics.get_food_statistics()
    daily_stats = statistics.get_daily_statistics()

    assert summary.event_count == 5
    assert summary.total_remaining_weight > 0
    assert summary.total_initial_weight > 0
    assert summary.total_consumed_weight is not None
    assert summary.consumption_rate is not None
    assert len(food_stats) == 4
    assert len(daily_stats) == 1

    print(f"\n测试数据库：{DB_PATH}")
    print(f"生成 Event：{len(events)} 条")
    for event in saved:
        full = db.get_event(event.event_id)
        total = sum(cell.net_weight or 0 for cell in (full.cells if full else []))
        print(f"  {event.event_id}  {event.timestamp:%Y-%m-%d %H:%M:%S}  {total:.2f}g")

    print("\n统计结果")
    print(f"  事件数量：{summary.event_count}")
    print(f"  总剩余重量：{summary.total_remaining_weight:.2f}g")
    print(f"  平均剩余重量：{summary.average_remaining_weight:.2f}g")
    print(f"  总初始重量：{summary.total_initial_weight:.2f}g")
    print(f"  总消耗量：{summary.total_consumed_weight:.2f}g")
    print(f"  剩余率：{summary.remaining_rate:.1%}")
    print(f"  消耗率：{summary.consumption_rate:.1%}")
    print("  食物统计：")
    for item in food_stats:
        print(f"    {item.food_name}: {item.total_remaining_weight:.2f}g / {item.count}格")
    print("  日期统计：")
    for item in daily_stats:
        print(f"    {item.date}: {item.event_count}条 / {item.total_remaining_weight:.2f}g")

    print("\n✓ V25 一键测试通过")
    if "--no-gui" in sys.argv:
        print("跳过 GUI 启动（--no-gui）")
        return 0

    print("正在打开完整运行界面……")
    subprocess.Popen([
        sys.executable,
        str(BASE_DIR / "main.py"),
        "--demo-ui",
        "--db", str(DB_PATH),
        "--tray-db", str(TRAY_DB_PATH),
        "--images", str(IMAGE_DIR),
    ], cwd=str(BASE_DIR))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
