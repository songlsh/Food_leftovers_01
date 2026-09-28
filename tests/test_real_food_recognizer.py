from app.ai.chinese_clip_food_recognizer import ChineseCLIPFoodRecognizer

def test():
    model = ChineseCLIPFoodRecognizer()
    result = model.recognize(
        "test_images/rice.jpg",
        ["米饭", "红烧肉", "青菜", "鸡蛋"]
    )

    assert "food" in result
    print("Real food recognizer interface test passed")
    print(result)

if __name__ == "__main__":
    test()
