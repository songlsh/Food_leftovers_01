"""V25 回归测试入口：运行核心业务、设备层与 UI 契约测试。"""
from __future__ import annotations
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

# Keep the regression suite deterministic even if a previous run or ZIP package
# contains old SQLite test artifacts. Individual tests also clean their own DBs.
TEST_DB_FILES = [
    "test_database.db", "test_detection.db", "test_food_seed.db",
    "test_history.db", "test_statistics.db",
]
for _name in TEST_DB_FILES:
    (ROOT / "data" / _name).unlink(missing_ok=True)
TESTS = [
    "test_database.py",
    "test_measurement.py",
    "test_tray_config.py",
    "test_tray_measurement.py",
    "test_ai_recognizer.py",
    "test_camera.py",
    "test_detection_service.py",
    "test_detection_state_machine.py",
    "test_auto_trigger.py",
    "test_auto_detection_workflow.py",
    "test_detection_camera.py",
    "test_detection_image_regions.py",
    "test_history.py",
    "test_statistics.py",
    "test_demo_runtime.py",
    "test_statistics_ui_contract.py",
    "test_runtime_ui_contract.py",
    "test_device_layer.py",
    "test_device_ui_contract.py",
    "test_v25_features.py",
    "test_food_config_ui_contract.py",
    "test_statistics_report.py",
    "test_v27_5_responsive_ui_contract.py",
    "test_software_robustness.py",
    "test_model_pipeline.py",
    "test_v30_menu_ai.py",
]

def main() -> int:
    print("=" * 52)
    print("V30 菜单约束 AI + V29 模型处理 + V28 软件稳定性回归测试")
    print("=" * 52)
    for name in TESTS:
        print(f"\n>>> {name}")
        result = subprocess.run([sys.executable, name], cwd=ROOT)
        if result.returncode != 0:
            print(f"\n✗ 测试失败：{name}")
            return result.returncode
    print("\n" + "=" * 52)
    print(f"✓ V30 菜单约束 AI + V29 模型处理 + V28 软件稳定性回归测试通过：{len(TESTS)}/{len(TESTS)}")
    print("=" * 52)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
