from __future__ import annotations

from typing import Any, Optional

from app.models.menu import DailyMenu

from app.models.enums import RecognitionStatus
from app.models.recognition import RecognitionCell, RecognitionResult
from .model_backend import FoodModelBackend


class ModelFoodRecognizer:
    """Food recognizer that delegates image inference to a model backend."""

    def __init__(self, backend: FoodModelBackend, confidence_threshold: float = 0.80):
        if not 0.0 <= confidence_threshold <= 1.0:
            raise ValueError("confidence_threshold must be between 0 and 1")
        self.backend = backend
        self.confidence_threshold = float(confidence_threshold)
        self.model_loaded = False
        self.last_regions: Optional[dict[int, Any]] = None
        self.last_error: Optional[str] = None

    def load_model(self) -> None:
        try:
            self.backend.load()
            self.model_loaded = True
            self.last_error = None
        except Exception as exc:
            self.model_loaded = False
            self.last_error = f"MODEL_LOAD_FAILED: {type(exc).__name__}: {exc}"
            raise

    def recognize(
        self,
        image: Any = None,
        regions: Optional[dict[int, Any]] = None,
        daily_menu: Optional[DailyMenu] = None,
    ) -> RecognitionResult:
        self.last_regions = regions
        self.last_error = None

        if not self.model_loaded:
            self.last_error = "MODEL_NOT_LOADED"
            return RecognitionResult(cells=[], status="FAILED")
        if not image:
            self.last_error = "IMAGE_REQUIRED"
            return RecognitionResult(cells=[], status="FAILED")
        if not regions:
            self.last_error = "REGIONS_REQUIRED"
            return RecognitionResult(cells=[], status="FAILED")

        cells = []
        for cell_id in sorted(regions):
            region = regions[cell_id]
            try:
                candidates = daily_menu.foods if daily_menu is not None else None
                prediction = self.backend.predict(str(image), region, candidates=candidates)
                confidence = float(prediction.confidence)
                if not 0.0 <= confidence <= 1.0:
                    raise ValueError("model confidence must be between 0 and 1")

                # V30 safety rule: the recognizer itself enforces the daily-menu
                # candidate set even if a future backend ignores the candidates argument.
                if daily_menu is not None:
                    allowed_ids = {food.food_id for food in daily_menu.foods}
                    if prediction.food_id not in allowed_ids:
                        cells.append(
                            RecognitionCell(
                                cell_id=int(cell_id),
                                food_id=None,
                                food_name=None,
                                confidence=confidence,
                                status=RecognitionStatus.UNKNOWN,
                                result_type="UNKNOWN",
                            )
                        )
                        continue

                status = (
                    RecognitionStatus.OK
                    if confidence >= self.confidence_threshold
                    else RecognitionStatus.LOW_CONFIDENCE
                )
                result_type = "FOOD" if status == RecognitionStatus.OK else "UNKNOWN"
                cells.append(
                    RecognitionCell(
                        cell_id=int(cell_id),
                        food_id=prediction.food_id if result_type == "FOOD" else None,
                        food_name=prediction.food_name if result_type == "FOOD" else None,
                        confidence=confidence,
                        status=status,
                        result_type=result_type,
                    )
                )
            except Exception as exc:
                self.last_error = f"CELL_{cell_id}_FAILED: {type(exc).__name__}: {exc}"
                cells.append(
                    RecognitionCell(
                        cell_id=int(cell_id),
                        status=RecognitionStatus.FAILED,
                        result_type="UNKNOWN",
                    )
                )

        overall = "OK" if cells and all(c.status == RecognitionStatus.OK for c in cells) else "PARTIAL"
        if cells and all(c.status == RecognitionStatus.FAILED for c in cells):
            overall = "FAILED"
        return RecognitionResult(cells=cells, status=overall)

    def get_model_info(self) -> dict:
        return {
            "name": self.backend.name,
            "version": self.backend.version,
            "loaded": self.model_loaded,
            "confidence_threshold": self.confidence_threshold,
            "last_error": self.last_error,
        }
