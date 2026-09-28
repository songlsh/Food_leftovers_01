from pathlib import Path

class RealWeightLoader:
    """Load the locally downloaded ChineseCLIP ViT-B/16 weights only."""
    def __init__(self, model_path="models/chinese_clip", device="auto"):
        self.model_path=Path(model_path); self.device=device
        self.model=None; self.processor=None; self.status="NOT_LOADED"; self.error=None
    def _device(self):
        if self.device != "auto": return self.device
        import torch
        if torch.cuda.is_available(): return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available(): return "mps"
        return "cpu"
    def load(self):
        try:
            if not self.model_path.exists(): raise FileNotFoundError(f"Model directory not found: {self.model_path}")
            if not any(self.model_path.iterdir()): raise FileNotFoundError(f"Model directory is empty: {self.model_path}")
            from transformers import ChineseCLIPModel, ChineseCLIPProcessor
            self.processor=ChineseCLIPProcessor.from_pretrained(str(self.model_path), local_files_only=True)
            self.model=ChineseCLIPModel.from_pretrained(str(self.model_path), local_files_only=True)
            runtime_device=self._device(); self.model.to(runtime_device); self.model.eval()
            self.status="READY"; self.error=None
            return self.model,self.processor,runtime_device
        except Exception as exc:
            self.status="FAILED"; self.error=str(exc); raise
    def get(self):
        if self.model is None or self.processor is None: return self.load()
        return self.model,self.processor,self._device()
