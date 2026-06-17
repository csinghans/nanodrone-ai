# Lesson 3 — Autonomous decision AI

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lesson 1 made the drone *move*; Lesson 2 made it *see*. Lesson 3 closes the loop:
the drone now **decides** for itself. This is the heart of the course — the
"decide" in *sense → decide → act* — and we tackle it two ways:

- **Route A (main): reinforcement learning.** The drone learns obstacle
  avoidance from scratch, by trial and error, guided only by a reward.
- **Route B: imitation learning.** A small neural network learns to replace
  Lesson 2's hand-written detector — the bridge to the real AI-deck in Lesson 4.

## Concept

**Route A — RL.** We don't tell the drone *how* to avoid the obstacle. We define
a task in [`avoid_aviary.py`](avoid_aviary.py): start here, reach the goal, a
reward for **progress** toward the goal, a penalty for hitting the pillar. PPO
(from Stable-Baselines3) explores and gradually discovers a path that arcs
around. Two ideas that made it actually learn:

- **Progress reward, not distance reward.** Rewarding "closer to goal each step"
  beats rewarding "be near the goal" (which lets it park in a comfy spot).
- **No wide repulsive zone + exploration bonus (`ent_coef`).** A big keep-away
  penalty punishes the very sideways motion the detour needs, trapping the
  policy in "don't move". We only penalize an actual crash, and keep PPO
  exploring long enough to stumble onto going around.

> Simplification: the start/obstacle/goal are **fixed**, so the drone's own
> position (the kinematic observation) is enough. To generalize to *new* layouts
> you'd add the obstacle's position to the observation — see *Going further*.

**Route B — imitation.** Where do training labels come from? From Lesson 2's
detector — it's the **teacher**. [`gen_dataset.py`](gen_dataset.py) moves the
obstacle around, captures the camera image, and records the detector's bearing
as the label. [`train_cnn.py`](train_cnn.py) then trains `TinyDronet`, a compact
CNN, to predict that bearing from raw pixels. This mirrors **PULP-Dronet**, the
research project that runs a CNN on the Crazyflie AI-deck — exactly what Lesson 4
deploys.

## Hands-on

**Route A — RL:**

```bash
conda activate nanodrone-ai
python lessons/03_autonomy_ai/train_rl.py                    # train + evaluate + plot
python lessons/03_autonomy_ai/train_rl.py --eval-only --gui  # watch the saved policy
```

Training ~200k–600k steps takes a couple of minutes (PPO on an MLP runs on CPU,
~2600 steps/s here). It saves `output/ppo_avoid.zip` and a top-down
`output/trajectory.png` of the learned path.

**Route B — imitation:**

```bash
python lessons/03_autonomy_ai/gen_dataset.py --samples 500   # build dataset (teacher = Lesson 2)
python lessons/03_autonomy_ai/train_cnn.py --epochs 100      # train the CNN (uses Apple GPU / MPS)
```

## Checkpoint ✅

**Route A** — evaluation prints (verified on this machine, 600k steps):

```
[EVAL] 20 episodes: 20 reached goal, 0 crashed (success rate 100%).
```

Open `output/trajectory.png`: the blue path should bow out in y and curve around
the red obstacle to the goal — a route nobody programmed.

**Route B** — training prints a falling validation error, ending near:

```
  epoch 100  val MAE = 2.16 deg
```

and a table where the CNN's predicted bearings track the teacher's within a few
degrees. The network learned to "see" the obstacle direction from pixels alone.

## Going further

- **Generalize the RL policy:** randomize `OBSTACLE_POS`/`GOAL_POS` each episode
  and add the obstacle's relative position to the observation (override
  `_computeObs`). Fixed-layout → memorization; randomized → real navigation.
- **Close the loop with vision:** feed the Route-B CNN's bearing into a simple
  steering rule (or into the RL observation) so the drone avoids using *its own
  eyes* instead of ground-truth positions.
- **Shrink for hardware:** quantize `TinyDronet` and measure its size — this is
  the first step toward fitting it on the GAP8 chip in Lesson 4.

---

<a name="中文"></a>
# Lesson 3 — 自主決策 AI

