import os

from app.config import TrayConfigManager
from app.models import TrayCellConfig, TrayConfig
from app.image_processing import ImageRegionProcessor

DB_PATH = "data/test_image_regions.db"
IMAGE_PATH = "images/test_regions.jpg"


def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("images", exist_ok=True)
    for path in (DB_PATH, IMAGE_PATH):
        if os.path.exists(path):
            os.remove(path)

    manager = TrayConfigManager(DB_PATH)
    config = TrayConfig(
        tray_config_id="TRAY_A",
        name="标准四格托盘",
        description="ImageRegion test",
        cell_count=4,
        enabled=True,
        cells=[
            TrayCellConfig("TRAY_A", 1, 1, [[0, 0], [320, 0], [320, 240], [0, 240]], 50.0),
            TrayCellConfig("TRAY_A", 2, 2, [[320, 0], [640, 0], [640, 240], [320, 240]], 50.0),
            TrayCellConfig("TRAY_A", 3, 3, [[0, 240], [320, 240], [320, 480], [0, 480]], 45.0),
            TrayCellConfig("TRAY_A", 4, 4, [[320, 240], [640, 240], [640, 480], [320, 480]], 45.0),
        ],
    )
    manager.save(config)
    loaded = manager.get("TRAY_A")
    open(IMAGE_PATH, "wb").write(b"MOCK_CAMERA_IMAGE")

    regions = ImageRegionProcessor().extract_regions(IMAGE_PATH, loaded)
    assert len(regions) == 4
    assert regions[1]["region"] == [[0, 0], [320, 0], [320, 240], [0, 240]]
    assert regions[4]["region"] == [[320, 240], [640, 240], [640, 480], [320, 480]]

    print("ImageRegion test passed")
    for cell_id, payload in regions.items():
        print(f"Cell {cell_id}: region={payload['region']}")


if __name__ == "__main__":
    main()
