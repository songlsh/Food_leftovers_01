from app.ai.chinese_clip.real_backend import RealChineseCLIPBackend

backend=RealChineseCLIPBackend()
backend.load_model()
result=backend.predict(None,[{"id":"F001","name":"米饭"},{"id":"F002","name":"红烧肉"}])
assert backend.loaded
assert len(result)==2
print("Chinese CLIP real backend interface test passed")
