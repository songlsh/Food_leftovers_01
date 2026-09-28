import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from app.ai.chinese_clip_real_inference import ChineseCLIPRealInference

p=argparse.ArgumentParser(); p.add_argument("--image",required=True); p.add_argument("--candidates",nargs="+",default=["米饭","红烧肉","青菜","鸡蛋"]); p.add_argument("--model-path",default=str(ROOT/"models"/"chinese_clip")); a=p.parse_args()
image=Path(a.image).expanduser().resolve()
if not image.exists():raise FileNotFoundError(image)
r=ChineseCLIPRealInference(a.model_path).recognize(str(image),a.candidates)
print("SLS V31_3_12 REAL ChineseCLIP Image->Text"); print("Image:",image); print("Device:",r["device"]); print("Prediction:",r["food"]); print("Confidence:",f"{r['confidence']:.6f}"); print("Similarity:",f"{r['similarity']:.6f}"); print("Status:",r["status"]); print("Ranking:")
for i,x in enumerate(r["candidates"],1):print(f"{i}. {x['name']:<12} similarity={x['similarity']:.6f} confidence={x['confidence']:.6f}")
