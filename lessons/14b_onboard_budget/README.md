# Lesson 14b — Perception under the on-board budget (sew it back to GAP8)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lessons 11–14a were all host-side, sim-only orchestration — they quietly drifted
away from the course's whole point: a neural net running **on the drone**,
offline, in int8, under 512 KB. This lesson sews the new capabilities back to
that target. It takes Lesson 13's confirm classifier and the Lesson 14a map and
asks the three honest on-board questions:

1. Does the model fit GAP8 in int8, and what accuracy does int8 cost?
2. Real inference takes milliseconds — does the mission still track when the
   drone can only *look* that often?
3. Does the map's memory fit too?

This is the bridge between "clever desktop simulation" and "runs on the AI-deck."

## Concept

- **`quantize_confirm.py`** reuses Lesson 4's footprint math on Lesson 13's
  `ConfirmCNN`: float32 vs int8 size, a real measured accuracy drop (per-tensor
  8-bit quantize-then-dequantize of every weight), and an ONNX export for the
  GAP8 NNTool flow. (`PERCEPTION_EVERY=6` in Lesson 13 was a hand-tuned guess;
  this is where you'd justify it.)
- **`latency_sim.py`** re-runs Lesson 13's find/follow mission with perception
  **throttled to one inference per latency** (a heavier model = fewer looks per
  second) and plots tracking error vs latency. It also reports the occupancy
  grid's int8 memory against GAP8's L2.

It changes no flight code — it measures the existing capability against silicon
limits. The honest gap is loud here: the sim is perfect ground truth; the real
AI-deck has a grayscale camera, sensor noise and a hard clock (→ domain
randomization, later).

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/13_find_follow_land/train_confirm.py   # needs L13's model first
python lessons/14b_onboard_budget/quantize_confirm.py    # fit + accuracy + ONNX
python lessons/14b_onboard_budget/latency_sim.py          # latency -> tracking error
# both take --selftest for the asserted, headless run
```

Read [`quantize_confirm.py`](quantize_confirm.py) (footprint + int8 cost) and
[`latency_sim.py`](latency_sim.py) (the latency sweep). Both need PyTorch, so —
like Lessons 3/8 training — they're verified locally, not in the torch-free CI.

## Checkpoint ✅

```
QUANT OK: int8 model 25.8 KB < 512 KB budget, val acc fp32 1.00 -> int8 1.00 (drop 0.00), ONNX 105.6 KB
LATENCY OK: 20ms->14.6deg, 80ms->12.9deg, 160ms->62.8deg (tracking error grows with inference latency); grid 20x20 int8 = 0.4 KB fits 256 KB
```

`quantize_confirm --selftest` asserts the int8 model fits and the accuracy drop
is small; `latency_sim --selftest` asserts tracking stays bounded at low latency
and blows up as inference slows — the quantitative reason `PERCEPTION_EVERY`
can't just be 1 on real hardware.

## Going further

- Run the real int8 conversion on the GAP8 NNTool (Linux + GAP SDK, Lesson 4)
  and compare its accuracy drop to the estimate here.
- Measure actual GAP8 inference latency and mark it on the curve.
- The low-latency floor (~14°) is the PID's yaw-tracking lag, not perception —
  tightening it is a controls problem, separate from the compute budget.

---

<a name="中文"></a>
# Lesson 14b — 板載預算下的感知（把能力縫回 GAP8）

🌐 [English](#lesson-14b--perception-under-the-on-board-budget-sew-it-back-to-gap8) · **繁體中文**（以下）

## 為什麼

Lesson 11–14a 全是 host 端、純模擬的編排 —— 它們悄悄偏離了整門課的核心目標：神經網路跑在
**無人機上**、離線、int8、512 KB 以內。這一課把新能力縫回那個目標。它拿 Lesson 13 的確認分類器
與 Lesson 14a 的地圖，問三個誠實的板載問題：

1. 模型 int8 塞得進 GAP8 嗎？int8 要付出多少精度？
2. 真實推論要花毫秒 —— 當無人機只能*這麼頻繁地看*時，任務還追得住嗎？
3. 地圖的記憶體也塞得下嗎？

這是「聰明的桌面模擬」與「真的跑在 AI-deck 上」之間的橋。

## 概念

- **`quantize_confirm.py`** 把 Lesson 4 的 footprint 算法套到 Lesson 13 的 `ConfirmCNN`：
  float32 vs int8 大小、實測的精度掉幅（把每個權重做 per-tensor 8-bit 量化再還原）、以及給 GAP8 NNTool
  的 ONNX 匯出。（Lesson 13 的 `PERCEPTION_EVERY=6` 是手調的猜測 —— 這裡正是替它找理由的地方。）
- **`latency_sim.py`** 重跑 Lesson 13 的找人/跟隨任務，把感知**節流成「每個延遲只能推論一次」**
  （更重的模型 = 每秒看的次數更少），畫出追蹤誤差 vs 延遲的曲線，並把佔據格的 int8 記憶體跟 GAP8 的 L2 對照。

它不改任何飛行程式 —— 只是拿既有能力去量對矽晶限制。誠實的落差在這裡很大聲：模擬是完美的 ground truth；
真實 AI-deck 是灰階相機、有感測雜訊、有硬時鐘（→ 之後的 domain randomization）。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/13_find_follow_land/train_confirm.py   # 先要有 L13 的模型
python lessons/14b_onboard_budget/quantize_confirm.py    # 塞得下嗎 + 精度 + ONNX
python lessons/14b_onboard_budget/latency_sim.py          # 延遲 → 追蹤誤差
# 兩支都可加 --selftest 做有 assert 的 headless 執行
```

請讀 [`quantize_confirm.py`](quantize_confirm.py)（footprint + int8 代價）與
[`latency_sim.py`](latency_sim.py)（延遲掃描）。兩支都需要 PyTorch，所以 —— 跟 Lesson 3／8 的訓練一樣 ——
在本機驗證，不進 torch-free 的 CI。

## 驗收 ✅

```
QUANT OK: int8 model 25.8 KB < 512 KB budget, val acc fp32 1.00 -> int8 1.00 (drop 0.00), ONNX 105.6 KB
LATENCY OK: 20ms->14.6deg, 80ms->12.9deg, 160ms->62.8deg (tracking error grows with inference latency); grid 20x20 int8 = 0.4 KB fits 256 KB
```

`quantize_confirm --selftest` 驗證 int8 模型塞得下、精度掉幅很小；`latency_sim --selftest` 驗證
低延遲時追蹤誤差有界、推論變慢時就崩掉 —— 這就是 `PERCEPTION_EVERY` 在真機上不能直接設成 1 的量化理由。

## 延伸

- 在 GAP8 NNTool 上跑真正的 int8 轉換（Linux + GAP SDK，Lesson 4），把它的精度掉幅跟這裡的估計對照。
- 量真實 GAP8 推論延遲，標到曲線上。
- 低延遲的下限（~14°）是 PID 的 yaw 追蹤延遲，不是感知 —— 收緊它是控制問題，跟算力預算無關。
