# Lesson 21 — Knowledge distillation + compression

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lesson 4 checked a model's footprint and exported it — but stopped there. Lessons
17/20 can grow a depth model bigger than you want on GAP8. The active "make it
fit" step is **knowledge distillation**: train a large, accurate *teacher*, then
train a much smaller *student* to mimic it. The student keeps most of the
accuracy at a fraction of the size. This complements Lesson 14b: 14b *measures*
whether a model fits; this *makes* one fit.

## Concept

`distill_depth.py`:

1. trains the full Lesson 17 `TinyDepthNet` as the **teacher** (on true depth);
2. trains a smaller `StudentDepthNet` (about half the channels) to **match the
   teacher's predictions** — distillation, not relabelling;
3. compares params/footprint and AbsRel, and exports the student to ONNX for the
   GAP8 toolchain.

The student learns from the teacher's soft outputs, which carry more information
than the hard labels — so it lands close to the teacher despite being much
smaller. (Distilling a *single capability* here is the warm-up for Lesson 22,
which distills *several* into one policy.)

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/21_distill/distill_depth.py            # train teacher, distill student
python lessons/21_distill/distill_depth.py --selftest  # tiny run, asserts (local)
```

Read [`distill_depth.py`](distill_depth.py). It builds on Lesson 17's network, so
it needs PyTorch — verified locally, not in the torch-free CI.

## Checkpoint ✅

```
DISTILL OK: teacher 32.9 KB / student 5.2 KB (6.3x smaller, <512 fits), AbsRel teacher=0.167 student=0.212 (kept 79%)
```

The self-test asserts the student is real compression (well under the teacher's
size and the GAP8 budget) **and** keeps most of the accuracy — small and good
enough to run on-board.

## Going further

- Quantize the student to int8 (Lesson 14b) on top of distillation — the two
  compounding.
- Try matching intermediate features, not just outputs (feature distillation).
- Lesson 22 distills *multiple* teachers (avoid + follow) into one on-board policy.

---

<a name="中文"></a>
# Lesson 21 — 知識蒸餾 + 模型壓縮

🌐 [English](#lesson-21--knowledge-distillation--compression) · **繁體中文**（以下）

## 為什麼

Lesson 4 檢查了模型 footprint 並匯出 —— 但就停在那。Lesson 17/20 可能把深度模型養得比你想在 GAP8 上跑的還大。
主動「讓它塞得下」的一步就是**知識蒸餾**：訓一個大而準的 *teacher*，再訓一個小很多的 *student* 去模仿它。
student 以一小部分的大小保留大部分準確度。這與 Lesson 14b 互補：14b *量測*塞不塞得下；這一課*讓*它塞得下。

## 概念

`distill_depth.py`：

1. 把完整的 Lesson 17 `TinyDepthNet` 當 **teacher** 訓練（用真實深度）；
2. 訓一個更小的 `StudentDepthNet`（通道約砍半）去**匹配 teacher 的預測** —— 是蒸餾，不是重新貼標籤；
3. 比較參數量/footprint 與 AbsRel，並把 student 匯出 ONNX 給 GAP8 工具鏈。

student 從 teacher 的軟輸出學習，軟輸出比硬標籤帶更多資訊 —— 所以雖然小很多，仍能逼近 teacher。
（這裡蒸餾*單一*能力，是 Lesson 22 把*多個*能力蒸餾成一個策略的暖身。）

## 動手做

```bash
conda activate nanodrone-ai
python lessons/21_distill/distill_depth.py            # 訓 teacher、蒸餾 student
python lessons/21_distill/distill_depth.py --selftest  # tiny、會 assert
```

請讀 [`distill_depth.py`](distill_depth.py)。它建在 Lesson 17 的網路上，需要 PyTorch —— 在本機驗證，不進 CI。

## 驗收 ✅

```
DISTILL OK: teacher 32.9 KB / student 5.2 KB (6.3x smaller, <512 fits), AbsRel teacher=0.167 student=0.212 (kept 79%)
```

自我測試驗證 student 是真壓縮（遠小於 teacher 與 GAP8 預算）**而且**保留大部分準確度 —— 小到能上板、又夠好。

## 延伸

- 在蒸餾之上再把 student 量化成 int8（Lesson 14b），兩者疊加。
- 試試匹配中間特徵而非只匹配輸出（feature distillation）。
- Lesson 22 把*多個* teacher（避障 + 跟隨）蒸餾成一個板載策略。
