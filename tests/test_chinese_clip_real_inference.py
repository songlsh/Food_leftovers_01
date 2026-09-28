import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.ai.chinese_clip_real_inference import ChineseCLIPRealInference

def main():
    image=ROOT/"test_images"/"rice.jpg"
    if not image.exists():
        print("SKIP: test_images/rice.jpg not found.")
        print("Use tests/test_v31_3_12_real_food_image.py --image <your-image>")
        return 0
    result=ChineseCLIPRealInference(ROOT/"models"/"chinese_clip").recognize(str(image),["米饭","红烧肉","青菜","鸡蛋"])
    assert result["status"]=="REAL_INFERENCE" and result["confidence"]>0 and result["similarity"]!=0
    print("ChineseCLIP V31_3_12 real Image->Text inference test passed")
    print("Prediction:",result["food"]); print("Confidence:",result["confidence"]); print("Similarity:",result["similarity"]); print("Device:",result["device"])
    for i,x in enumerate(result["candidates"],1): print(f"  {i}. {x['name']} similarity={x['similarity']:.6f} confidence={x['confidence']:.6f}")
    return 0
if __name__=="__main__":raise SystemExit(main())
