import os

from app.config import TrayConfigManager
from app.models import TrayCellConfig, TrayConfig


DB_PATH = "data/test_tray_config.db"


def main():
    os.makedirs("data", exist_ok=True)

    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    manager = TrayConfigManager(DB_PATH)

    config = TrayConfig(
        tray_config_id="TRAY_A",
        name="标准四格托盘",
        description="第一版四格托盘配置",
        cell_count=4,
        enabled=True,
        cells=[
            TrayCellConfig(
                tray_config_id="TRAY_A",
                cell_id=1,
                weight_channel=1,
                image_region=[[0, 0], [320, 0], [320, 240], [0, 240]],
                tare_weight=50.0,
            ),
            TrayCellConfig(
                tray_config_id="TRAY_A",
                cell_id=2,
                weight_channel=2,
                image_region=[[320, 0], [640, 0], [640, 240], [320, 240]],
                tare_weight=50.0,
            ),
            TrayCellConfig(
                tray_config_id="TRAY_A",
                cell_id=3,
                weight_channel=3,
                image_region=[[0, 240], [320, 240], [320, 480], [0, 480]],
                tare_weight=45.0,
            ),
            TrayCellConfig(
                tray_config_id="TRAY_A",
                cell_id=4,
                weight_channel=4,
                image_region=[[320, 240], [640, 240], [640, 480], [320, 480]],
                tare_weight=45.0,
            ),
        ],
    )

    manager.save(config)
    loaded = manager.get("TRAY_A")

    assert loaded is not None
    assert loaded.tray_config_id == "TRAY_A"
    assert loaded.name == "标准四格托盘"
    assert loaded.cell_count == 4
    assert loaded.enabled is True
    assert len(loaded.cells) == 4

    assert loaded.cells[0].weight_channel == 1
    assert loaded.cells[0].tare_weight == 50.0
    assert loaded.cells[0].image_region == [
        [0, 0], [320, 0], [320, 240], [0, 240]
    ]

    print("TrayConfig test passed")
    print(f"Tray: {loaded.name}")
    print(f"Cell count: {loaded.cell_count}")

    for cell in loaded.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"channel={cell.weight_channel}, "
            f"tare={cell.tare_weight}g, "
            f"region={cell.image_region}"
        )


if __name__ == "__main__":
    main()
