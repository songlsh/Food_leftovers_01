from pathlib import Path

ROOT = Path(__file__).resolve().parent
UI = (ROOT / "app/ui/runtime_window.py").read_text()
FACTORY = (ROOT / "app/devices/factory.py").read_text()
MANAGER = (ROOT / "app/devices/device_manager.py").read_text()
WEIGHT = (ROOT / "app/devices/mock_weight_device.py").read_text()

for text in (
    "MockDeviceBundle",
    "device_manager",
    "weight_device",
    "camera_device",
    "设备模式",
    "get_info_map",
):
    assert text in UI, text

for text in ("set_weights", "read"):
    assert text in WEIGHT, text

for text in ("DeviceManager", "MockWeightDevice", "MockCameraDevice", "build_mock_devices"):
    assert text in FACTORY or text in MANAGER, text

print("V24 device UI contract test passed")
