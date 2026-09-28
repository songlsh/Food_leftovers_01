from __future__ import annotations
import argparse
from pathlib import Path
from app.database import Database
from app.config.paths import DEFAULT_DB, DEFAULT_TRAY_DB, DEFAULT_IMAGES

def main():
    parser=argparse.ArgumentParser(description="剩菜检测系统 V24")
    parser.add_argument("--demo",action="store_true",help="运行自动检测命令行演示")
    parser.add_argument("--history",action="store_true",help="直接打开历史记录窗口")
    parser.add_argument("--statistics",action="store_true",help="直接打开统计分析窗口")
    parser.add_argument("--demo-ui",action="store_true",help="打开完整运行演示界面")
    parser.add_argument("--db",default=None,help="SQLite数据库路径")
    parser.add_argument("--tray-db",default=None,help="托盘配置数据库路径")
    parser.add_argument("--images",default=None,help="Mock图片输出目录")
    args=parser.parse_args()
    if args.demo:
        from demo_runtime import main as demo_main
        return demo_main()
    from PySide6.QtWidgets import QApplication
    from app.history import HistoryService
    db_path=Path(args.db).expanduser().resolve() if args.db else DEFAULT_DB
    tray_db_path=Path(args.tray_db).expanduser().resolve() if args.tray_db else DEFAULT_TRAY_DB
    image_dir=Path(args.images).expanduser().resolve() if args.images else DEFAULT_IMAGES
    db_path.parent.mkdir(parents=True,exist_ok=True); tray_db_path.parent.mkdir(parents=True,exist_ok=True); image_dir.mkdir(parents=True,exist_ok=True)
    database=Database(str(db_path)); database.initialize()
    app=QApplication([])
    if args.history:
        from app.ui.history_window import HistoryWindow
        window=HistoryWindow(HistoryService(database)); window.show(); return app.exec()
    if args.statistics:
        from app.statistics import StatisticsService
        from app.ui.statistics_window import StatisticsWindow
        window=StatisticsWindow(StatisticsService(database)); window.show(); return app.exec()
    from demo_runtime import build_service, build_mock_device_bundle
    from app.ui.runtime_window import RuntimeWindow
    devices=build_mock_device_bundle(str(image_dir)); service=build_service(str(db_path),str(tray_db_path),str(image_dir),camera=devices.camera); window=RuntimeWindow(service,HistoryService(database),db_path,devices); window.show(); return app.exec()
if __name__=="__main__": raise SystemExit(main())
