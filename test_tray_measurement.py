from app.detection import MeasurementManager
from app.models.tray import TrayCellConfig, TrayConfig

def main():
    tray = TrayConfig(
        tray_config_id="TRAY_A", name="标准四格托盘", cell_count=4,
        cells=[TrayCellConfig("TRAY_A", 1, 1, tare_weight=50.0),
               TrayCellConfig("TRAY_A", 2, 2, tare_weight=50.0),
               TrayCellConfig("TRAY_A", 3, 3, tare_weight=45.0),
               TrayCellConfig("TRAY_A", 4, 4, tare_weight=45.0)])
    manager = MeasurementManager(filter_window=5, stability_threshold=2.0, stability_samples=3, tray_config=tray)
    result = None
    for _ in range(3): result = manager.update({1:300.0,2:182.0,3:252.0,4:103.0})
    assert result.status == "OK" and result.stable is True and result.valid_cells == 4
    expected={1:250.0,2:132.0,3:207.0,4:58.0}
    for cell in result.cells:
        assert cell.weight == expected[cell.cell_id]
        print(f"Cell {cell.cell_id}: net={cell.weight:.1f}g - {cell.status.value}")
    print("TrayConfig + MeasurementManager integration test passed")
if __name__ == "__main__": main()
