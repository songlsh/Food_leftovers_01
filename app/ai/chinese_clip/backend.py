class ChineseCLIPBackend:
    name = "Chinese-CLIP"
    version = "ViT-B-16"

    def __init__(self, mode="mock"):
        self.mode = mode

    def predict(self, image, candidates):
        scores = [0.91, 0.82, 0.73, 0.56]
        return [
            {"food_id": c.get("id"), "name": c.get("name"), "score": scores[i % 4]}
            for i, c in enumerate(candidates)
        ]
