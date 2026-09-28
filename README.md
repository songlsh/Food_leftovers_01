# 食堂四格餐盘剩菜检测系统 V30

本项目用于食堂四格餐盘的剩余食物识别、称重、记录和统计。当前软件阶段以 Mock 设备和 Mock/Demo AI 为主，真实硬件与真实模型后续接入。

## V30 核心 AI 思路

四个格子的位置不固定，但每天菜单固定，因此 AI 不做开放世界食物识别，而是使用当天菜单作为候选集：

```text
日期
 ↓
DailyMenuProvider
 ↓
当天菜单
 ↓
四个 ROI 独立识别
 ↓
FOOD / EMPTY / UNKNOWN
 ↓
Event
```

当前 V30 先用 `DemoModelBackend` 验证菜单约束和数据链路，后续可以替换为 CLIP/SigLIP，不需要修改 DetectionService。

## 一键验证

```bash
python3 test_demo.py
python3 test_all.py
```

当前完整回归：V30 新增 1 项，合计 26 项。

## 菜单配置

周菜单位于：

```text
config/weekly_menu.json
```

每一天配置当天允许 AI 识别的食品候选。
