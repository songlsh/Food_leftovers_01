from app.ai import AIRecognizer
from app.models.enums import RecognitionStatus


def main():
    recognizer = AIRecognizer()

    # Before loading, recognition should fail safely.
    failed = recognizer.recognize(
        image="mock_image",
        regions={1: None, 2: None, 3: None, 4: None},
    )

    assert failed.status == "FAILED"

    recognizer.load_model()

    result = recognizer.recognize(
        image="mock_image",
        regions={1: None, 2: None, 3: None, 4: None},
    )

    assert result.status == "OK"
    assert len(result.cells) == 4

    expected_foods = ["米饭", "红烧肉", "青菜", "鸡蛋"]

    for cell, expected_food in zip(result.cells, expected_foods):
        assert cell.food_name == expected_food
        assert cell.food_id is not None
        assert cell.confidence is not None
        assert cell.status == RecognitionStatus.OK

    print("AI recognizer test passed")
    print(f"Model: {recognizer.get_model_info()['name']}")
    print(f"Version: {recognizer.get_model_info()['version']}")
    print(f"Status: {result.status}")

    for cell in result.cells:
        print(
            f"Cell {cell.cell_id}: "
            f"{cell.food_name} - "
            f"{cell.confidence:.2f} - "
            f"{cell.status.value}"
        )


if __name__ == "__main__":
    main()
