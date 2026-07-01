"""
DroneVoice Phase 5a — Tello over Wi-Fi: same protocol, real drone
=================================================================
The end-to-end real flight: the iPhone app (Phase 4) sends the SAME newline-JSON
to port 9000, and this server flies a real Tello via Lesson 24's TelloBackend —
not one line of the app, the voice parser or the protocol changes, only the
controller behind the socket. The AI is off-board (Tello is Wi-Fi), so this is
the cheapest real DroneVoice demo, not the offline GAP8 goal.

Run:
  python hardware/tello_server.py             # listen on 0.0.0.0:9000, drive a Tello
  python hardware/tello_server.py --selftest   # FakeTello, asserts (no drone, CI)
"""

import json
import os
import socket
import sys

from nanodrone import safety
from nanodrone.protocol import ACTIONS, normalize_action

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "lessons",
        "24_tello",
    ),
)
from tello_backend import FakeTello, TelloBackend  # noqa: E402

# On a low battery, refuse take-off AND further moves; still allow land / stop /
# hover / emergency so the drone can always come down safely.
_GATED = {
    "takeoff",
    "forward",
    "back",
    "left",
    "right",
    "up",
    "down",
    "turn_left",
    "turn_right",
}


def handle(backend, cmd) -> bool:
    """Apply one command, gated by the battery. Returns False if refused."""
    action = normalize_action(cmd.get("action", ""))
    low_batt = not safety.battery_gate(backend.tello.get_battery())
    if action in _GATED and low_batt:
        return False  # don't take off or fly further on a low battery
    backend.apply_command(cmd)
    return True


def serve(host: str, port: int) -> None:  # pragma: no cover - needs a real Tello
    from djitellopy import Tello

    tello = Tello()
    tello.connect()
    backend = TelloBackend(tello)
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"[tello] listening on {host}:{port}, battery {tello.get_battery()}%")
    conn, _ = srv.accept()
    buf = b""
    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                if line.strip():
                    handle(backend, json.loads(line))


def selftest() -> None:
    backend = TelloBackend(FakeTello(battery=80))
    stream = [
        {"action": "takeoff"},
        {"action": "forward", "distance": 1.0},
        {"action": "up", "distance": 0.5},
        {"action": "turn_left", "degrees": 90},
        {"action": "land"},
    ]
    served = sum(1 for c in stream if handle(backend, c))
    calls = [name for name, _ in backend.tello.calls]

    # battery gate: a low battery refuses takeoff
    low = TelloBackend(FakeTello(battery=10))
    refused = not handle(low, {"action": "takeoff"})

    print(
        f"TELLO-SERVER OK: served {served} protocol cmds -> "
        f"[{', '.join(calls)}], battery-gate enforced, app-equivalent"
    )
    assert served == len(stream), "a command was dropped"
    assert calls[0] == "takeoff" and calls[-1] == "land", calls
    assert refused, "low battery should refuse takeoff"
    assert len(ACTIONS) == 13  # protocol unchanged


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        serve("0.0.0.0", 9000)


if __name__ == "__main__":
    main()
    sys.exit(0)
