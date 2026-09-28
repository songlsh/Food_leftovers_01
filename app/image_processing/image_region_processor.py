from pathlib import Path
from typing import Any


class ImageRegionProcessor:
    """Map configured tray image regions to individual cell inputs.

    v13 intentionally keeps the image operation lightweight: the MockCamera
    does not create a real image yet, so this layer produces validated region
    descriptors. A real OpenCV implementation can later replace the payload
    with actual cropped image arrays without changing DetectionService/AI APIs.
    """

    def extract_regions(self, image_path: str, tray_config: Any) -> dict[int, dict]:
        if not image_path:
            raise ValueError("image_path is required")
        if not Path(image_path).exists():
            raise FileNotFoundError(image_path)
        if tray_config is None:
            raise ValueError("tray_config is required")

        regions = {}
        for cell in tray_config.cells:
            if cell.image_region is None:
                raise ValueError(
                    f"Cell {cell.cell_id} has no image_region"
                )
            regions[cell.cell_id] = {
                "image_path": image_path,
                "cell_id": cell.cell_id,
                "region": cell.image_region,
            }

        return regions
