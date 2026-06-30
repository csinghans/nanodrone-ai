# DroneVoice Phase 5 — real drones (same protocol, swap the controller)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Phases 1–4 fly the PyBullet sim. Phase 5 puts the **same** newline-JSON on a real
drone — the app, the voice parser and the protocol don't change a line; only the
controller behind port 9000 does. Two backends, in order of risk:

- **`tello_server.py` (5a)** — a Tello over Wi-Fi via Lesson 24's `TelloBackend`.
  Cheapest, lowest risk; **AI off-board**, so not the offline goal — the proof
  that the protocol is portable and the safe first real flight.
- **`crazyflie_server.py` (5b)** — a Crazyflie via cflib's `MotionCommander`. The
  course's end point: high-level commands from the app/voice, while real autonomy
  (avoidance) runs as the quantized model **on the AI-deck** (Lessons 4 / 22),
  **offline and on-board**. Golden rule: any exit — normal or exception — lands.

## Hands-on

```bash
conda activate nanodrone-ai
python hardware/tello_server.py --selftest        # FakeTello, asserts (no drone)
python hardware/crazyflie_server.py --selftest    # FakeCrazyflie, asserts (no drone)

pip install djitellopy && python hardware/tello_server.py        # real Tello
pip install cflib       && python hardware/crazyflie_server.py    # real Crazyflie
```

Both servers reuse `nanodrone.protocol` and `nanodrone.safety`; `FakeTello` /
`FakeMotionCommander` record the controller calls so the mapping is verified with
no hardware (and no `djitellopy` / `cflib` installed), so the self-tests run in CI.

## Checkpoint ✅

```
TELLO-SERVER OK: served 5 protocol cmds -> [takeoff, move_forward, move_up, rotate_counter_clockwise, land], battery-gate enforced, app-equivalent
CF-SERVER OK: mapped protocol cmds -> motion_commander calls [forward, turn_right, up, land], battery-gate + commander-always-lands enforced
```

## Safety (non-negotiable for real flight)

Open space, props clear of people, an RC override ready, failsafe on
(`nanodrone.safety`: battery / link / geofence), pre-flight gate green
(`lessons/26_field_test/preflight_check.py`), and always verified in sim first.

---

<a name="中文"></a>
# DroneVoice Phase 5 — 真機（同協定，換 controller）

🌐 [English](#dronevoice-phase-5--real-drones-same-protocol-swap-the-controller) · **繁體中文**（以下）

## 為什麼

Phase 1–4 飛 PyBullet 模擬。Phase 5 把**同一套** newline-JSON 放到真機 —— app、語音解析、協定一行都不改；
只有 port 9000 背後的 controller 換掉。兩個 backend，依風險排序：

- **`tello_server.py`（5a）** —— 透過 Lesson 24 的 `TelloBackend` 用 Wi-Fi 飛 Tello。最便宜、最低風險；
  **AI 在機外**，所以不是離線目標 —— 它是協定可攜的證明與安全的第一次真機飛行。
- **`crazyflie_server.py`（5b）** —— 透過 cflib 的 `MotionCommander` 飛 Crazyflie。課程的終點：高階指令來自 app／語音，
  而真正的自主（避障）以量化模型跑在 **AI-deck 上**（Lesson 4／22），**離線、板載**。鐵則：任何離開 —— 正常或例外 —— 都降落。

## 動手做

```bash
conda activate nanodrone-ai
python hardware/tello_server.py --selftest        # FakeTello、會 assert（無人機）
python hardware/crazyflie_server.py --selftest    # FakeCrazyflie、會 assert（無人機）

pip install djitellopy && python hardware/tello_server.py        # 真 Tello
pip install cflib       && python hardware/crazyflie_server.py    # 真 Crazyflie
```

兩個 server 都重用 `nanodrone.protocol` 與 `nanodrone.safety`；`FakeTello` / `FakeMotionCommander`
記錄 controller 呼叫，所以不需硬體（也不需裝 `djitellopy` / `cflib`）就能驗證映射，自我測試能進 CI。

## 驗收 ✅

```
TELLO-SERVER OK: served 5 protocol cmds -> [takeoff, move_forward, move_up, rotate_counter_clockwise, land], battery-gate enforced, app-equivalent
CF-SERVER OK: mapped protocol cmds -> motion_commander calls [forward, turn_right, up, land], battery-gate + commander-always-lands enforced
```

## 安全（真機飛行不可妥協）

空曠處、螺旋槳遠離人、備好 RC 可接管、開啟 failsafe（`nanodrone.safety`：電量／連線／geofence）、
飛行前 gate 綠燈（`lessons/26_field_test/preflight_check.py`），且永遠先在模擬驗證。
