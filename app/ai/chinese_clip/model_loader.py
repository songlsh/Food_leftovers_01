"""ChineseCLIP model loader with optional transformers backend."""

class ChineseCLIPModelLoader:
    def __init__(self, model_name=None, device="auto"):
        self.model_name = model_name or "OFA-Sys/chinese-clip-vit-base-patch16"
        self.device = device
        self.model = None
        self.processor = None

    def get_device(self):
        if self.device != "auto":
            return self.device
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            return "cpu"

    def load_model(self):
        try:
            from transformers import ChineseCLIPModel, ChineseCLIPProcessor
            import torch
            device = self.get_device()
            self.processor = ChineseCLIPProcessor.from_pretrained(self.model_name)
            self.model = ChineseCLIPModel.from_pretrained(self.model_name)
            self.model.to(device)
            self.model.eval()
            return True
        except Exception:
            # Keep demo/system compatibility when model packages or weights are absent.
            return False

    def get(self):
        if self.model is None:
            self.load_model()
        return self.model, self.processor, self.get_device()
