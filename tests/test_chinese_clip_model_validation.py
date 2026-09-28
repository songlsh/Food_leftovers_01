from app.ai.chinese_clip_model_validator import ChineseCLIPModelValidator

def test():
    validator = ChineseCLIPModelValidator()

    result = validator.validate(
        "test_images/rice.jpg",
        [
            "米饭",
            "红烧肉",
            "青菜",
            "鸡蛋"
        ]
    )

    assert result["status"] == "MODEL_BACKEND_PENDING"

    print("ChineseCLIP model validation interface test passed")
    print(result)


if __name__ == "__main__":
    test()
