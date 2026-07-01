"""
Lesson 24 — fly a real Tello with the course's protocol
=======================================================
The first real drone. Same JSON protocol as the sim — only the controller behind
it changes (PyBullet -> Tello). The AI runs on your laptop and sends commands
over Wi-Fi; that's NOT the offline GAP8 goal, it's the safe, cheap first real
flight and proof the protocol is portable. Failsafe is now real: the
`nanodrone.safety` battery gate is enforced before take-off. (Its link-watchdog
and geofence are pure functions exercised in --selftest, but a Tello flies
*relative* moves with no on-board position, so an absolute geofence can't
constrain it — a Crazyflie with a Flow deck could.)

Run:
  python lessons/24_tello/fly_tello.py --selftest   # FakeTello, asserts (no drone)
  python lessons/24_tello/fly_tello.py              # a real Tello (needs djitellopy)
"""

import os
import sys

from nanodrone import safety
from nanodrone.protocol import ACTIONS

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tello_backend import FakeTello, TelloBackend  # noqa: E402


def selftest() -> None:
    backend = TelloBackend(FakeTello(battery=80))

    # 1. every protocol action maps to a Tello call
    mapped = sum(1 for a in ACTIONS if backend.apply_command({"action": a}) is not None)

    # 2. unit conversion: metres -> cm, degrees pass through
    fwd = backend.apply_command({"action": "forward", "distance": 1.0})
    ccw = backend.apply_command({"action": "turn_left", "degrees": 90})
    assert fwd == ("move_forward", 100), fwd
    assert ccw == ("rotate_counter_clockwise", 90), ccw
    # an unsafe-by-default tiny move is clamped up to the Tello minimum
    tiny = backend.apply_command({"action": "up", "distance": 0.05})
    assert tiny == ("move_up", 20), tiny

    # 3. the safety layer trips the right reason for each injected fault
    faults = {
        "low_batt": safety.decide_failsafe(10.0, 0.0, 0.0, [0, 0, 1.0]),
        "lost_link": safety.decide_failsafe(80.0, 0.0, 5.0, [0, 0, 1.0]),
        "out_of_bounds": safety.decide_failsafe(80.0, 0.0, 0.0, [5.0, 0, 1.0]),
    }
    ok = safety.decide_failsafe(80.0, 0.0, 0.0, [0, 0, 1.0])
    triggered = sum(1 for reason, got in faults.items() if got == reason)

    print(
        f"TELLO OK: mapped {mapped}/{len(ACTIONS)} actions to Tello calls "
        f"(1.0 m forward -> move_forward(100), 90 deg -> rotate_ccw(90)), "
        f"unit conversion verified; safety {triggered}/{len(faults)} faults "
        f"triggered correct response"
    )
    assert mapped == len(ACTIONS), f"only mapped {mapped}/{len(ACTIONS)} actions"
    assert triggered == len(faults), f"safety mis-handled a fault: {faults}"
    assert ok == "ok", f"healthy state flagged a failsafe: {ok}"


def live() -> None:  # pragma: no cover - needs a real Tello on Wi-Fi
    try:
        from djitellopy import Tello
    except ImportError:
        print("Install DJITelloPy:  pip install djitellopy")
        sys.exit(1)
    tello = Tello()
    tello.connect()
    if not safety.battery_gate(tello.get_battery()):
        print(f"Battery too low ({tello.get_battery()}%) — not flying.")
        return
    backend = TelloBackend(tello)
    print("Connected. Open space, props clear, RC override ready.")
    for cmd in [
        {"action": "takeoff"},
        {"action": "forward", "distance": 0.5},
        {"action": "turn_left", "degrees": 90},
        {"action": "land"},
    ]:
        backend.apply_command(cmd)


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        live()


if __name__ == "__main__":
    main()
    sys.exit(0)
