# Lesson 7 — Follow the pilot

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

This is the "follow-me drone" everyone pictures: **you** walk around and the
drone trails you on its own. It's also a satisfying payoff for the course — it
fuses Lesson 5 (you driving), Lesson 6 (visual following), and yaw control into
one loop, with almost no new ideas.

## Concept

Two agents share the simulator:

- **The person** — a little orange figure you drive with the gamepad or keyboard
  (the input backends are imported straight from Lesson 5).
- **The drone** — fully autonomous. Each perception tick it detects the orange
  person (HSV, like Lesson 2), finds your distance from the depth image, and
  computes your **world position** from its own pose. Then it:
  - **yaws to face you** (so the camera keeps you centred — this is the new bit
    vs Lesson 6, and it's what lets the drone follow you *around*, not just
    side-to-side), and
  - flies to a standoff point `DESIRED_DIST` behind you.

The PID flight controller (Lesson 1) does the actual flying. Perception runs
slower than control, just like real hardware.

## Hands-on

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-extra.txt   # pygame, for the gamepad (Lesson 5)
python lessons/07_follow_person/follow_person.py            # you drive, drone follows
python lessons/07_follow_person/follow_person.py --headless # scripted demo (CI/verify)
```

Drive the **person** with the right stick (or arrow keys); the drone follows
itself. The person has a dark **"face"** marker showing which way they walk, and
the camera is a chase cam with the side panels hidden. For a bigger view,
maximize the window (on macOS: green button → *Enter Full Screen*, or double-
click the title bar).

Read [`follow_person.py`](follow_person.py): `detect_person()` is the Lesson 2
detector, and the `theta = drone_yaw - bearing` line is the whole "turn to face
you" trick.

## Checkpoint ✅

Headless walks the person in a circle and prints (verified on this machine):

```
FOLLOW OK: tracked 71 frames while the person circled, mean bearing error 1.5 deg.
```

A bearing error of ~1° means the drone kept you almost perfectly centred the
entire circle. In the GUI, drive the person anywhere and watch the drone pivot
and trail you.

## Going further

- **Lead the target:** predict where the person is going and aim there to cut
  follow lag on fast turns.
- **Keep a filming angle:** trail at 45° instead of directly behind.
- **Lose-and-reacquire:** add a slow search yaw when the person leaves view.

---

<a name="中文"></a>
# Lesson 7 — 跟著飛手

🌐 [English](#lesson-7--follow-the-pilot) · **繁體中文**（以下）

## 為什麼

這就是大家想像中的「follow-me 空拍機」：**你**到處走，無人機自己跟著你。它也是整門課很爽的收尾 —— 把 Lesson 5（你操控）、Lesson 6（視覺跟隨）和機頭轉向融成一個迴圈，幾乎沒有新觀念。

## 概念

模擬器裡有兩個角色：

- **人** —— 一個橘色小人，你用手把或鍵盤驅動（輸入後端直接從 Lesson 5 import 過來）。
- **無人機** —— 完全自主。每個感知 tick 偵測橘色的人（HSV，與 Lesson 2 相同）、從深度影像得到距離、由自己的姿態算出你的**世界座標**，然後：
  - **轉機頭面向你**（讓相機持續把你保持在中央 —— 這是相對 Lesson 6 新增的部分，也正是能跟著你「繞圈」而非只左右移動的關鍵），以及
  - 飛到你後方 `DESIRED_DIST` 的尾隨點。

實際飛行由 PID 飛控（Lesson 1）負責。感知比控制慢，跟真實硬體一樣。

## 動手做

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-extra.txt   # pygame，手把用（Lesson 5）
python lessons/07_follow_person/follow_person.py            # 你操控、無人機跟
python lessons/07_follow_person/follow_person.py --headless # 腳本化 demo（CI/驗證）
```

用右搖桿（或方向鍵）驅動**人**；無人機自己跟。橘色小人有一個深色**「臉」**標記顯示朝向；鏡頭是跟拍鏡頭、側邊面板已隱藏。想要更大畫面就最大化視窗（macOS：綠色按鈕 →「進入全螢幕」，或雙擊標題列）。

請讀 [`follow_person.py`](follow_person.py)：`detect_person()` 就是 Lesson 2 的偵測器，而 `theta = drone_yaw - bearing` 那行就是整個「轉向面對你」的訣竅。

## 驗收 ✅

headless 會讓人走一圈並印出（本機實測）：

```
FOLLOW OK: tracked 71 frames while the person circled, mean bearing error 1.5 deg.
```

方位誤差約 1° 代表無人機整圈幾乎把你完美保持在中央。在 GUI 裡，把人往任何方向開，看無人機轉身尾隨。

## 延伸

- **預判目標：** 預測人要往哪走、瞄準前方，減少急轉時的跟隨延遲。
- **保持拍攝角度：** 改成 45° 側後方尾隨，而非正後方。
- **遺失後重新鎖定：** 人離開視野時加一個緩慢的搜尋轉向。
