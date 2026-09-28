from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI = (ROOT / "app/ui/statistics_window.py").read_text()
MAIN = (ROOT / "main.py").read_text()
RUNTIME = (ROOT / "app/ui/runtime_window.py").read_text()

for text in (
    "StatisticsService",
    "StatisticsQuery",
    "开始日期",
    "结束日期",
    "总体统计",
    "按食物统计",
    "按日期统计",
    "_load_statistics",
):
    assert text in UI, text

assert "--statistics" in MAIN
assert "StatisticsWindow" in MAIN
assert "打开统计分析" in RUNTIME
print("V21 statistics UI contract test passed")
