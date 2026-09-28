import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("SLS V31_3_11 Runtime Environment")
print("Project Root:", ROOT)

if __name__ == "__main__":
    from tests.test_real_model_weight_integration import test
    test()
