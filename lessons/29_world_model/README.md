# Lesson 29 — Nano world model: latent-space prediction for proactive avoidance

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Every model so far has been *reactive*: the depth net (Lesson 17) and the RL
policy (Lesson 19) both answer "what should I do about the obstacle that is close
**now**?" But at speed, "now" is already too late — by the time a pillar fills the
frame, a 27 g drone with bounded acceleration cannot turn hard enough to miss it.

A **world model** buys you the missing ingredient: *anticipation*. It learns how
the world will change and lets the drone act on what is **about to** happen. This
is the frontier the course has been pointing at — the same problem self-driving
research now attacks with world models.

The trap is to build it by predicting the **next image** (diffusion / pixel
generation). That is slow and it hallucinates detail a controller can't use. We
take the **V-JEPA** route instead — *predict the next latent embedding, never the
next pixels*. No hallucinated frames, no diffusion latency, a fixed compute cost.

And the signature move returns, at the frontier this time: the real V-JEPA is a
billion-parameter model that needs an Orin-class GPU — it will **never** fit on a
GAP8. So you don't download it; you **train your own nano version** and distil it
under the 512 KB int8 budget.

## Concept

Three tiny networks, all reusing the course's existing conv stack, all int8-able:

- **Encoder** `f_θ`: image → a 64-d latent `z` (Lesson 3's `TinyDronet` conv
  stack, the same features Lesson 17's depth net used).
- **Predictor** `g_φ`: `(z_t, action) → ẑ_{t+k}` — a small MLP that predicts the
  **residual** (`ẑ = z_t + Δ`), so "nothing changes" is the free baseline and any
  learned motion can only improve on it.
- **Collision head**: `ẑ → P(too close within k steps)` — one linear layer. This
  is the *anticipation* signal.

The trick that makes latent prediction work without a pixel loss (and without
collapsing to a constant) is a **target encoder**: an EMA copy of `f_θ` with a
stop-gradient, à la V-JEPA / BYOL. A VICReg-style variance term is a second guard.
The whole loss is just:

```
‖ g_φ(f_θ(x_t), a_t) − sg(f_EMA(x_{t+k})) ‖²   +   variance-guard   +   BCE(collision)
```

**Why latent (V-JEPA), not explicit 4D geometry (4D-GS)?** Both are world models;
they sit at opposite ends of the trade-off.

| | **V-JEPA (this lesson)** | **4D Gaussian Splatting** |
|---|---|---|
| Represents | an implicit *latent* manifold | explicit metric 3D + time geometry |
| Predicts | the future *embedding* | renders the future *scene* |
| Strength | anticipation, abstraction, **bounded latency** | metric precision, photorealism |
| Cost | fixed FLOPs, **distils to int8 < 512 KB** | scales with #Gaussians → Orin-class |
| Hallucination | none (no pixels committed) | geometric "floaters" when extrapolating |

4D-GS is the heavyweight explicit-geometry cousin of the **2D occupancy grid you
built in Lesson 14a** — extended to 3D and time. It is wonderful for metric
precision but it does not fit on a GAP8. V-JEPA is the latent path that does, which
is why it is our on-board backbone. (See *Going further* for a hybrid that uses
4D-GS offline to metric-ground the latent prediction — a research-grade idea.)

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/29_world_model/gen_wm_dataset.py --rollouts 20   # 1. fly + record clips
python lessons/29_world_model/train_world_model.py --epochs 80  # 2. train the nano V-JEPA
python lessons/29_world_model/proactive_avoid.py               # 3. proactive vs reactive
```

Read [`train_world_model.py`](train_world_model.py) — the `Encoder` / `Predictor`
/ `CollisionHead` and the EMA target — then [`gen_wm_dataset.py`](gen_wm_dataset.py)
(how the *sequence* data is made) and [`proactive_avoid.py`](proactive_avoid.py)
(what the look-ahead buys you). Each script self-generates its data, so any step
runs on its own with `--selftest`.

## Checkpoint ✅

`train_world_model.py --selftest` trains a tiny nano V-JEPA and prints (measured
locally):

```
WORLD-MODEL OK: trained 333 seqs, latent MSE=0.40 (no-op baseline 4.54), collision AUC=0.89, int8 footprint=40.5 KB (<512 fits), saved .../output/world_model.pth
```

It asserts the predictor **beats the "future == present" no-op baseline**, the
collision head predicts danger (AUC > 0.70), and the on-board footprint fits the
GAP8 budget. Then `proactive_avoid.py --selftest` flies the same course twice and
prints:

```
PROACTIVE OK: reactive min-clear=0.32 m (avoid@step 12), proactive min-clear=0.60 m (avoid@step 0), lead=+12 steps (~600ms earlier), crashes reactive/proactive = 0/0
```

It asserts the proactive rule **triggers earlier** and keeps **more clearance**
(here ~2×) without crashing — the payoff of anticipation.

## Going further

- **Metric-ground the latent (research-grade, the academic angle).** JEPA's weak
  spot is that a latent has no direct metric meaning. Use **4D-GS offline** (in
  sim / on an Orin workstation) to produce geometry-consistent occupancy, and add
  a *geometry-grounded latent-prediction loss* so `ẑ_{t+k}` decodes to a
  collision-checkable distance. That gives V-JEPA's latency with 4D-GS's grounding
  — a genuine ICRA/CVPR-flavoured contribution.
- **Close the loop with vision.** `proactive_avoid.py` uses the simulator's
  privileged look-ahead (the honest Lesson 13 convention); swap in the trained
  collision head so the danger signal comes from the camera alone.
- **Feed it to the policy.** Add the predicted "time-to-collision" to Lesson 19's
  RL observation — a learned proactive avoider instead of a hand-coded veer.
- **Honest gap.** This is a *nano distillation of the idea*. The real V-JEPA 2 /
  4D-GS are Orin-class; here we teach the principle under the GAP8 budget.

---

<a name="中文"></a>
# Lesson 29 — nano 世界模型：隱空間預測做預判式避障

🌐 [English](#lesson-29--nano-world-model-latent-space-prediction-for-proactive-avoidance) · **繁體中文**（以下）

## 為什麼

目前為止每個模型都是**反應式**的：深度網路（Lesson 17）與 RL 策略（Lesson 19）回答的都是
「對**現在**已經很近的障礙我該怎麼辦？」但在高速下，「現在」已經太遲——等柱子塞滿畫面，
一台加速度有上限的 27 克無人機根本轉不過來。

**世界模型**補上缺的那一塊：**預判（anticipation）**。它學會世界將如何變化，讓無人機對
**即將**發生的事先動作。這正是本課一路指向的前沿——也是自駕研究如今用世界模型攻堅的問題。

陷阱是用「預測下一張影像」（擴散／像素生成）來做，那既慢又會幻想出控制器根本用不到的細節。
我們改走 **V-JEPA** 路線——**預測下一個隱空間 embedding，而不是下一格像素**。沒有幻覺影格、
沒有擴散延遲、算力固定。

而招牌動作在前沿再現一次：真正的 V-JEPA 是十億參數、需要 Orin 級 GPU 的大模型，**永遠**塞不進
GAP8。所以你不是下載它，而是**訓練你自己的 nano 版**，蒸餾到 512KB int8 預算之內。

## 概念

三個小網路，全部沿用課程既有的 conv stack，全部可 int8：

- **Encoder** `f_θ`：影像 → 64 維隱向量 `z`（Lesson 3 `TinyDronet` 的 conv stack，
  也就是 Lesson 17 深度網用的那組特徵）。
- **Predictor** `g_φ`：`(z_t, action) → ẑ_{t+k}`——一個小 MLP，預測**殘差**（`ẑ = z_t + Δ`），
  於是「什麼都不變」是免費的基線，任何學到的運動只會更好。
- **Collision head**：`ẑ → P(k 步內太靠近)`——一層 linear。這就是**預判**訊號。

讓隱空間預測「不用像素 loss 也不塌縮成常數」的關鍵，是一個 **target encoder**：`f_θ` 的
EMA 複本加上 stop-gradient（V-JEPA / BYOL 的做法）。再加一個 VICReg 式的變異數項當第二道護欄。
整個 loss 就是：

```
‖ g_φ(f_θ(x_t), a_t) − sg(f_EMA(x_{t+k})) ‖²   +   變異數護欄   +   BCE(collision)
```

**為什麼選隱空間（V-JEPA），而非顯式 4D 幾何（4D-GS）？** 兩者都是世界模型，但在權衡的兩端。

| | **V-JEPA（本課）** | **4D Gaussian Splatting** |
|---|---|---|
| 表徵 | 隱式*隱空間*流形 | 顯式度量 3D + 時間幾何 |
| 預測 | 未來的*embedding* | 渲染未來的*場景* |
| 強項 | 預判、抽象、**延遲有上限** | 度量精準、擬真 |
| 成本 | 定長 FLOP、**可蒸餾成 int8 < 512KB** | 隨 Gaussian 數擴張 → Orin 級 |
| 幻覺 | 無（不 commit 像素） | 外推時出現幾何 floater |

4D-GS 是你在 **Lesson 14a 建的 2D occupancy grid** 的重量級顯式幾何表親——延伸到 3D 加時間。
它度量精準得很美，卻塞不進 GAP8。V-JEPA 是塞得進的隱空間路線，所以是我們的機上骨幹。
（*延伸*裡有一個用 4D-GS 離線把隱空間預測「度量接地」的 hybrid——研究級的點子。）

## 動手做

```bash
conda activate nanodrone-ai
python lessons/29_world_model/gen_wm_dataset.py --rollouts 20   # 1. 飛行並錄製片段
python lessons/29_world_model/train_world_model.py --epochs 80  # 2. 訓練 nano V-JEPA
python lessons/29_world_model/proactive_avoid.py               # 3. 預判式 vs 反應式
```

請讀 [`train_world_model.py`](train_world_model.py)——`Encoder` / `Predictor` /
`CollisionHead` 與 EMA target——再看 [`gen_wm_dataset.py`](gen_wm_dataset.py)
（*序列*資料怎麼產）與 [`proactive_avoid.py`](proactive_avoid.py)（look-ahead 買到什麼）。
每支腳本都會自產資料，所以任一步都能用 `--selftest` 獨立跑。

## 驗收 ✅

`train_world_model.py --selftest` 訓練一個 tiny nano V-JEPA 並印出（本機實測）：

```
WORLD-MODEL OK: trained 333 seqs, latent MSE=0.40 (no-op baseline 4.54), collision AUC=0.89, int8 footprint=40.5 KB (<512 fits), saved .../output/world_model.pth
```

它驗證 predictor **贏過「未來＝現在」的 no-op 基線**、collision head 能預測危險（AUC > 0.70）、
且機上 footprint 塞得進 GAP8 預算。接著 `proactive_avoid.py --selftest` 在同一條航道飛兩次並印出：

```
PROACTIVE OK: reactive min-clear=0.32 m (avoid@step 12), proactive min-clear=0.60 m (avoid@step 0), lead=+12 steps (~600ms earlier), crashes reactive/proactive = 0/0
```

它驗證預判規則**更早觸發**、保住**更多淨空**（這裡約 2×）且不墜機——這就是預判的回報。

## 延伸

- **把隱空間度量接地（研究級，學術亮點）。** JEPA 的弱點是隱空間沒有直接的度量意義。
  用 **4D-GS 離線**（在 sim／Orin 工作站）產生幾何一致的 occupancy，再加一個
  *geometry-grounded latent-prediction loss*，讓 `ẑ_{t+k}` 能解碼成可做碰撞檢測的距離。
  這就用 V-JEPA 的延遲換到 4D-GS 的接地——一個真正 ICRA/CVPR 級的貢獻。
- **用視覺閉環。** `proactive_avoid.py` 用的是模擬器的 privileged look-ahead（誠實的 Lesson 13
  慣例）；把訓練好的 collision head 換進去，讓危險訊號只來自相機。
- **餵給策略。** 把預測的 time-to-collision 加進 Lesson 19 的 RL 觀測——用學出來的預判避障，
  取代手寫的閃避。
- **誠實的落差。** 這是**該想法的 nano 蒸餾版**。真正的 V-JEPA 2 / 4D-GS 是 Orin 級；
  這裡是在 GAP8 預算下教原理。
