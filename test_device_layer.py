from pathlib import Path
import tempfile

from app.devices import DeviceManager, MockCameraDevice, MockWeightDevice, build_mock_devices

with tempfile.TemporaryDirectory() as tmp:
    bundle = build_mock_devices(tmp)
    info = bundle.manager.get_info_map()
    assert info["称重设备"].mode == "MOCK"
    assert info["称重设备"].status == "OK"
    assert info["摄像头"].mode == "MOCK"
    assert info["摄像头"].status == "OK"

    bundle.weight.set_weights({1: 10, 2: 20, 3: 30, 4: 40})
    assert bundle.weight.read() == {1: 10.0, 2: 20.0, 3: 30.0, 4: 40.0}

    image = bundle.camera.capture("EVV24TEST")
    assert Path(image).exists()

    bundle.manager.disconnect_all()
    assert all(item.status == "DISCONNECTED" for item in bundle.manager.get_info())
    bundle.manager.connect_all()
    assert all(item.status == "OK" for item in bundle.manager.get_info())

print("V24 device layer test passed")
print("Weight: MOCK / OK")
print("Camera: MOCK / OK")
print("Lifecycle: connect -> disconnect -> reconnect / OK")
