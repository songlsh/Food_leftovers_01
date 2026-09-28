from .prompt import build_prompts


def _extract_tensor(outputs):
    """
    兼容不同 Transformers 版本的 BaseModelOutputWithPooling、
    tuple/list 以及 Tensor 输出。
    """
    import torch

    if isinstance(outputs, torch.Tensor):
        return outputs

    # BaseModelOutputWithPooling
    pooler = getattr(outputs, "pooler_output", None)

    if isinstance(pooler, torch.Tensor):
        return pooler

    # 有些版本的 pooler_output 本身可能仍然是 model output
    if pooler is not None:
        nested = getattr(pooler, "pooler_output", None)
        if isinstance(nested, torch.Tensor):
            return nested

        nested = getattr(pooler, "last_hidden_state", None)
        if isinstance(nested, torch.Tensor):
            return nested[:, 0]

    # last_hidden_state
    hidden = getattr(outputs, "last_hidden_state", None)

    if isinstance(hidden, torch.Tensor):
        return hidden[:, 0]

    # tuple / list
    if isinstance(outputs, (tuple, list)):
        for item in outputs:
            if isinstance(item, torch.Tensor):
                if item.ndim == 3:
                    return item[:, 0]
                return item

    raise TypeError(
        f"Unable to extract Tensor from text model output: "
        f"{type(outputs)}"
    )


def _text_embedding(model, outputs):
    """
    从 ChineseCLIP text encoder 输出中提取 Tensor，
    然后通过 text_projection 投影到 CLIP embedding space。
    """
    pooled = _extract_tensor(outputs)

    projection = getattr(model, "text_projection", None)

    if projection is not None:
        pooled = projection(pooled)

    return pooled


def encode_text(food_name, loader):
    import torch

    model, processor, device = loader.get()

    prompts = build_prompts(food_name)

    inputs = processor(
        text=prompts,
        padding=True,
        return_tensors="pt"
    )

    inputs = {
        k: v.to(device)
        for k, v in inputs.items()
    }

    with torch.no_grad():
        outputs = model.text_model(**inputs)

        features = _text_embedding(
            model,
            outputs
        )

    # 每条 prompt 分别归一化
    features = features / features.norm(
        p=2,
        dim=-1,
        keepdim=True
    ).clamp_min(1e-12)

    # 多个中文 prompt 求平均
    features = features.mean(
        dim=0,
        keepdim=True
    )

    # 再归一化
    features = features / features.norm(
        p=2,
        dim=-1,
        keepdim=True
    ).clamp_min(1e-12)

    return features