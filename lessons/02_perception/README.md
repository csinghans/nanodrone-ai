# Lesson 2 — Perception (seeing an obstacle)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

A drone that can only follow fixed waypoints (Lesson 1) is blind. Before it can
*decide* where to go (Lesson 3), it has to *perceive* the world. This lesson
gives the drone a camera and teaches it to answer the two questions that matter
about any obstacle: **how far away** and **in which direction**.

## Concept

Real drones perceive with cameras and depth sensors. We simulate exactly that:

- **RGB image** — what the forward camera sees. We find the obstacle in it.
- **Depth image** — how far each pixel is. We read distance from it.

The pipeline is the classic computer-vision recipe, and it's the **"sense"**
stage of *sense → decide → act*:

1. **Threshold** the red pixels (OpenCV HSV color mask) → a binary mask.
2. **Find the blob** (largest contour) and its **centroid**.
3. **Bearing** comes from the centroid's horizontal position within the 60° FOV
   (a pinhole-camera angle).
4. **Distance** comes from the depth image sampled at the centroid — after
   converting PyBullet's non-linear depth buffer into metres.

> Why a bright red box? Color thresholding is the simplest perception that
> *works*, so you can focus on the pipeline. Lesson 3 replaces this hand-written
> detector with a neural network.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/02_perception/perception_demo.py            # opens a window
python lessons/02_perception/perception_demo.py --headless # no window (CI)
```

Read [`perception_demo.py`](perception_demo.py) — `detect_obstacle()` is the
heart of it, and `linearize_depth()` shows the one formula beginners always
trip on (a depth buffer is **not** a distance).

It also saves two images to `output/`:

- `camera_rgb.png` — the raw camera view.
- `detection.png` — the same view with the detected box, centroid, and a
  `distance / bearing` label drawn on top.

## Checkpoint ✅

Console prints something like:

```
Obstacle detected: 1.80 m ahead, bearing -12.2 deg (left).
```

The box sits 2 m ahead and 0.4 m to one side, so ~1.8 m and ~12° **left** is
correct. Open `output/detection.png` and confirm the green box is drawn tightly
around the red obstacle.

## Going further

- Move `OBSTACLE_POS` and confirm distance and bearing change as expected
  (e.g. put it dead ahead → bearing ≈ 0°).
- Change the obstacle's color and update the HSV ranges in `detect_obstacle()`.
- **Challenge:** combine this with Lesson 1 — if an obstacle is detected closer
  than 1 m, command the drone to stop. That tiny `if` is your first *autonomous
  decision*, and it's exactly what Lesson 3 learns to do with a neural network.

---

<a name="中文"></a>
# Lesson 2 — 感知（看見障礙物）

🌐 [English](#lesson-2--perception-seeing-an-obstacle) · **繁體中文**（以下）

## 為什麼

只會照固定航點飛的無人機（Lesson 1）是「瞎」的。在它能**決定**往哪飛（Lesson 3）之前，得先**感知**世界。這一課給無人機一台相機，教它回答對任何障礙物最關鍵的兩個問題：**有多遠**、**在哪個方向**。

## 概念

真實無人機用相機與深度感測器來感知，我們模擬的正是這個：

- **RGB 影像** — 前向相機看到的畫面，我們在裡面找出障礙物。
- **深度影像** — 每個像素有多遠，我們從中讀出距離。

整條流程就是經典電腦視覺套路，也是 *感知 → 決策 → 動作* 裡的**「感知」**：

1. 用 OpenCV HSV 色彩遮罩**門檻化**紅色像素 → 二值遮罩。
2. **找出色塊**（最大輪廓）與其**形心**。
3. **方位（bearing）** 由形心在 60° 視野裡的水平位置算出（針孔相機角度）。
4. **距離** 由形心處的深度影像取得 —— 但要先把 PyBullet 的非線性深度緩衝轉成公尺。

> 為什麼用鮮紅方塊？色彩門檻化是最簡單又**真的有效**的感知，讓你專注在流程本身。Lesson 3 會用神經網路取代這個手寫偵測器。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/02_perception/perception_demo.py            # 開視窗
python lessons/02_perception/perception_demo.py --headless # 不開視窗（CI 用）
```

請讀 [`perception_demo.py`](perception_demo.py) — `detect_obstacle()` 是核心，而 `linearize_depth()` 點出新手最常踩的坑：**深度緩衝值不等於距離**。

它也會把兩張圖存到 `output/`：

- `camera_rgb.png` — 相機原始畫面。
- `detection.png` — 同畫面，疊上偵測框、形心，與 `距離／方位` 標籤。

## 驗收 ✅

終端機會印出類似：

```
Obstacle detected: 1.80 m ahead, bearing -12.2 deg (left).
```

方塊在正前方 2 公尺、側向 0.4 公尺處，所以「約 1.8 公尺、約 12° **偏左**」是正確的。打開 `output/detection.png`，確認綠框緊緊框住紅色障礙物。

## 延伸

- 改 `OBSTACLE_POS`，確認距離與方位如預期改變（例如放正前方 → 方位 ≈ 0°）。
- 改障礙物顏色，並同步更新 `detect_obstacle()` 裡的 HSV 範圍。
- **挑戰：** 把它跟 Lesson 1 結合 —— 偵測到障礙物近於 1 公尺時，命令無人機停下。那個小小的 `if` 就是你的第一個**自主決策**，也正是 Lesson 3 要用神經網路學會的事。
