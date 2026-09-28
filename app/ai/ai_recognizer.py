from typing import Any, Optional

from app.models.enums import RecognitionStatus
from app.models.recognition import RecognitionCell, RecognitionResult
from app.models.menu import DailyMenu


class AIRecognizer:
    """First-version mock AI recognizer.

    The interface is designed so a real image-recognition model
    can replace this implementation later.
    """

    def __init__(self, mock_foods: Optional[list[dict]] = None):
        self.mock_foods = mock_foods or [
            {"food_id": "F001", "food_name": "米饭", "confidence": 0.96},
            {"food_id": "F002", "food_name": "红烧肉", "confidence": 0.91},
            {"food_id": "F003", "food_name": "青菜", "confidence": 0.88},
            {"food_id": "F004", "food_name": "鸡蛋", "confidence": 0.94},
        ]
        self.model_loaded = False
        self.last_regions = None

    def load_model(self) -> None:
        """Mock model loading."""
        self.model_loaded = True

    def recognize(
        self,
        image: Any = None,
        regions: Optional[dict[int, Any]] = None,
        daily_menu: Optional[DailyMenu] = None,
    ) -> RecognitionResult:
        """Recognize food in each tray cell.

        image and regions are intentionally generic in v1.
        A real implementation can later receive an OpenCV image
        and configured image regions.
        """
        self.last_regions = regions

        if not self.model_loaded:
            return RecognitionResult(
                cells=[],
                status="FAILED",
            )

        cell_count = len(regions) if regions else len(self.mock_foods)
        cells = []

        for index in range(cell_count):
            food = self.mock_foods[index % len(self.mock_foods)]
            if daily_menu is not None and daily_menu.foods:
                menu_food = daily_menu.foods[index % len(daily_menu.foods)]
                food = {
                    "food_id": menu_food.food_id,
                    "food_name": menu_food.food_name,
                    "confidence": food["confidence"],
                }

            cells.append(
                RecognitionCell(
                    cell_id=index + 1,
                    food_id=food["food_id"],
                    food_name=food["food_name"],
                    confidence=food["confidence"],
                    status=RecognitionStatus.OK,
                )
            )

        return RecognitionResult(
            cells=cells,
            status="OK",
        )

    def get_model_info(self) -> dict:
        return {
            "name": "MockFoodRecognizer",
            "version": "1.0",
            "loaded": self.model_loaded,
        }
