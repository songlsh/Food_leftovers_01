from pathlib import Path
from .chinese_clip.real_backend import RealChineseCLIPBackend

class ChineseCLIPRealInference:
    def __init__(self,model_path="models/chinese_clip",device="auto"):
        self.model_path=Path(model_path); self.backend=RealChineseCLIPBackend(str(self.model_path),device)
    def load(self):
        self.backend.load_model()
        return {"status":"READY","device":self.backend.loader._device(),"model_path":str(self.model_path)}
    def recognize(self,image_path,candidates):
        ranked=self.backend.predict(image_path,candidates); best=ranked[0]
        return {"food":best["name"],"confidence":best["confidence"],"similarity":best["similarity"],"status":"REAL_INFERENCE","candidates":ranked,"device":self.backend.loader._device()}
