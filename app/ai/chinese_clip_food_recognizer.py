"""
V31_3_5.1 ChineseCLIP Food Recognizer
Keeps DetectionService interface compatibility.
"""

class ChineseCLIPFoodRecognizer:
    def __init__(self, backend=None):
        self.backend = backend

    def recognize(self, image, candidates):
        if self.backend:
            return self.backend.recognize(image, candidates)

        return {
            "food": candidates[0] if candidates else "unknown",
            "confidence": 0.0,
            "status": "BACKEND_NOT_CONNECTED"
        }
