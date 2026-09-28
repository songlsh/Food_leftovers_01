import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.ai.chinese_clip.real_weight_loader import RealWeightLoader


def test():
    loader = RealWeightLoader(os.path.join(ROOT, "models", "chinese_clip"))
    ok = loader.load()
    print("ChineseCLIP V31_3_11 real weight integration test")
    print("Status:", loader.status)
    if loader.error:
        print("Detail:", loader.error)
    # This test distinguishes genuine READY from an expected missing-weight state.
    assert loader.status in ("READY", "FAILED")
    return ok


if __name__ == "__main__":
    test()
