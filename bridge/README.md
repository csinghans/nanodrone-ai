# DroneVoice bridge

🌐 English · 繁體中文

The glue between the **DroneVoice Apple app** and the nanodrone simulator: a tiny
TCP server that receives newline-delimited JSON flight commands and flies the
PyBullet sim, so you can watch the drone obey commands spoken to your iPhone
(Siri / in-app mic → Apple Foundation Model → structured command → here). The
same JSON protocol later targets a real Tello/Crazyflie — only the controller
changes.

橋接 **DroneVoice Apple App** 與 nanodrone 模擬器：一支小 TCP server，收換行 JSON
飛行指令並驅動 PyBullet 模擬，讓你看到無人機回應對 iPhone 講的話（Siri／App 內麥克風
→ Apple Foundation Model → 結構化指令 → 這裡）。同一套 JSON 協定之後可換真機。

## Run

```bash
conda activate nanodrone-ai
python bridge/sim_server.py                 # GUI + listen on 0.0.0.0:9000
python bridge/sim_server.py --selftest      # scripted, headless (CI)

# test client (stands in for the app):
python bridge/send.py takeoff
python bridge/send.py forward 1.5           # metres
python bridge/send.py turn_left 90          # degrees
python bridge/send.py land
python bridge/send.py --host <mac-ip> forward 1   # from another machine
```

## Protocol

One JSON object per line over TCP:

```json
{"action": "takeoff"}
{"action": "forward", "distance": 1.0}
{"action": "turn_left", "degrees": 45}
{"action": "land"}
{"action": "emergency_stop"}
```

Actions: `takeoff, land, forward, back, left, right, up, down, turn_left,
turn_right, stop, hover, emergency_stop`. `distance` (m, default 0.5) for moves,
`degrees` (default 30) for turns. Body-frame, geofenced, low indoor speed —
reuses the Lesson 5/9 flight loop and the `nanodrone` core.

> The iOS app lives in its own project; this server runs on the Mac (same Wi-Fi
> as the phone). Point the app at the Mac's IP, port 9000.
