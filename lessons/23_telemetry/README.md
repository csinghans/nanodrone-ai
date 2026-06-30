# Lesson 23 — Flight black box: telemetry & replay

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Real-hardware bring-up's first need isn't smarter AI — it's being able to **see
what happened** after a flight: a jitter, a misfire, a near-miss. So before any
hardware, we build the flight recorder in $0 sim and fix the log format here.
Then Lesson 24's Tello and a Crazyflie only have to emit the same rows, and one
replay tool works for all of them — instead of re-writing analysis per platform.
It's the clearest case of the sim-first rule paying off.

## Concept

- **`nanodrone/telemetry.py`** — `FlightLogger.log(t, pos, target, yaw)` appends a
  structured row; `save`/`load_log` are newline-JSON (human-readable, greppable,
  the same wire format as the DroneVoice bridge).
- **`record_flight.py`** — flies a short mission on the Lesson 11 runner and logs
  a row every frame via the runner's `on_frame` hook → `logs/flight.jsonl`.
- **`replay_flight.py`** — reads the log and feeds each recorded **target** back to
  the flight controller, retracing the flight. A faithful black box replays to
  within centimetres of where the log ended.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/23_telemetry/record_flight.py            # GUI, writes logs/flight.jsonl
python lessons/23_telemetry/record_flight.py --selftest  # asserts (CI)
python lessons/23_telemetry/replay_flight.py             # GUI replay of the log
python lessons/23_telemetry/replay_flight.py --selftest   # asserts (CI)
```

## Checkpoint ✅

```
RECORD OK: logged 283 frames, 8 fields/frame, file=.../logs/flight.jsonl
REPLAY OK: replayed 283 frames, end-pos within 0.01 m of logged end
```

Record asserts a non-empty, consistent log was written and the flight landed;
replay asserts re-flying the log lands within 0.15 m of the logged end — proof
the recorder is faithful.

## Going further

- It's the prerequisite for Lesson 26's SOP ("logging on" is a pre-flight gate).
- Feed the log to a dashboard / the DroneVoice Phase 4 telemetry UI.
- Add `battery` and `failsafe_reason` columns and replay a real Tello flight.

---

<a name="中文"></a>
# Lesson 23 — 飛行黑盒子：遙測與回放

🌐 [English](#lesson-23--flight-black-box-telemetry--replay) · **繁體中文**（以下）

## 為什麼

真機 bring-up 最先需要的不是更聰明的 AI —— 而是飛完能**看到發生什麼**：抖動、誤觸發、差點撞到。
所以在碰任何硬體之前，先在 $0 sim 把飛行記錄器做出來、把 log 格式定下來。之後 Lesson 24 的 Tello 與
Crazyflie 只要吐出同樣的 row，同一支回放工具就能用 —— 而不是每換一個平台就重寫分析腳本。
這是 sim-first 原則最清楚的回報案例。

## 概念

- **`nanodrone/telemetry.py`** —— `FlightLogger.log(t, pos, target, yaw)` 每幀 append 一筆結構化 row；
  `save`/`load_log` 用 newline-JSON（人類可讀、可 grep，與 DroneVoice 橋接同一套 wire 格式）。
- **`record_flight.py`** —— 在 Lesson 11 runner 上飛一段短任務，透過 runner 的 `on_frame` hook 每幀記一筆 → `logs/flight.jsonl`。
- **`replay_flight.py`** —— 讀 log，把每筆記錄的 **target** 餵回飛控，重走一遍。忠實的黑盒子回放到距 log 結束點幾公分內。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/23_telemetry/record_flight.py            # GUI，寫 logs/flight.jsonl
python lessons/23_telemetry/record_flight.py --selftest  # 驗收（CI）
python lessons/23_telemetry/replay_flight.py             # GUI 回放 log
python lessons/23_telemetry/replay_flight.py --selftest   # 驗收（CI）
```

## 驗收 ✅

```
RECORD OK: logged 283 frames, 8 fields/frame, file=.../logs/flight.jsonl
REPLAY OK: replayed 283 frames, end-pos within 0.01 m of logged end
```

Record 驗證寫出非空、欄位一致的 log 且有降落；replay 驗證重飛 log 後降落在距記錄終點 0.15 公尺內 ——
證明記錄器忠實。

## 延伸

- 這是 Lesson 26 SOP 的前置（「開啟 log」是飛行前 gate）。
- 把 log 餵到 dashboard / DroneVoice Phase 4 的遙測 UI。
- 加 `battery` 與 `failsafe_reason` 欄位，回放一段真實 Tello 飛行。
