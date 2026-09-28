from pathlib import Path


class MockCamera:
    """First-version mock camera.

    It creates a placeholder image file path so the rest of the
    application can test the camera workflow before real hardware
    is connected.
    """

    def __init__(self, image_dir: str = "images"):
        self.image_dir = Path(image_dir)

    def capture(self, event_id: str) -> str:
        self.image_dir.mkdir(parents=True, exist_ok=True)

        image_path = self.image_dir / f"{event_id}.jpg"

        # Valid tiny JPEG so the V25 UI can preview the mock image.
        import base64
        payload = (
            "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////2wBDAf//////////////////////////////////////////////////////////////////////////////////////wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAX/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIQAxAAAAF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABBQJ//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAwEBPwF//8QAFBEBAAAAAAAAAAAAAAAAAAAAAP/aAAgBAgEBPwF//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQAGPwJ//8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPyF//9k="
        )
        image_path.write_bytes(base64.b64decode(payload) + b"\nMOCK_CAMERA_IMAGE\n" + f"event_id={event_id}\n".encode("utf-8"))

        return str(image_path)
