def rank_candidates(items,threshold=0.0):
    import torch
    if not items:return []
    logits=torch.tensor([float(x["similarity"]) for x in items],dtype=torch.float32)
    confidence=torch.softmax(logits,dim=0).tolist()
    ranked=[]
    for item,conf in zip(items,confidence):
        row=dict(item); row["confidence"]=float(conf); row["status"]="REAL_INFERENCE" if row["similarity"]>=threshold else "BELOW_THRESHOLD"; ranked.append(row)
    return sorted(ranked,key=lambda x:x["similarity"],reverse=True)