🌐 [English](#lesson-3--autonomous-decision-ai) · **繁體中文**（以下）

## 為什麼

Lesson 1 讓無人機會**動**；Lesson 2 讓它會**看**。Lesson 3 把迴圈接起來：無人機開始自己**決策**。這是整門課的核心 —— *感知 → 決策 → 動作* 裡的「決策」—— 我們用兩條路線來做：

- **Route A（主線）：強化學習。** 無人機從零開始、靠試誤學會避障，只靠一個獎勵引導。
- **Route B：模仿學習。** 一個小神經網路學著取代 Lesson 2 的手寫偵測器 —— 這是通往 Lesson 4 真實 AI-deck 的橋樑。

## 概念

**Route A — RL。** 我們不告訴無人機「怎麼」避障，只在 [`avoid_aviary.py`](avoid_aviary.py) 裡定義任務：從起點出發、抵達目標、**朝目標前進**有獎勵、撞到柱子有懲罰。PPO（來自 Stable-Baselines3）自行探索，漸漸發現一條繞過去的弧線。讓它「真的學得會」的兩個關鍵：

- **用「進度」獎勵，而非「距離」獎勵。** 獎勵「每步更靠近目標」遠勝於獎勵「待在目標附近」（後者會讓它停在舒服的位置不動）。
- **不要大範圍排斥區 + 探索獎勵（`ent_coef`）。** 大範圍的「遠離」懲罰會壓制繞道所需的側向移動，把策略困在「乾脆別動」。我們只在**真的撞上**才罰，並讓 PPO 探索久一點，才會碰巧發現繞過去。

> 簡化：起點／障礙／目標是**固定**的，所以光靠無人機自己的位置（KIN 觀測）就夠。要推廣到**新佈局**，得把障礙位置加進觀測 —— 見「延伸」。

**Route B — 模仿。** 訓練標籤哪來？來自 Lesson 2 的偵測器 —— 它就是**老師**。[`gen_dataset.py`](gen_dataset.py) 把障礙物到處移動、擷取相機影像、把偵測器算出的方位當標籤記下來。[`train_cnn.py`](train_cnn.py) 接著訓練 `TinyDronet`（一個精簡 CNN）從原始像素預測方位。這正是 **PULP-Dronet** 的縮影 —— 那個在 Crazyflie AI-deck 上跑 CNN 的研究專案，也正是 Lesson 4 要部署的東西。

## 動手做

**Route A — RL：**

```bash
conda activate nanodrone-ai
python lessons/03_autonomy_ai/train_rl.py                    # 訓練 + 評估 + 畫軌跡
python lessons/03_autonomy_ai/train_rl.py --eval-only --gui  # 觀看已訓練策略飛行
```

訓練約 200k–600k 步、幾分鐘內完成（PPO 用 MLP 跑在 CPU 上，本機約每秒 2600 步）。會存下 `output/ppo_avoid.zip` 與俯視軌跡圖 `output/trajectory.png`。

**Route B — 模仿：**

```bash
python lessons/03_autonomy_ai/gen_dataset.py --samples 500   # 產生資料集（老師＝Lesson 2）
python lessons/03_autonomy_ai/train_cnn.py --epochs 100      # 訓練 CNN（用 Apple GPU / MPS）
```

## 驗收 ✅

**Route A** —— 評估會印出（本機實測，600k 步）：

```
[EVAL] 20 episodes: 20 reached goal, 0 crashed (success rate 100%).
```

打開 `output/trajectory.png`：藍色路徑應在 y 方向鼓出、繞過紅色障礙再到目標 —— 一條沒有人寫死的路線。

**Route B** —— 訓練會印出逐漸下降的驗證誤差，最後接近：

```
  epoch 100  val MAE = 2.16 deg
```

並有一張表，CNN 預測的方位與老師相差僅幾度。這個網路學會了**單憑像素**「看出」障礙物方向。

## 延伸

- **讓 RL 策略能泛化：** 每回合隨機化 `OBSTACLE_POS`／`GOAL_POS`，並把障礙的相對位置加進觀測（覆寫 `_computeObs`）。固定佈局 → 死背；隨機化 → 真正的導航。
- **用視覺閉環：** 把 Route B 的 CNN 方位輸出餵進一個簡單轉向規則（或進 RL 觀測），讓無人機用**自己的眼睛**避障，而非吃地面真值位置。
- **為硬體瘦身：** 把 `TinyDronet` 量化並量測大小 —— 這是 Lesson 4 把它塞進 GAP8 晶片的第一步。
