import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.ai.chinese_clip_real_model import ChineseCLIPRealModel

def test():
    model = ChineseCLIPRealModel()

    result = model.predict(
        "test_images/rice.jpg",
        ["米饭", "红烧肉", "青菜", "鸡蛋"]
    )

    assert "status" in result

    print("ChineseCLIP V31_3_9 real model test passed")
    print(result)

if __name__ == "__main__":
    test()
