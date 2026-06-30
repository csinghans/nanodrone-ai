"""
Lesson 23 — flight black box (step 1): record telemetry
=======================================================
Fly a short mission on the Lesson 11 state machine and write a telemetry row per
frame to a JSONL log — the drone's flight recorder. Lesson 24's Tello and a
Crazyflie emit the same rows, so one replay_flight.py works for all.

Run:
  python lessons/23_telemetry/record_flight.py             # GUI, writes the log
  python lessons/23_telemetry/record_flight.py --headless  # no window
  python lessons/23_telemetry/record_flight.py --selftest  # asserts (CI)
"""

import os
import sys

try:
    from nanodrone.mission import GoTo, Hover, Land, Mission, Takeoff
    from nanodrone.telemetry import FIELDS, FlightLogger
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 23 dependencies:", exc)
    sys.exit(1)

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "flight.jsonl")


def make_setup():
    def setup(m):
        m.scene["logger"] = FlightLogger()
        m.scene["t"] = 0.0

    return setup


def on_frame(m):
    m.scene["t"] += m.dt
    m.scene["logger"].log(m.scene["t"], m.pos, m.target, m.yaw)


def fly(gui: bool):
    plan = [
        Takeoff(height=1.1),
        GoTo([1.0, 0.5, 1.1], face=True),
        Hover(seconds=1.0),
        Land(),
    ]
    m = Mission(plan, start=(0.0, 0.0, 0.1), gui=gui)
    r = m.run(max_seconds=30.0, setup=make_setup(), on_frame=on_frame)
    n = m.scene["logger"].save(LOG)
    return r, n


def selftest() -> None:
    r, n = fly(gui=False)
    print(f"RECORD OK: logged {n} frames, {len(FIELDS)} fields/frame, file={LOG}")
    assert n > 0, "nothing was logged"
    assert r["landed"], f"flight did not land (z={r['final_z']:.2f})"
    from nanodrone.telemetry import load_log

    rows = load_log(LOG)
    assert len(rows) == n, "saved/loaded row count mismatch"
    assert all(set(row) == set(FIELDS) for row in rows), "inconsistent fields"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        fly(gui="--headless" not in sys.argv)


if __name__ == "__main__":
    main()
    sys.exit(0)
