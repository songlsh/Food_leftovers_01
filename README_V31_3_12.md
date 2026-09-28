# SLS V31_3_12 ChineseCLIP Real Image→Text

基于 V31_3_11 FULL 完整项目，替换掉原来的 REAL_BACKEND_PENDING 占位推理。

真实流程：本地 ViT-B/16 权重 → 图片 embedding → 中文候选文本 embedding → cosine similarity → learned logit scale → softmax → 排名。

运行：
```bash
PYTHONPATH=. python tests/test_v31_3_12_real_food_image.py --image "/path/to/food.jpg"
```

`confidence` 是候选集合内的相对 softmax 分数，并非校准后的食品分类概率。
