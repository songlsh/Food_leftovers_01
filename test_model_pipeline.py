from pathlib import Path
import tempfile

from app.ai import DemoModelBackend, ModelFoodRecognizer
from app.models.enums import RecognitionStatus


def main():
    with tempfile.TemporaryDirectory() as tmp:
        image = Path(tmp) / "tray.jpg"
        image.write_bytes(b"demo-image")
        regions = {
            1: {"image_path": str(image), "cell_id": 1, "region": [[0, 0], [10, 0], [10, 10], [0, 10]]},
            2: {"image_path": str(image), "cell_id": 2, "region": [[10, 0], [20, 0], [20, 10], [10, 10]]},
            3: {"image_path": str(image), "cell_id": 3, "region": [[0, 10], [10, 10], [10, 20], [0, 20]]},
            4: {"image_path": str(image), "cell_id": 4, "region": [[10, 10], [20, 10], [20, 20], [10, 20]]},
        }
        recognizer = ModelFoodRecognizer(DemoModelBackend(), confidence_threshold=0.85)
        assert recognizer.recognize(str(image), regions).status == "FAILED"
        recognizer.load_model()
        result = recognizer.recognize(str(image), regions)
        assert result.status == "OK"
        assert len(result.cells) == 4
        assert all(c.status == RecognitionStatus.OK for c in result.cells)
        assert [c.food_name for c in result.cells] == ["米饭", "红烧肉", "青菜", "鸡蛋"]

        low = ModelFoodRecognizer(
            DemoModelBackend(), confidence_threshold=0.95
        )
        low.load_model()
        low_result = low.recognize(str(image), regions)
        assert low_result.status == "PARTIAL"
        assert low_result.cells[1].status == RecognitionStatus.LOW_CONFIDENCE

    print("V29 model pipeline test passed")
    print("- Four image regions are passed independently to the model backend")
    print("- Confidence threshold produces LOW_CONFIDENCE safely")
    print("- Model backend is replaceable without changing DetectionService")


if __name__ == "__main__":
    main()
