import os

from app.devices import MockCamera


IMAGE_DIR = "images"
EVENT_ID = "EV000001"


def main():
    camera = MockCamera(IMAGE_DIR)

    image_path = camera.capture(EVENT_ID)

    assert os.path.exists(image_path)
    assert image_path.endswith("EV000001.jpg")

    with open(image_path, "rb") as f:
        content = f.read()

    assert b"MOCK_CAMERA_IMAGE" in content
    assert b"event_id=EV000001" in content

    print("Camera test passed")
    print(f"Image path: {image_path}")
    print("Mock image file created successfully")


if __name__ == "__main__":
    main()
