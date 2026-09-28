from app.ai.chinese_clip.prompt import build_prompts
from app.ai.chinese_clip.similarity import cosine_similarity

print(build_prompts("红烧肉"))
score = cosine_similarity([1, 0], [1, 0])
score = float(score.item()) if hasattr(score, "item") else float(score)
assert abs(score - 1.0) < 1e-6
print("ChineseCLIP Backend PASS")
