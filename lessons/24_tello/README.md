# Lesson 24 — Your first real drone: a cheap Tello over Wi-Fi

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

The GAP8 / AI-deck path (Lesson 4, ~US$545, soldering + flashing, offline) is a
high bar for a first real flight. A DJI/Ryze **Tello** is ~US$100, connects over
Wi-Fi, and flies from one `pip install` — the AI runs on your laptop and sends
the **same** JSON commands the sim used. That's not the offline goal (the AI is
off-board), but it's the safe, cheap first real flight and proof the protocol is
portable: only the controller behind it changes. Failsafe is now real, so this
lesson also factors `nanodrone.safety` out of Lesson 11's Failsafe state.

## Concept

- **`nanodrone/safety.py`** — the failsafe layer as pure functions: `battery_gate`,
  `link_watchdog`, `geofence_clip`, and one `decide_failsafe` returning
  `low_batt` / `lost_link` / `out_of_bounds` / `ok`. Pure functions let you inject
  the faults you'd never dare create on a real battery and unit-test the response.
- **`tello_backend.py`** — `TelloBackend.apply_command` maps the protocol's 13
  actions to DJITelloPy calls with unit conversion (metres → centimetres, degrees
  pass through). `FakeTello` records the calls so CI / no-hardware runs verify the
  mapping without a drone (or DJITelloPy installed).
- **`fly_tello.py`** — drives a real Tello (or FakeTello), gated by the safety layer.

The two-layer split holds on real hardware: your code sends a high-level action;
the Tello's own firmware stabilizes — you never touch a motor.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/24_tello/fly_tello.py --selftest   # FakeTello, asserts (no drone)
pip install djitellopy                            # only for a real flight
python lessons/24_tello/fly_tello.py              # connect to a real Tello
```

## Checkpoint ✅

```
TELLO OK: mapped 13/13 actions to Tello calls (1.0 m forward -> move_forward(100), 90 deg -> rotate_ccw(90)), unit conversion verified; safety 3/3 faults triggered correct response
```

The self-test asserts all 13 protocol actions map to the right Tello call with
correct units, and that `decide_failsafe` trips the right reason for an injected
low battery, lost link, and out-of-bounds — without any hardware, so it runs in CI.

## Going further

- Lesson 25 uses the Tello's camera to measure the sim-to-real gap.
- Point a Phase-4 SwiftUI app at this backend (same protocol) and fly the Tello
  by voice.
- Crazyflie swaps `TelloBackend` for a cflib controller (DroneVoice Phase 5b) —
  same protocol, finally offline and on-board.

---

<a name="中文"></a>
# Lesson 24 — 你的第一台真機：平價 Tello（Wi-Fi）

🌐 [English](#lesson-24--your-first-real-drone-a-cheap-tello-over-wi-fi) · **繁體中文**（以下）

## 為什麼

GAP8 / AI-deck 路線（Lesson 4，約 US$545，要焊接+燒錄、離線）對第一次真機飛行門檻很高。DJI/Ryze **Tello**
約 US$100、Wi-Fi 連線、一個 `pip install` 就能飛 —— AI 跑在你筆電上，送的是和 sim **同一套** JSON 指令。
那不是離線目標（AI 在機外），但它是安全、便宜的第一次真機飛行，也證明協定可攜：只有背後的 controller 換掉。
Failsafe 現在是真的了，所以這課也把 `nanodrone.safety` 從 Lesson 11 的 Failsafe 狀態抽出來。

## 概念

- **`nanodrone/safety.py`** —— failsafe 層做成純函式：`battery_gate`、`link_watchdog`、`geofence_clip`，
  與一個 `decide_failsafe` 回傳 `low_batt` / `lost_link` / `out_of_bounds` / `ok`。純函式讓你能注入
  那些在真電池上絕不敢造的故障，並單元測試其反應。
- **`tello_backend.py`** —— `TelloBackend.apply_command` 把協定的 13 個動作映到 DJITelloPy 呼叫，
  含單位換算（公尺 → 公分、度數直接傳）。`FakeTello` 記錄呼叫，讓 CI / 無硬體跑也能驗證映射（不需真機或 DJITelloPy）。
- **`fly_tello.py`** —— 驅動真 Tello（或 FakeTello），由 safety 層把關。

雙層架構在真機上一樣成立：你的程式送高階動作；Tello 自己的韌體穩定 —— 你永遠不碰馬達。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/24_tello/fly_tello.py --selftest   # FakeTello、會 assert（無人機）
pip install djitellopy                            # 只在真飛時需要
python lessons/24_tello/fly_tello.py              # 連真 Tello
```

## 驗收 ✅

```
TELLO OK: mapped 13/13 actions to Tello calls (1.0 m forward -> move_forward(100), 90 deg -> rotate_ccw(90)), unit conversion verified; safety 3/3 faults triggered correct response
```

自我測試驗證 13 個協定動作都映到正確的 Tello 呼叫與單位，且 `decide_failsafe` 對注入的低電量、失聯、越界
都觸發正確原因 —— 完全不需硬體，所以能進 CI。

## 延伸

- Lesson 25 用 Tello 的相機量測 sim-to-real 落差。
- 把 Phase 4 的 SwiftUI app 指向這個 backend（同協定），用語音飛 Tello。
- Crazyflie 把 `TelloBackend` 換成 cflib controller（DroneVoice Phase 5b）—— 同協定，終於離線、板載。
