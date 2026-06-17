# Lesson 8 — Follow a real person (learned detector)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lesson 7 followed a bright-orange marker by colour. But you can't put an orange
ball on a real person — and a colour rule falls apart on a multi-coloured human
against a busy background. This is exactly the case from "when do you need
training?": the rule is impossible to hand-write, so we **train a detector**.
It's the first lesson whose capability doesn't work until you train it.

## Concept

The person here is a small multi-colour figure (skin head, **blue shirt that
blends with the floor**, dark legs) — a single HSV threshold can't isolate it.
So we replace the colour detector with a small **CNN** that learns the person's
appearance:

1. **Make data** — drop the person at random spots; the simulator's ground truth
   gives the true bearing for free (a "privileged teacher" — no hand labels).
2. **Train** — a `PersonCNN` learns image → bearing (just like Lesson 3's
   imitation CNN, but the target is a person, not a red box).
3. **Fly** — the follow loop asks the CNN "which way is the person?", takes the
   *range* from the depth sensor (no need to learn metric distance), then reuses
   Lesson 7's yaw-follow to trail them.

Everything else (geometry, GUI, input) comes from the shared `nanodrone` core.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/08_follow_real/gen_person_dataset.py        # 1. data (ground-truth labels)
python lessons/08_follow_real/train_person_cnn.py          # 2. train the detector (MPS)
python lessons/08_follow_real/follow_real.py               # 3. you drive, drone follows
python lessons/08_follow_real/follow_real.py --headless     # scripted demo / verify
```

Read [`follow_real.py`](follow_real.py): `cnn_bearing()` is the learned "which
way", `depth_at_bearing()` is the sensed range, and the rest is Lesson 7's loop.

## Checkpoint ✅

Training prints a falling error, ending around (verified on this machine):

```
  epoch 120  val MAE = 1.23 deg
```

Then the headless follow walks the person in a circle and prints:

```
FOLLOW OK (CNN): tracked 56 frames, mean true bearing error 14.1 deg.
```

The drone keeps the person in view using a detector it *learned* — no colour
rule anywhere. In the GUI, drive the person around and watch it trail you.

## Going further

- **Real images:** retrain on a proper humanoid model or textured person to
  shrink the sim-to-real gap.
- **Detect + range in one net:** add a second CNN output for distance instead of
  using the depth sensor.
- **Re-acquire:** add a search behaviour when the CNN loses the person.

---

<a name="中文"></a>
# Lesson 8 — 跟隨真人（學習式偵測器）

🌐 [English](#lesson-8--follow-a-real-person-learned-detector) · **繁體中文**（以下）

## 為什麼

Lesson 7 靠顏色跟隨橘色標記。但你不能在真人身上貼橘色球 —— 而且色彩規則碰到「多色的人 + 雜亂背景」就崩潰。這正是「什麼時候需要訓練」的案例：規則寫不出來，所以我們**訓練一個偵測器**。這是課程中第一個「不訓練就不會動」的能力。

## 概念

這裡的人是一個多色小人（膚色頭、**會跟地板混淆的藍衣**、深色腿）—— 單一 HSV 門檻無法把它分離。於是我們用一個小 **CNN** 取代色彩偵測，讓它學人的外觀：

1. **產資料** —— 把人隨機擺放；模擬器的真值直接給出正確方位（「特權老師」，免手標）。
2. **訓練** —— `PersonCNN` 學「影像 → 方位」（就像 Lesson 3 的模仿 CNN，只是目標從紅盒換成人）。
3. **飛行** —— 跟隨迴圈問 CNN「人在哪個方向」、用**深度感測器**取得距離（不必學公制距離），再沿用 Lesson 7 的 yaw 跟隨尾隨他。

其餘（幾何、GUI、輸入）都來自共用核心 `nanodrone`。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/08_follow_real/gen_person_dataset.py        # 1. 產資料（真值標籤）
python lessons/08_follow_real/train_person_cnn.py          # 2. 訓練偵測器（MPS）
python lessons/08_follow_real/follow_real.py               # 3. 你操控、無人機跟
python lessons/08_follow_real/follow_real.py --headless     # 腳本化 demo / 驗證
```

請讀 [`follow_real.py`](follow_real.py)：`cnn_bearing()` 是學習出來的「哪個方向」、`depth_at_bearing()` 是感測到的距離，其餘就是 Lesson 7 的迴圈。

## 驗收 ✅

訓練會印出逐漸下降的誤差，最後約（本機實測）：

```
  epoch 120  val MAE = 1.23 deg
```

接著 headless 跟隨讓人走一圈並印出：

```
FOLLOW OK (CNN): tracked 56 frames, mean true bearing error 14.1 deg.
```

無人機用一個**自己學來的**偵測器把人保持在視野中 —— 全程沒有任何色彩規則。在 GUI 裡開著人到處走，看它尾隨你。

## 延伸

- **真實影像：** 用正式人形或貼圖人物重新訓練，縮小 sim-to-real 落差。
- **偵測 + 測距合一：** 給 CNN 加第二個輸出預測距離，取代深度感測器。
- **重新鎖定：** CNN 跟丟時加一個搜尋行為。
