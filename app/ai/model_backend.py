"""Pluggable image-model backends for V29.

The application does not bundle model weights.  This module defines a stable
inference contract and an optional ONNX Runtime implementation so a trained
food-classification model can be plugged in later without changing
DetectionService.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class ModelPrediction:
    food_id: Optional[str]
    food_name: Optional[str]
    confidence: float


class FoodModelBackend(ABC):
    """Backend contract used by ModelFoodRecognizer."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def version(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def load(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def predict(
        self, image_path: str, region: dict[str, Any], candidates: Optional[Sequence[Any]] = None
    ) -> ModelPrediction:
        raise NotImplementedError


class DemoModelBackend(FoodModelBackend):
    """Deterministic backend used to test the V29 model pipeline.

    It deliberately does not pretend to be an image model.  It only verifies
    that region inputs, prediction results, confidence thresholds and the
    DetectionService integration work before real weights are available.
    """

    def __init__(self, predictions: Optional[list[ModelPrediction]] = None):
        self.predictions = predictions or [
            ModelPrediction("F001", "米饭", 0.96),
            ModelPrediction("F002", "红烧肉", 0.91),
            ModelPrediction("F003", "青菜", 0.88),
            ModelPrediction("F004", "鸡蛋", 0.94),
        ]
        self.loaded = False

    @property
    def name(self) -> str:
        return "DemoFoodModel"

    @property
    def version(self) -> str:
        return "1.0"

    def load(self) -> None:
        self.loaded = True

    def predict(
        self, image_path: str, region: dict[str, Any], candidates: Optional[Sequence[Any]] = None
    ) -> ModelPrediction:
        if not self.loaded:
            raise RuntimeError("model is not loaded")
        cell_id = int(region["cell_id"])
        if cell_id < 1:
            raise ValueError("cell_id must be positive")
        prediction = self.predictions[(cell_id - 1) % len(self.predictions)]
        if not candidates:
            return prediction

        candidate_ids = {str(getattr(item, "food_id", item)) for item in candidates}
        if prediction.food_id in candidate_ids:
            return prediction

        # Demo behavior: force the deterministic prediction into today's menu.
        first = candidates[(cell_id - 1) % len(candidates)]
        return ModelPrediction(
            str(getattr(first, "food_id", "")),
            str(getattr(first, "food_name", first)),
            prediction.confidence,
        )


class OnnxFoodModelBackend(FoodModelBackend):
    """Optional ONNX image-classification backend.

    Expected model output: one vector of class scores/logits.  Labels are
    loaded from a JSON file with either a list of names or a list of objects
    containing ``food_id`` and ``food_name``.

    Optional dependencies are imported only when this backend is used.
    """

    def __init__(
        self,
        model_path: str | Path,
        labels_path: str | Path,
        input_size: tuple[int, int] = (224, 224),
        mean: tuple[float, float, float] = (0.485, 0.456, 0.406),
        std: tuple[float, float, float] = (0.229, 0.224, 0.225),
    ):
        self.model_path = Path(model_path)
        self.labels_path = Path(labels_path)
        self.input_size = input_size
        self.mean = mean
        self.std = std
        self._session = None
        self._labels: list[dict[str, str]] = []

    @property
    def name(self) -> str:
        return "ONNXFoodModel"

    @property
    def version(self) -> str:
        return "1.0"

    def load(self) -> None:
        try:
            import onnxruntime as ort
            from PIL import Image  # noqa: F401
        except ImportError as exc:
            raise RuntimeError(
                "ONNX backend requires optional dependencies: pillow and onnxruntime"
            ) from exc

        if not self.model_path.exists():
            raise FileNotFoundError(self.model_path)
        if not self.labels_path.exists():
            raise FileNotFoundError(self.labels_path)

        raw = json.loads(self.labels_path.read_text(encoding="utf-8"))
        if not isinstance(raw, list) or not raw:
            raise ValueError("labels JSON must contain a non-empty list")
        labels = []
        for index, item in enumerate(raw):
            if isinstance(item, str):
                labels.append({"food_id": f"F{index + 1:03d}", "food_name": item})
            elif isinstance(item, dict) and item.get("food_name"):
                labels.append({
                    "food_id": str(item.get("food_id") or f"F{index + 1:03d}"),
                    "food_name": str(item["food_name"]),
                })
            else:
                raise ValueError(f"invalid label at index {index}")

        self._labels = labels
        self._session = ort.InferenceSession(str(self.model_path), providers=["CPUExecutionProvider"])

    def predict(
        self, image_path: str, region: dict[str, Any], candidates: Optional[Sequence[Any]] = None
    ) -> ModelPrediction:
        if self._session is None:
            raise RuntimeError("model is not loaded")

        import numpy as np
        from PIL import Image

        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(path)

        box = region.get("region")
        if not box or len(box) != 4:
            raise ValueError("region must contain four points")
        xs = [int(point[0]) for point in box]
        ys = [int(point[1]) for point in box]
        left, right = min(xs), max(xs)
        top, bottom = min(ys), max(ys)
        if right <= left or bottom <= top:
            raise ValueError("invalid image region")

        with Image.open(path) as image:
            crop = image.convert("RGB").crop((left, top, right, bottom))
            crop = crop.resize(self.input_size)
            array = np.asarray(crop, dtype=np.float32) / 255.0

        mean = np.asarray(self.mean, dtype=np.float32)
        std = np.asarray(self.std, dtype=np.float32)
        array = (array - mean) / std
        tensor = np.transpose(array, (2, 0, 1))[None, ...]

        input_name = self._session.get_inputs()[0].name
        outputs = self._session.run(None, {input_name: tensor})
        if not outputs:
            raise RuntimeError("model returned no output")
        scores = np.asarray(outputs[0]).reshape(-1)
        if scores.size != len(self._labels):
            raise RuntimeError(
                f"model output classes={scores.size} do not match labels={len(self._labels)}"
            )

        # Softmax makes the confidence semantics consistent for raw logits.
        scores = scores - np.max(scores)
        probabilities = np.exp(scores)
        probabilities = probabilities / np.sum(probabilities)

        if candidates:
            candidate_ids = {str(getattr(item, "food_id", item)) for item in candidates}
            mask = np.array([label["food_id"] in candidate_ids for label in self._labels], dtype=bool)
            if not np.any(mask):
                raise RuntimeError("none of the daily-menu foods exist in model labels")
            probabilities = np.where(mask, probabilities, 0.0)
            total = float(np.sum(probabilities))
            if total <= 0.0:
                raise RuntimeError("candidate probabilities are empty")
            probabilities = probabilities / total

        index = int(np.argmax(probabilities))
        label = self._labels[index]
        return ModelPrediction(
            food_id=label["food_id"],
            food_name=label["food_name"],
            confidence=float(probabilities[index]),
        )
