# Lesson 18 — Optical flow / visual odometry (no-GPS state estimate)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Teach the drone to track its own motion from camera frames alone, so it can tell where it has flown without any GPS. · **Builds on:** L1, L3, L8, L4

## Why

Every flight loop so far read the simulator's **privileged** position
(`obs[0][0:3]`). The real drone has no such oracle indoors — to know it moved, it
reads its own camera: how the texture *flows* between two frames tells you the
motion. This trains a tiny CNN on a frame pair → body displacement
`(dx, dy, dyaw)`, then integrates those into a dead-reckoned trajectory. Same
"train your own small model" move, on a new modality (motion); it's the state
estimate an offline indoor drone needs (a Flow deck does this in hardware).

## Concept

Two design choices the lesson makes explicit, because both are easy to get wrong:

- **Look down, not forward.** A forward camera has almost no translational flow —
  trained that way the net just predicts the mean. A **downward** camera over
  textured floor (here, scattered tiles) gives clean, learnable flow. That's
  exactly why real optical-flow decks point at the ground.
- **Don't global-pool.** Flow is about *where* texture moved, so `FlowNet` keeps
  the spatial feature map and flattens it — average-pooling it away makes both
  frames look identical and the net can't recover the shift.

`odom_demo.py` integrates the predictions like an odometer. It **drifts** — every
odometer does — and the plot shows the estimate sliding off the true loop.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/18_flow/train_flow.py --samples 320 --epochs 60   # train
python lessons/18_flow/train_flow.py --selftest                   # tiny, asserts
python lessons/18_flow/odom_demo.py                               # save output/odom.png
```

Both need PyTorch, so (like Lessons 3/8/13/14b/17) they're verified locally, not
in the torch-free CI.

## Checkpoint ✅

```
FLOW OK: 220 pairs, vel MAE=0.072 m/s (vs 0.169 predict-mean baseline), int8 footprint=86.6 KB (<512 fits)
ODOM OK: 48 flow updates over 4.4 m path, final drift 0.99 m (22% of distance)
```

`train_flow.py --selftest` asserts the net **clearly beats** the predict-mean
baseline (it really learned flow) and fits GAP8. `odom_demo.py --selftest` asserts
the integrated drift stays a small fraction of the distance flown — it tracked
the loop rather than wandering.

## Going further

- Fuse the flow estimate with the Lesson 11 state machine as a fallback when the
  privileged position isn't available.
- Honest gap: real indoor VO needs a downward camera (Crazyflie Flow deck v2,
  ~US$45) and still drifts — it's fused with an IMU/rangefinder, not used alone.
- Try a scale-invariant or correlation-layer architecture and compare drift.

---

<a name="中文"></a>
# Lesson 18 — 光流 / 視覺里程計（無 GPS 自估狀態）

🌐 [English](#lesson-18--optical-flow--visual-odometry-no-gps-state-estimate) · **繁體中文**（以下）

> **一句話：**教無人機只靠前後兩張影像估出自己動了多少，沒有 GPS 也能知道自己飛到哪裡。 · **建立在：**第 1 課、第 3 課、第 8 課、第 4 課

## 為什麼

到目前為止每個飛行迴圈都讀模擬器的**特權**位置（`obs[0][0:3]`）。真機在室內沒有這個神諭 ——
要知道自己動了多少，得讀自己的相機：紋理在兩幀間怎麼*流動*，就透露了運動。這一課訓一個 tiny CNN
從一對影像 → 機體位移 `(dx, dy, dyaw)`，再把它們積分成 dead-reckoning 軌跡。同樣是「訓你自己的小模型」，
換到新模態（運動）；這正是離線室內無人機需要的狀態估計（Flow deck 用硬體做這件事）。

## 概念

兩個本課刻意點明的設計選擇，因為都很容易做錯：

- **朝下，不要朝前。** 前向相機幾乎沒有平移流 —— 這樣訓出來的網路只會猜均值。**朝下**相機俯視有紋理的地板
  （這裡用撒落的色塊）才有乾淨、可學的流。真實光流感測器朝地正是這個原因。
- **不要 global-pool。** 流的本質是「紋理在*哪裡*移動」，所以 `FlowNet` 保留空間特徵圖再 flatten ——
  平均池化掉就讓兩幀看起來一樣，網路無法還原位移。

`odom_demo.py` 像里程計一樣積分預測。它會**漂移** —— 任何里程計都會 —— 圖上會看到估計軌跡逐漸偏離真實迴圈。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/18_flow/train_flow.py --samples 320 --epochs 60   # 訓練
python lessons/18_flow/train_flow.py --selftest                   # tiny、會 assert
python lessons/18_flow/odom_demo.py                               # 存 output/odom.png
```

兩支都需要 PyTorch，所以（跟 Lesson 3/8/13/14b/17 一樣）在本機驗證，不進 torch-free 的 CI。

## 驗收 ✅

```
FLOW OK: 220 pairs, vel MAE=0.072 m/s (vs 0.169 predict-mean baseline), int8 footprint=86.6 KB (<512 fits)
ODOM OK: 48 flow updates over 4.4 m path, final drift 0.99 m (22% of distance)
```

`train_flow.py --selftest` 驗證網路**明顯贏過** predict-mean baseline（真的學到流）且塞得進 GAP8。
`odom_demo.py --selftest` 驗證積分漂移維持在飛行距離的一小部分 —— 它有跟著迴圈走，而非亂飄。

## 延伸

- 把流估計與 Lesson 11 狀態機融合，當特權位置不可用時的 fallback。
- 誠實的落差：真實室內 VO 需要朝下相機（Crazyflie Flow deck v2，約 US$45）且仍會漂 ——
  它會跟 IMU/測距融合，不單獨使用。
- 試試 scale-invariant 或 correlation-layer 架構，比較漂移。
