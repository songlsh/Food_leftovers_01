from app.detection.measurement_manager import MeasurementManager
from app.models.enums import WeightStatus


def main():
    manager = MeasurementManager(
        tare_weights={
            1: 0.0,
            2: 0.0,
            3: 0.0,
            4: 0.0,
        },
        filter_window=5,
        stability_threshold=2.0,
        stability_samples=3,
    )

    samples = [
        {1: 298.0, 2: 181.0, 3: 251.0, 4: 102.0},
        {1: 299.0, 2: 180.5, 3: 250.5, 4: 102.5},
        {1: 298.5, 2: 181.2, 3: 251.2, 4: 101.8},
    ]

    result = None

    for sample in samples:
        result = manager.update(sample)

    assert result is not None
    assert result.stable is True
    assert result.valid_cells == 4
    assert result.status == "OK"

    for cell in result.cells:
        assert cell.status == WeightStatus.OK
        assert cell.weight is not None

    print("Measurement test passed")
    print(f"Stable: {result.stable}")
    print(f"Valid cells: {result.valid_cells}")
    print(f"Status: {result.status}")

    for cell in result.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"{cell.weight}g - {cell.status.value}"
        )


if __name__ == "__main__":
    main()
