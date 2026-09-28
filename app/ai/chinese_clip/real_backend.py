from .image_encoder import encode_image
from .text_encoder import encode_text
from .similarity import cosine_similarity
from .ranker import rank_candidates
from .real_weight_loader import RealWeightLoader

class RealChineseCLIPBackend:
    name="Chinese-CLIP"; version="ViT-B/16"
    def __init__(self,model_path="models/chinese_clip",device="auto",threshold=0.0):
        self.loader=RealWeightLoader(model_path,device); self.threshold=threshold; self.status="NOT_LOADED"
    def load_model(self): self.loader.load(); self.status="READY"; return True
    def _candidate(self,c,i):
        if isinstance(c,str): return str(i+1),c
        if isinstance(c,dict):
            n=c.get("name") or c.get("food_name") or c.get("label") or c.get("food")
            if not n: raise ValueError(f"Candidate {i} has no food name")
            return str(c.get("food_id",c.get("id",i+1))),n
        raise TypeError(type(c).__name__)
    def predict(self,image_path,candidates):
        if not candidates: raise ValueError("candidates must not be empty")
        if self.loader.model is None:self.load_model()
        image_features=encode_image(image_path,self.loader); raw=[]
        for i,c in enumerate(candidates):
            fid,name=self._candidate(c,i); text_features=encode_text(name,self.loader)
            sim=float(cosine_similarity(image_features,text_features).item())
            raw.append({"food_id":fid,"name":name,"similarity":sim})
        ranked=rank_candidates(raw,self.threshold)
        try:
            import torch
            scale=float(self.loader.model.logit_scale.exp().detach().cpu().item())
            scale=min(max(scale,1.0),100.0)
            probs=torch.softmax(torch.tensor([x["similarity"] for x in raw])*scale,dim=0).tolist()
            by_id={x["food_id"]:float(p) for x,p in zip(raw,probs)}
            for x in ranked:x["confidence"]=by_id[x["food_id"]]
        except Exception: pass
        for x in ranked:x["status"]="REAL_INFERENCE"
        self.status="READY"; return ranked
    def recognize(self,image_path,candidates): return self.predict(image_path,candidates)
