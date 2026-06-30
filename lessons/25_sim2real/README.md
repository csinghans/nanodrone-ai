# Lesson 25 — Measure the sim-to-real gap, honestly

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Every model in the course (L3/L8/L13/L17) was trained and scored in clean sim.
The honest question before trusting one on hardware: **how much accuracy do you
lose on a real camera?** This turns the hand-wave "it'll be worse on real
hardware" into a number — run a sim-trained model on clean frames vs the *same*
frames degraded to look like a real camera, and report the gap. It's the
measurement that justifies Lesson 20's domain randomization.

## Concept

- **`nanodrone/degrade.py`** — make a clean sim image look real: `jitter_brightness`
  (dimmer), `blur` (lens softness), `add_noise` (sensor noise), and a combined
  `degrade`. No real camera needed to expose the gap.
- **`measure_gap.py`** — trains Lesson 17's depth CNN on **clean** sim (as every
  earlier lesson did), then scores it on a clean test set vs the same frames put
  through `degrade`. `gap = degraded AbsRel − clean AbsRel` is the sim-to-real
  penalty, made concrete.

The point is the honest number, not a fix — the fix is Lesson 20 (DR), and the
real test is Lesson 24's actual Tello frames.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/25_sim2real/measure_gap.py            # train clean, measure the gap
python lessons/25_sim2real/measure_gap.py --selftest  # tiny run, asserts (local)
```

Read [`nanodrone/degrade.py`](../../nanodrone/degrade.py) and
[`measure_gap.py`](measure_gap.py). Needs PyTorch (uses Lesson 17's net) —
verified locally, not in the torch-free CI.

## Checkpoint ✅

```
SIM2REAL OK: sim AbsRel=0.191, degraded(real-ish) AbsRel=0.265, gap=0.074 measured over 40 frames
```

The self-test asserts the model fits clean sim **and** that the degraded frames
measurably hurt it — a non-zero, quantified sim-to-real gap.

## Going further

- Re-run with Lesson 20's DR-trained model and confirm the gap shrinks.
- Feed real frames from Lesson 24's Tello camera instead of `degrade` — the true
  gap.
- Decide from the number whether to fine-tune on a little real data.

---

<a name="中文"></a>
# Lesson 25 — 誠實量測 sim-to-real 落差

🌐 [English](#lesson-25--measure-the-sim-to-real-gap-honestly) · **繁體中文**（以下）

## 為什麼

課程裡每個模型（L3/L8/L13/L17）都在乾淨 sim 裡訓練與評分。上真機前最誠實的問題：**在真實相機上會掉多少準確度？**
這一課把「上真機會比較差」這句空話變成數字 —— 用 sim 訓的模型跑乾淨影像 vs *同一批*被退化成真實相機樣子的影像，
報出落差。這正是支撐 Lesson 20 域隨機化的量測。

## 概念

- **`nanodrone/degrade.py`** —— 把乾淨 sim 影像變得像真的：`jitter_brightness`（變暗）、`blur`（鏡頭柔化）、
  `add_noise`（感測雜訊），以及合成的 `degrade`。不需真相機就能暴露落差。
- **`measure_gap.py`** —— 在**乾淨** sim 上訓 Lesson 17 的深度 CNN（跟之前每課一樣），再在乾淨測試集
  vs 同一批經 `degrade` 的影像上評分。`gap = 退化 AbsRel − 乾淨 AbsRel` 就是 sim-to-real 代價，具體化。

重點是誠實的數字，不是修法 —— 修法是 Lesson 20（DR），真正的考驗是 Lesson 24 的真實 Tello 影格。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/25_sim2real/measure_gap.py            # 乾淨訓練、量落差
python lessons/25_sim2real/measure_gap.py --selftest  # tiny、會 assert
```

請讀 [`nanodrone/degrade.py`](../../nanodrone/degrade.py) 與 [`measure_gap.py`](measure_gap.py)。
需要 PyTorch（用 Lesson 17 的網路）—— 在本機驗證，不進 CI。

## 驗收 ✅

```
SIM2REAL OK: sim AbsRel=0.191, degraded(real-ish) AbsRel=0.265, gap=0.074 measured over 40 frames
```

自我測試驗證模型在乾淨 sim 上有訓起來，**而且**退化影像會可量測地傷害它 —— 一個非零、量化的 sim-to-real 落差。

## 延伸

- 改用 Lesson 20 DR 訓的模型重跑，確認落差縮小。
- 用 Lesson 24 Tello 相機的真實影格取代 `degrade` —— 真正的落差。
- 用這個數字決定要不要拿少量真實資料 fine-tune。
