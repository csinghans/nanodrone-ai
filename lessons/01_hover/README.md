# Lesson 1 — Flight control basics (hover & waypoints)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Before an AI can decide *where* a drone goes, you need to trust that *"go to point X"* actually works. This lesson gives you that foundation: you'll make a simulated Crazyflie hover, then fly a path — with zero hardware and zero cost.

## Concept

A drone has two control layers:

- **Low-level (the flight controller):** keeps it stable and turns a target like
  "be at (0, 0, 1)" into four motor speeds. Runs hundreds of times per second.
  In this repo that's `DSLPIDControl` — think of it as the firmware.
- **High-level (your code / future AI):** decides the target. Runs ~tens of times
  per second. Today it's a fixed point; later it'll be a neural network.

The script `hover_demo.py` is the smallest possible version of this loop.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/01_hover/hover_demo.py
```

Read the comments in [`hover_demo.py`](hover_demo.py) — every block is explained.
The three steps inside the loop are the heartbeat of every autonomous system:
**sense → decide → act.**

## Checkpoint ✅

- A PyBullet window opens and a small quadcopter rises to ~1 m and holds steady.
- The terminal prints `Done: hovered at [0.0, 0.0, 1.0] for 10 s.`

If the window doesn't open, run `python lessons/01_hover/hover_demo.py --headless`
to confirm the physics runs without graphics, then troubleshoot the GUI.

## Going further

- Change `TARGET_POS` and watch the drone fly to a new point.
- **Challenge:** make it fly a 1 m square (4 waypoints) then land. Hint: change
  the target on a schedule based on the loop index `i`.
- Read about the Crazyflie 2.x model the simulator uses (`DroneModel.CF2X`).

---

<a name="中文"></a>
# Lesson 1 — 飛行控制基礎（懸停與航點）

🌐 [English](#lesson-1--flight-control-basics-hover--waypoints) · **繁體中文**（以下）

## 為什麼

在 AI 能決定無人機「往哪飛」之前，你得先信任「飛到某點 X」這件事真的有效。這一課就是打地基：你會讓一台模擬的 Crazyflie 懸停、再飛一段路徑 — 不用任何硬體、零成本。

## 概念

無人機有兩個控制層：

- **低階（飛控）：** 負責穩定，把「飛到 (0, 0, 1)」這種目標轉成四顆馬達的轉速，每秒跑數百次。在本 repo 裡就是 `DSLPIDControl` — 把它想成韌體。
- **高階（你的程式／未來的 AI）：** 負責決定目標，每秒跑幾十次。今天是固定一點，之後會換成神經網路。

`hover_demo.py` 就是這個迴圈最精簡的版本。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/01_hover/hover_demo.py
```

請讀 [`hover_demo.py`](hover_demo.py) 裡的註解 — 每一段都有解釋。迴圈裡的三個步驟，就是所有自主系統的心跳：**感知 → 決策 → 動作。**

## 驗收 ✅

- 跳出 PyBullet 視窗，一台小四旋翼升到約 1 公尺並穩定懸停。
- 終端機印出 `Done: hovered at [0.0, 0.0, 1.0] for 10 s.`

若視窗沒跳出，先跑 `python lessons/01_hover/hover_demo.py --headless` 確認物理運算本身正常（不畫圖），再排查 GUI 問題。

## 延伸

- 改 `TARGET_POS`，看無人機飛到新的點。
- **挑戰：** 讓它飛一個 1 公尺的正方形（4 個航點）再降落。提示：用迴圈索引 `i` 來排程切換目標。
- 了解模擬器用的 Crazyflie 2.x 機型（`DroneModel.CF2X`）。
