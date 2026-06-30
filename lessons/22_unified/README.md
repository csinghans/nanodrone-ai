# Lesson 22 — Distill multiple skills into one on-board policy (Track B capstone)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Avoidance (Lesson 19) and following (Lesson 8) are separate networks and loops.
On GAP8 you can't run several nets and switch between them mid-flight — there's
room for **one** small policy. So we **distill**: let the specialist teachers
demonstrate `observation → action`, and train a single student network to imitate
all of them. This closes the on-board AI thread — every self-trained small model
from Lessons 17–21 folded into one brain that fits. (It's the *on-board* capstone,
complementing Lesson 16's *host-side* mission capstone.)

## Concept

`distill_policy.py` runs the distillation pipeline:

- **teachers** demonstrate `(observation → action)` — avoid the nearest obstacle,
  or steer to the target — combined into one behaviour (avoid when an obstacle is
  close, else follow);
- a single small `UnifiedPolicy` MLP is trained to **imitate** the combined
  demonstrations;
- it's scored on imitation error, on whether it actually avoids inside the danger
  zone, and on int8 footprint.

For a robust, self-contained run the teachers here are compact reference
controllers; **the same pipeline takes Lesson 19's PPO policy and Lesson 8's
follower as the teachers** in a full run — the student doesn't care where the
demonstrations came from.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/22_unified/distill_policy.py            # distill + report
python lessons/22_unified/distill_policy.py --selftest  # asserts (local)
```

Read [`distill_policy.py`](distill_policy.py) — the two teachers, the combined
behaviour, and the one student. Needs PyTorch — verified locally, not in the
torch-free CI.

## Checkpoint ✅

```
UNIFIED OK: distilled 2 teachers (avoid+follow) into one policy, imitation MSE=0.025, avoids in 100% of danger states, single int8=1.3 KB (<512 fits)
```

The self-test asserts the one policy imitates the teachers (low MSE), genuinely
**avoids** when an obstacle is close (not just averages the two behaviours), and
fits GAP8 — a single, tiny, deployable brain.

## Going further

- Swap the reference teachers for Lesson 19's trained PPO policy and Lesson 8's
  follower (same pipeline) and fly the unified policy in sim.
- Quantize it (Lesson 14b) and run it as the on-board reflex under DroneVoice
  Phase 5b's high-level commands.
- Add a third skill (e.g. "return home") and watch one network absorb it.

---

<a name="中文"></a>
# Lesson 22 — 把多個能力蒸餾成單一板載策略（Track B 畢業專題）

🌐 [English](#lesson-22--distill-multiple-skills-into-one-on-board-policy-track-b-capstone) · **繁體中文**（以下）

## 為什麼

避障（Lesson 19）與跟隨（Lesson 8）是分開的網路與迴圈。在 GAP8 上你沒辦法同時跑好幾個網路、飛行中切換 ——
只放得下**一個**小策略。所以我們**蒸餾**：讓專家 teacher 示範 `觀測 → 動作`，訓一個 student 網路模仿全部。
這收束了板載 AI 主線 —— Lesson 17–21 每個自訓小模型，疊進一個塞得下的大腦。
（這是*板載*畢業專題，與 Lesson 16 的*host 端*任務畢業專題互補。）

## 概念

`distill_policy.py` 跑蒸餾 pipeline：

- **teacher** 示範 `(觀測 → 動作)` —— 避開最近障礙、或朝目標 —— 合成一個行為（障礙近就避，否則跟）；
- 訓一個小 `UnifiedPolicy` MLP **模仿**合成示範；
- 用模仿誤差、危險區是否真的避障、int8 footprint 來評分。

為了穩健、自足，這裡的 teacher 是精簡的參考控制器；**同一套 pipeline 在完整跑時會把 Lesson 19 的 PPO policy
與 Lesson 8 的跟隨器當 teacher** —— student 不在乎示範從哪來。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/22_unified/distill_policy.py            # 蒸餾 + 報告
python lessons/22_unified/distill_policy.py --selftest  # 驗收（本機）
```

請讀 [`distill_policy.py`](distill_policy.py) —— 兩個 teacher、合成行為、一個 student。需要 PyTorch —— 在本機驗證，不進 CI。

## 驗收 ✅

```
UNIFIED OK: distilled 2 teachers (avoid+follow) into one policy, imitation MSE=0.025, avoids in 100% of danger states, single int8=1.3 KB (<512 fits)
```

自我測試驗證單一策略模仿了 teacher（低 MSE）、障礙靠近時真的**避開**（而非只是平均兩種行為）、且塞得進 GAP8 ——
一個小巧、可部署的單一大腦。

## 延伸

- 把參考 teacher 換成 Lesson 19 訓好的 PPO policy 與 Lesson 8 的跟隨器（同一套 pipeline），在 sim 裡飛統一策略。
- 量化它（Lesson 14b），當 DroneVoice Phase 5b 高階指令下的板上 reflex 跑。
- 加第三個能力（例如「返航」），看一個網路把它吸收進去。
