from app.esp32.camera_client import ESP32CameraClient
r=ESP32CameraClient().capture()
assert r["status"]=="IMAGE_READY"
print("ESP32 camera protocol test passed")
