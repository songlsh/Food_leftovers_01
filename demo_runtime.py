"""Run the V18 automatic detection workflow with mock devices.

This is a safe local demonstration: no real hardware is required.
It creates one Event in the selected SQLite database and prints the
stored Event/cell data so the user can verify the complete write path.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app.ai import AIRecognizer
from app.config import TrayConfigManager
from app.config.paths import DEFAULT_DB, DEFAULT_TRAY_DB, DEFAULT_IMAGES
from app.database import Database
from app.detection import DetectionService, MeasurementManager
from app.devices import MockCamera, build_mock_devices
from app.models.tray import TrayConfig, TrayCellConfig


def build_service(db_path: str, tray_db_path: str, image_dir: str, camera=None) -> DetectionService:
    db = Database(db_path)
    db.initialize()

    tray_manager = TrayConfigManager(tray_db_path)
    tray_manager.initialize()
    tray_manager.save(
        TrayConfig(
            tray_config_id="TRAY_RUNTIME_DEMO",
            name="V18运行演示托盘",
            cell_count=4,
            cells=[
                TrayCellConfig("TRAY_RUNTIME_DEMO", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 0),
                TrayCellConfig("TRAY_RUNTIME_DEMO", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 0),
                TrayCellConfig("TRAY_RUNTIME_DEMO", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 0),
                TrayCellConfig("TRAY_RUNTIME_DEMO", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 0),
            ],
        )
    )

    measurement = MeasurementManager(
        filter_window=5,
        stability_threshold=2.0,
        stability_samples=3,
    )
    measurement.apply_tray_config(tray_manager.get("TRAY_RUNTIME_DEMO"))

    ai = AIRecognizer()
    ai.load_model()
    if camera is None:
        camera = build_mock_devices(image_dir).camera

    return DetectionService(
        measurement_manager=measurement,
        ai_recognizer=ai,
        database=db,
        camera=camera,
        tray_config_id="TRAY_RUNTIME_DEMO",
        tray_config_manager=tray_manager,
        presence_threshold=100,
        removal_threshold=20,
    )



def build_mock_device_bundle(image_dir: str):
    """Return the V24 replaceable-device bundle for runtime UI/demo use."""
    return build_mock_devices(image_dir)

def main() -> int:
    parser = argparse.ArgumentParser(description="V22自动检测完整链路演示（Mock设备）")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite数据库路径")
    parser.add_argument("--tray-db", default=str(DEFAULT_TRAY_DB), help="托盘配置数据库路径")
    parser.add_argument("--images", default=str(DEFAULT_IMAGES), help="Mock图片输出目录")
    parser.add_argument("--reset", action="store_true", help="运行前删除演示数据库")
    args, _unknown = parser.parse_known_args()

    if args.reset:
        for path in (args.db, args.tray_db):
            Path(path).unlink(missing_ok=True)

    service = build_service(args.db, args.tray_db, args.images)

    # Same stable weight is fed repeatedly to simulate a tray being placed
    # on the scale until the automatic trigger fires.
    raw_present = {1: 300, 2: 182, 3: 252, 4: 103}
    event = None
    for _ in range(5):
        event = service.update(raw_present) or event

    if event is None:
        raise RuntimeError("自动检测没有触发 Event")

    db = service.database
    saved = db.get_event(event.event_id)
    if saved is None:
        raise RuntimeError(f"Event {event.event_id} 未写入数据库")

    print("=== V18 自动检测运行演示 ===")
    print(f"Database: {Path(args.db).resolve()}")
    print(f"Event ID: {saved.event_id}")
    print(f"Status: {saved.status.value}")
    print(f"Timestamp: {saved.timestamp.isoformat(sep=' ')}")
    print(f"Image: {saved.image_path}")
    print(f"Cells: {len(saved.cells)}")
    for cell in saved.cells:
        print(
            f"  Cell {cell.cell_id}: food={cell.food_id}, "
            f"net={cell.net_weight:.2f}g, confidence={cell.confidence}"
        )

    print("\n数据库事件数量:", len(db.get_events()))
    print("状态机:", service.get_state())
    print("=== 完成：V18 → Event → SQLite 已打通 ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
