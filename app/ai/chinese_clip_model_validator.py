"""
V31_3_7 ChineseCLIP Model Validation Layer

Used for validating model backend connection,
image encoder, text encoder and similarity pipeline.
"""

class ChineseCLIPModelValidator:

    def __init__(self, backend=None):
        self.backend = backend

    def validate(self, image_path, candidates):

        if self.backend:
            return self.backend.validate(
                image_path,
                candidates
            )

        return {
            "status": "MODEL_BACKEND_PENDING",
            "image": image_path,
            "candidates": candidates
        }
