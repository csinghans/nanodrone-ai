# Lesson 5 (bonus) — Fly it yourself with an Xbox controller

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lessons 1–4 made the drone fly *itself*. This bonus hands **you** the sticks.
Teleoperating the simulated drone is the fastest way to build flight intuition —
and to feel just how much the autonomy in Lesson 3 was doing for you.

## Concept

The gamepad does **not** drive the motors — same two-layer split as Lesson 1.
Each frame we:

1. read the sticks → a desired **velocity** (world-frame),
2. integrate it into a moving **target position** (clamped to a safe box),
3. let the **PID flight controller** chase that target.

Release the sticks → the target stops → the drone **hovers in place**. Controls
are *body-frame* (like an FPV pilot): the left stick also **yaws** the heading,
and "forward" then follows wherever the nose points.

## Hands-on

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-extra.txt    # installs pygame (Lesson 5 only)

# pair your Xbox controller (Bluetooth or USB) to the Mac first, then:
python lessons/05_teleop/teleop_xbox.py

# no controller? use the keyboard:
python lessons/05_teleop/teleop_xbox.py --input keyboard

# axes not matching? calibrate — move a stick and see which index changes:
python lessons/05_teleop/teleop_xbox.py --list
```

**Controls**

| Input | Xbox | Keyboard |
|-------|------|----------|
| forward / back | right stick ↕ | ↑ / ↓ |
| right / left | right stick ↔ | → / ← |
| up / down | left stick ↕ | W / S |
| yaw (turn heading) | left stick ↔ | Q / E |
| quit | Ctrl-C | Ctrl-C |

Read [`teleop_xbox.py`](teleop_xbox.py): the three input backends (`xbox`,
`keyboard`, `selftest`) all feed the same flight loop. The default Xbox axis
indices follow SDL2 (LX0/LY1/RX2/RY3); use `--list` if yours differ.

## Checkpoint ✅

A PyBullet window opens with the drone hovering. Pushing the **right stick**
moves it horizontally; the **left stick** changes height; releasing the sticks
makes it hold position. (No hardware? `--input keyboard` does the same with the
arrow keys + W/S.)

You can verify the flight loop without any controller or window:

```bash
python lessons/05_teleop/teleop_xbox.py --input selftest
# -> SELFTEST OK: flight loop ran 97 steps, target moved 0.87 m.
```

## Going further

- **Tune the feel:** adjust `SPEED` and `YAW_RATE` at the top of the script.
- **Heads-up display:** overlay Lesson 2's obstacle detector so you see what an
  AI *would* see while you fly.
- **Record a GIF** of your flight (see `tools/render_media.py` for the headless
  camera capture pattern).

---

<a name="中文"></a>
# Lesson 5（加成課）— 用 Xbox 手把親手飛

🌐 [English](#lesson-5-bonus--fly-it-yourself-with-an-xbox-controller) · **繁體中文**（以下）

## 為什麼

Lesson 1–4 讓無人機自己飛。這堂加成課把搖桿交給**你**。親手遙控模擬無人機，是建立飛行直覺最快的方式 —— 也讓你體會 Lesson 3 的自主到底替你做了多少事。

## 概念

手把**不直接**控馬達 —— 跟 Lesson 1 一樣的雙層架構。每一幀：

1. 讀搖桿 → 換成想要的**速度**（世界座標），
2. 積分進一個會移動的**目標位置**（夾在安全飛行盒內），
3. 交給 **PID 飛控**去追那個目標。

鬆開搖桿 → 目標停住 → 無人機**定點懸停**。操控是*機體座標*（像 FPV 飛手）：左搖桿還能**轉機頭（yaw）**，轉完之後「前進」就跟著機頭方向走。

## 動手做

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-extra.txt    # 裝 pygame（Lesson 5 專用）

# 先把 Xbox 手把（藍牙或 USB）配對到 Mac，然後：
python lessons/05_teleop/teleop_xbox.py

# 沒手把？用鍵盤：
python lessons/05_teleop/teleop_xbox.py --input keyboard

# 軸對不上？校準 —— 撥動搖桿看哪個索引在變：
python lessons/05_teleop/teleop_xbox.py --list
```

**操控對照**

| 動作 | Xbox | 鍵盤 |
|------|------|------|
| 前進／後退 | 右搖桿 ↕ | ↑ / ↓ |
| 右／左 | 右搖桿 ↔ | → / ← |
| 上升／下降 | 左搖桿 ↕ | W / S |
| yaw（轉機頭） | 左搖桿 ↔ | Q / E |
| 離開 | Ctrl-C | Ctrl-C |

請讀 [`teleop_xbox.py`](teleop_xbox.py)：三種輸入後端（`xbox`／`keyboard`／`selftest`）共用同一個飛行迴圈。Xbox 預設軸索引依 SDL2（LX0/LY1/RX2/RY3）；不同的話用 `--list` 校準。

## 驗收 ✅

PyBullet 視窗開啟、無人機懸停。推**右搖桿**水平移動；**左搖桿**改變高度；鬆開搖桿就定點。（沒硬體？`--input keyboard` 用方向鍵 + W/S 做一樣的事。）

不用手把、不開視窗也能驗證飛行迴圈：

```bash
python lessons/05_teleop/teleop_xbox.py --input selftest
# -> SELFTEST OK: flight loop ran 97 steps, target moved 0.87 m.
```

## 延伸

- **調手感：** 改腳本最上方的 `SPEED` 與 `YAW_RATE`。
- **抬頭顯示（HUD）：** 疊上 Lesson 2 的障礙偵測器，邊飛邊看 AI「會看到」什麼。
- **錄一段飛行 GIF**（headless 相機擷取作法見 `tools/render_media.py`）。
