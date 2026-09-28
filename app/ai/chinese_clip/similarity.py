def cosine_similarity(image_features, text_features):
    """Cosine similarity for torch tensors or array-like inputs."""
    import torch

    # 强制转换为 float32，兼容 [1, 0] 这种 Python list / Long Tensor
    image_features = torch.as_tensor(
        image_features,
        dtype=torch.float32
    )
    text_features = torch.as_tensor(
        text_features,
        dtype=torch.float32
    )

    # 一维向量转换成 [1, D]
    if image_features.ndim == 1:
        image_features = image_features.unsqueeze(0)

    if text_features.ndim == 1:
        text_features = text_features.unsqueeze(0)

    # L2 Normalize
    image_features = image_features / image_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    ).clamp_min(1e-12)

    text_features = text_features / text_features.norm(
        p=2,
        dim=-1,
        keepdim=True
    ).clamp_min(1e-12)

    # Cosine similarity
    return (
        image_features @ text_features.transpose(0, 1)
    ).squeeze(0)