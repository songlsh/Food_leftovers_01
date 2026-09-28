from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAIN = (ROOT / "main.py").read_text()
UI = (ROOT / "app/ui/runtime_window.py").read_text()

assert "RuntimeWindow" in MAIN and "--history" in MAIN and "--statistics" in MAIN and "--demo-ui" in MAIN
for text in (
    "开始监测",
    "停止监测",
    "模拟放入餐盘",
    "模拟取走餐盘",
    "打开历史记录",
    "打开统计分析",
    "称重设备",
    "摄像头",
    "AI 检测",
    "数据库",
    "当前总重量",
    "最近 Event",
    "DetectionService",
    "HistoryService",
    "QTimer",
    "_simulate_place",
    "_simulate_remove",
    "_load_latest_event",
):
    assert text in UI, text

print("V24 runtime UI contract test passed")
