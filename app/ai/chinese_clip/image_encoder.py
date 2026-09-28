from PIL import Image


def _image_embedding(model, outputs):
    """Extract the projected ChineseCLIP image embedding from model outputs."""
    pooled = getattr(outputs, "pooler_output", None)

    if pooled is None and isinstance(outputs, (tuple, list)):
        pooled = outputs[1] if len(outputs) > 1 else outputs[0]

    if pooled is None:
        pooled = outputs

    projection = getattr(model, "visual_projection", None)
    if projection is not None:
        pooled = projection(pooled)

    return pooled


def encode_image(image_path, loader):
    """Encode one local image with the real ChineseCLIP image encoder."""
    import torch

    model, processor, device = loader.get()
    image = Image.open(image_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # Use no_grad rather than inference_mode because some Transformers
    # projection modules may save their input for autograd internally.
    with torch.no_grad():
        outputs = model.vision_model(**inputs)
        features = _image_embedding(model, outputs)

    features = features / features.norm(
        p=2, dim=-1, keepdim=True
    ).clamp_min(1e-12)
    return features
