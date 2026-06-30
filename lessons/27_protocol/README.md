# Lesson 27 — One flight protocol, reused everywhere

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

The DroneVoice bridge welded the *protocol* — which actions exist, their
defaults, the body-frame math, the geofence — into the PyBullet loop. But the
iPhone app (Phase 2–5), a Tello and a Crazyflie all parse the **same JSON**.
Leave the contract inside the sim and each end re-implements it, and they drift —
a distance that means metres here and centimetres there, an action one side
forgot. This lesson pays that debt: extract the contract into one module before
building anything that depends on it. (Pairs with Lesson 11's `mission` extract —
both are technical debt, best repaid up front.)

## Concept

`nanodrone/protocol.py` is the **single source of truth**: pure data + pure
functions, no simulator import.

- `ACTIONS` — the 13 agreed actions; `DEFAULT_DIST` / `DEFAULT_DEG`; the geofence.
- `validate(cmd) -> (ok, reason)` — rejects unknown actions, negative distance, NaN.
- `step_target(cmd, target, yaw)` — the body-frame nudge + geofence clip (this is
  the bridge's original `apply_command`, moved here verbatim).
- `schema()` — a machine-readable JSON Schema to hand Apple's guided generation
  (Phase 3) or any client, so the action enum has one home.

`bridge/sim_server.py` now just imports it; behaviour is unchanged (its
`BRIDGE OK` self-test still passes), proving a contract-first refactor with no
regression.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/27_protocol/protocol_demo.py            # print the contract + schema
python lessons/27_protocol/protocol_demo.py --selftest  # asserts (CI)
python bridge/sim_server.py --selftest                  # unchanged behaviour
```

Read [`nanodrone/protocol.py`](../../nanodrone/protocol.py), then see how
[`bridge/sim_server.py`](../../bridge/sim_server.py) and `send.py` import it
instead of hard-coding actions.

## Checkpoint ✅

```
PROTOCOL OK: 13 actions, validate rejects 4/4 bad cmds, schema valid, body-frame + geofence correct
BRIDGE OK: ran 336 steps, target moved 1.00 m, yaw 90 deg, landed.
```

The first asserts the contract (valid/invalid handling, body-frame, geofence,
schema); the second is the bridge regression — same flight, now sourced from the
shared protocol.

## Going further

- This `schema()` is what Lesson 28 grades parsers against, and what DroneVoice
  Phase 3 turns into a Swift `@Generable` type.
- Add an action (e.g. `flip`) in *one* place and watch every backend gain it.

---

<a name="中文"></a>
# Lesson 27 — 一套飛行協定，到處重用

🌐 [English](#lesson-27--one-flight-protocol-reused-everywhere) · **繁體中文**（以下）

## 為什麼

DroneVoice 橋接把*協定* —— 有哪些動作、預設值、body-frame 數學、geofence —— 焊死在 PyBullet 迴圈裡。
但 iPhone app（Phase 2–5）、Tello、Crazyflie 解析的是**同一份 JSON**。把契約留在 sim 裡，
每一端就各自重寫、然後漂移 —— 這邊 distance 是公尺、那邊變公分，某一端漏了一個動作。這一課償還這筆債：
在任何依賴它的東西之前，先把契約抽成一個模組。（與 Lesson 11 的 `mission` 抽取成對 —— 兩者都是技術債，最好先還。）

## 概念

`nanodrone/protocol.py` 是**單一事實來源**：純資料 + 純函式，不 import 模擬器。

- `ACTIONS` —— 13 個約定動作；`DEFAULT_DIST` / `DEFAULT_DEG`；geofence。
- `validate(cmd) -> (ok, reason)` —— 擋掉未知動作、負距離、NaN。
- `step_target(cmd, target, yaw)` —— body-frame 位移 + geofence 裁切（這就是橋接原本的 `apply_command`，原封搬過來）。
- `schema()` —— 機器可讀的 JSON Schema，交給 Apple guided generation（Phase 3）或任何 client，讓動作 enum 只有一個家。

`bridge/sim_server.py` 現在只是 import 它；行為不變（`BRIDGE OK` 自我測試照過），證明 contract-first 重構零回歸。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/27_protocol/protocol_demo.py            # 印出契約 + schema
python lessons/27_protocol/protocol_demo.py --selftest  # 驗收（CI）
python bridge/sim_server.py --selftest                  # 行為不變
```

請讀 [`nanodrone/protocol.py`](../../nanodrone/protocol.py)，再看 [`bridge/sim_server.py`](../../bridge/sim_server.py)
與 `send.py` 如何 import 它，而不是各自寫死動作。

## 驗收 ✅

```
PROTOCOL OK: 13 actions, validate rejects 4/4 bad cmds, schema valid, body-frame + geofence correct
BRIDGE OK: ran 336 steps, target moved 1.00 m, yaw 90 deg, landed.
```

第一行驗證契約（合法/非法處理、body-frame、geofence、schema）；第二行是橋接回歸 —— 同一段飛行，
現在改由共用協定供給。

## 延伸

- 這個 `schema()` 就是 Lesson 28 用來評分解析器的標準，也是 DroneVoice Phase 3 變成 Swift `@Generable` 型別的來源。
- 在*一個*地方加一個動作（例如 `flip`），看每個 backend 都跟著有了它。
