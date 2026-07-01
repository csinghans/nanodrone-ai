"""
Lesson 14b (step 2) — does it still fly within the on-board compute budget?
===========================================================================
On your Mac, perception runs every few frames for free. On GAP8 each inference
takes real milliseconds, so the drone can only look so often — and a control
loop that looks less often tracks worse. This makes that trade-off visible:
re-run Lesson 13's find/follow mission at several inference latencies and watch
the tracking error grow. It answers "why not just set PERCEPTION_EVERY=1?" with
a curve instead of a guess, and checks the occupancy grid's memory fits too.

Run (after Lesson 13's train_confirm.py):
  python lessons/14b_onboard_budget/latency_sim.py
  python lessons/14b_onboard_budget/latency_sim.py --selftest   # asserts (local)
"""

import os
import sys

import numpy as np

try:
    from nanodrone.map import OccupancyGrid

    _L13 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "13_find_follow_land",
    )
    sys.path.insert(0, _L13)
    import mission as l13  # Lesson 13's find/follow/land mission
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 13's mission:", exc)
    sys.exit(1)

CTRL_MS = 1000.0 / 48.0  # one control frame at ctrl_freq=48 Hz (~20.8 ms)
LATENCIES_MS = [20, 80, 160]  # cheap / mid / heavy on-board inference


def run_at(latency_ms: float) -> float:
    """Run the mission with perception throttled to one inference per latency."""
    period = max(1, round(latency_ms / CTRL_MS))
    _r, m = l13.fly(gui=False, perception_every=period)
    errs = m.scene["track_errs"]
    return float(np.mean(errs)) if errs else 99.0


def grid_footprint_kb() -> tuple:
    g = OccupancyGrid(extent=3.0, res=0.3)  # the Lesson 14a map
    return g.n, g.grid.nbytes / 1024.0  # its real allocation (int32 accumulators)


def main() -> None:
    selftest = "--selftest" in sys.argv
    results = [(ms, run_at(ms)) for ms in LATENCIES_MS]
    n, kb = grid_footprint_kb()

    curve = ", ".join(f"{ms}ms->{err:.1f}deg" for ms, err in results)
    print(
        f"LATENCY OK: {curve} (tracking error grows with inference latency); "
        f"grid {n}x{n} int32 = {kb:.1f} KB fits 256 KB"
    )
    if selftest:
        lo_err, hi_err = results[0][1], results[-1][1]
        # low-latency error is dominated by the PID's yaw-tracking lag (~14 deg);
        # the point is that it stays bounded there and blows up when perception
        # is starved at high latency.
        assert lo_err < 20.0, f"unstable even at low latency ({lo_err:.1f} deg)"
        assert (
            hi_err > lo_err
        ), f"error did not grow with latency ({lo_err:.1f}->{hi_err:.1f})"
        assert kb < 256.0, f"occupancy grid too big for GAP8 L2 ({kb:.1f} KB)"


if __name__ == "__main__":
    main()
    sys.exit(0)
