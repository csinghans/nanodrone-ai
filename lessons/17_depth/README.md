# Lesson 17 — Monocular depth estimation (train a dense model)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Train a model that guesses distance from a single flat image — a depth value for every pixel, with no depth sensor needed. · **Builds on:** L2, L3, L4

## Why

Until now depth was only ever read at a single point — range to one target
(Lesson 2/8). But the real AI-deck has a **grayscale camera and no depth
sensor**. To avoid obstacles on-board, the drone has to **guess depth from a
single image**. That's the course's signature move one more time (Lesson 3/8/13):
when there's no rule, train a small model — and here, for the first time, it's a
**dense** model (a value per pixel, not one number). The labels are free: the
simulator hands us a full depth image, the "privileged teacher".

## Concept

`TinyDepthNet` is a tiny **encoder–decoder**:

- the **encoder** is Lesson 3's TinyDronet conv stack (kept spatial, no global
  pool), shrinking 64×64 → 8×8 features;
- the **decoder** upsamples back to a 16×16 depth grid, with a sigmoid so the
  output is depth in [0, 1] of `MAX_DEPTH` (5 m — the empty horizon is "far", not
  infinite, so depth is clipped and bounded).

Trained with L1 loss on the normalized depth; scored with **AbsRel**
(`mean(|pred − true| / true)`). The dominant signal — floor distance grows with
image row — is easy to learn, and the pillars add the structure that matters for
avoidance. GAP8 reality is kept in view: int8 footprint must stay < 512 KB.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/17_depth/train_depth.py --samples 240 --epochs 60  # train
python lessons/17_depth/train_depth.py --selftest                  # tiny, asserts
python lessons/17_depth/depth_demo.py                              # save output/depth.png
```

Read [`train_depth.py`](train_depth.py) — the encoder–decoder and the free
depth labels — then [`depth_demo.py`](depth_demo.py). Both need PyTorch, so (like
Lessons 3/8/13/14b) they're verified locally, not in the torch-free CI.

## Checkpoint ✅

```
DEPTH OK: trained 160 samples, val AbsRel=0.155, int8 footprint=32.9 KB (<512 fits), saved .../output/depth_cnn.pth
DEPTH-DEMO OK: saved .../output/depth.png, frame AbsRel=0.153
```

`train_depth.py --selftest` asserts the model reaches AbsRel < 0.25 and fits the
GAP8 budget. `depth_demo.py` writes a RGB | true-depth | predicted-depth panel so
you can *see* what it learned.

## Going further

- Feed the dense depth into the harder multi-obstacle RL course (Lesson 19) as
  an observation — perception now drives decision.
- Honest gap: this is trained on clean sim renders; on the real grayscale camera
  it will degrade. That's exactly what domain randomization (Lesson 20) fixes and
  Lesson 25 measures.
- Try a scale-invariant log-depth loss and compare AbsRel.

---

<a name="中文"></a>
# Lesson 17 — 單目深度估計（訓練一個 dense 模型）

🌐 [English](#lesson-17--monocular-depth-estimation-train-a-dense-model) · **繁體中文**（以下）

> **一句話：**訓練一個模型從一張平面影像猜出遠近：每個像素都有距離值，完全不需要深度感測器。 · **建立在：**第 2 課、第 3 課、第 4 課

## 為什麼

到目前為止深度只被拿來對單一點測距（Lesson 2/8）。但真實 AI-deck 是**灰階相機、沒有深度感測器**。
要在板上避障，無人機得**從單張影像猜深度**。這是課程招牌動作再現一次（Lesson 3/8/13）：
沒有規則時，就訓一個小模型 —— 而這裡第一次是 **dense** 模型（每個像素一個值，不是單一數字）。
標籤免費：模擬器直接給我們整張深度圖，這個「特權老師」。

## 概念

`TinyDepthNet` 是一個 tiny **encoder–decoder**：

- **encoder** 是 Lesson 3 TinyDronet 的卷積堆疊（保留空間、不做 global pool），把 64×64 → 8×8 特徵；
- **decoder** 上採樣回 16×16 深度格，最後 sigmoid，讓輸出是 `MAX_DEPTH`（5 公尺）的 [0, 1] 比例 ——
  空曠的地平線是「遠」而非無限，所以深度被裁切、有界。

用 L1 loss 在正規化深度上訓練；用 **AbsRel**（`mean(|pred − true| / true)`）評分。最主要的訊號 ——
地板距離隨影像列數增加 —— 很好學，柱子則加上避障真正需要的結構。GAP8 現實也顧到：int8 footprint 必須 < 512 KB。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/17_depth/train_depth.py --samples 240 --epochs 60  # 訓練
python lessons/17_depth/train_depth.py --selftest                  # tiny、會 assert
python lessons/17_depth/depth_demo.py                              # 存 output/depth.png
```

請讀 [`train_depth.py`](train_depth.py)（encoder–decoder 與免費的深度標籤），再看 [`depth_demo.py`](depth_demo.py)。
兩支都需要 PyTorch，所以（跟 Lesson 3/8/13/14b 一樣）在本機驗證，不進 torch-free 的 CI。

## 驗收 ✅

```
DEPTH OK: trained 160 samples, val AbsRel=0.155, int8 footprint=32.9 KB (<512 fits), saved .../output/depth_cnn.pth
DEPTH-DEMO OK: saved .../output/depth.png, frame AbsRel=0.153
```

`train_depth.py --selftest` 驗證模型達到 AbsRel < 0.25 且塞得進 GAP8 預算。`depth_demo.py` 會輸出
「RGB｜真值深度｜預測深度」三聯圖，讓你*看到*它學到了什麼。

## 延伸

- 把 dense 深度餵進更難的多障礙 RL（Lesson 19）當觀測 —— 感知開始驅動決策。
- 誠實的落差：這是用乾淨 sim 畫面訓的；上真實灰階相機會劣化。那正是 domain randomization（Lesson 20）要修、
  Lesson 25 要量的東西。
- 試試 scale-invariant 的 log-depth loss，比較 AbsRel。
