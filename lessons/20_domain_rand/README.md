# Lesson 20 — Domain randomization (shrink the sim-to-real gap)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lessons 14b / 17 / 18 kept flagging the same honest gap: a model trained on clean
sim renders falls apart on a real camera (different lighting, sensor noise). The
fix isn't a fancier renderer — it's **domain randomization**: jitter the training
images so hard the model *can't* rely on exact pixels and has to learn robust
cues. This is what makes a self-trained small model actually survive deployment.

## Concept

`dr_compare.py` trains two copies of Lesson 17's depth CNN on the **same** scene
data and scores both on a held-out test set seen through a different, never-seen
"camera" (dimmer + heavy noise — `randomize.shift_appearance`):

- **baseline** — trained on clean images. It overfits the clean look and degrades
  on the shifted test.
- **DR** — trained with per-batch `randomize.jitter` (random brightness + heavy
  noise spanning the shifts it'll meet). It learns noise-robust features and
  holds up.

The win is concrete: lower AbsRel on the shifted scene. Same primitives are
reused by Lesson 25 to mimic a real camera and *measure* the gap.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/20_domain_rand/dr_compare.py            # train baseline + DR, compare
python lessons/20_domain_rand/dr_compare.py --selftest  # tiny run, asserts (local)
```

Read [`randomize.py`](randomize.py) (the augmentations) and
[`dr_compare.py`](dr_compare.py). It builds on Lesson 17's `TinyDepthNet`, so it
needs PyTorch — verified locally, not in the torch-free CI.

## Checkpoint ✅

```
DR OK: baseline AbsRel=0.196 on shifted scene, DR model=0.163 (robustness up 17%)
```

The self-test asserts the DR model beats the clean-trained baseline on the
appearance-shifted test — domain randomization measurably shrinks the gap.

## Going further

- Apply the same `jitter` to Lesson 18's flow net and Lesson 13's confirm CNN.
- Add scene-level randomization (`p.changeVisualShape` colours, light direction),
  not just image-space.
- Lesson 25 measures the gap on *real* camera frames — DR's gain there is the
  real test.

---

<a name="中文"></a>
# Lesson 20 — 域隨機化（縮小 sim-to-real 落差）

🌐 [English](#lesson-20--domain-randomization-shrink-the-sim-to-real-gap) · **繁體中文**（以下）

## 為什麼

Lesson 14b / 17 / 18 一再點出同一個誠實的落差：用乾淨 sim 畫面訓的模型，一上真實相機（不同光照、感測雜訊）就垮。
解法不是更逼真的 renderer —— 而是**域隨機化**：把訓練影像擾動到模型*無法*依賴精確像素、被迫學穩健特徵。
這正是讓自訓小模型真能上線存活的關鍵。

## 概念

`dr_compare.py` 用**同一份**場景資料訓兩個 Lesson 17 深度 CNN，並在一個從未見過的「相機」
（更暗 + 重雜訊，`randomize.shift_appearance`）下的測試集上評分：

- **baseline** —— 用乾淨影像訓練。過擬合乾淨外觀，在偏移測試上劣化。
- **DR** —— 每個 batch 套 `randomize.jitter`（隨機亮度 + 涵蓋將遇到偏移的重雜訊）。學到抗雜訊特徵，撐得住。

贏的地方很具體：偏移場上的 AbsRel 更低。同一套原語被 Lesson 25 重用來模擬真實相機並*量測*落差。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/20_domain_rand/dr_compare.py            # 訓 baseline + DR，比較
python lessons/20_domain_rand/dr_compare.py --selftest  # tiny、會 assert
```

請讀 [`randomize.py`](randomize.py)（增強）與 [`dr_compare.py`](dr_compare.py)。它建在 Lesson 17 的
`TinyDepthNet` 上，需要 PyTorch —— 在本機驗證，不進 torch-free 的 CI。

## 驗收 ✅

```
DR OK: baseline AbsRel=0.196 on shifted scene, DR model=0.163 (robustness up 17%)
```

自我測試驗證 DR 模型在外觀偏移測試上勝過乾淨訓練的 baseline —— 域隨機化可量測地縮小落差。

## 延伸

- 把同一套 `jitter` 套到 Lesson 18 的 flow net 與 Lesson 13 的 confirm CNN。
- 加場景級隨機化（`p.changeVisualShape` 顏色、光照方向），不只影像空間。
- Lesson 25 在*真實*相機影格上量測落差 —— DR 在那裡的收益才是真正的考驗。
