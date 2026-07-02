"""
Lesson 30 — the graduation check: do the course's contracts still hold?
=======================================================================
A summary lesson should not just *say* what you built — it should *prove* the
load-bearing pieces still work, the way every lesson proved itself with a
`--selftest`. This script re-asserts the course's three shared contracts, the
ones every later lesson leaned on:

  1. **The command protocol** (`nanodrone.protocol`, Lesson 27): the 13-action
     JSON contract that the simulator, a Tello, a Crazyflie and the DroneVoice
     app all parse. One source of truth, machine-readable schema included.
  2. **The safety layer** (`nanodrone.safety`, Lesson 24): pure functions —
     battery gate, link watchdog, geofence — folded into one `decide_failsafe`
     verdict. We walk its whole truth table.
  3. **The mission graph** (`nanodrone.mission`, Lessons 11/16): Takeoff-first,
     Land-last, guarded transitions, Failsafe always wired — checked by Lesson
     16's own validator, which also *flies* the template mission headless.

If PyTorch is available it also reloads Lesson 29's world model and re-checks
the on-board budget (weights + activations + workspace < 512 KB). Without
torch it stays green and says so — the shared contracts are torch-free by
design, which is exactly why they run in the course's torch-free CI.

Run:
  python lessons/30_summary/course_check.py             # the graduation check
  python lessons/30_summary/course_check.py --selftest  # same, with asserts
"""

import argparse
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "16_capstone")))

from nanodrone import protocol, safety  # noqa: E402


def check_protocol() -> str:
    assert len(protocol.ACTIONS) == 13, "the 13-action contract changed"
    ok, why = protocol.validate({"action": "forward", "distance": 1.0})
    assert ok, f"a canonical command failed validation: {why}"
    ok, _ = protocol.validate({"action": "teleport"})
    assert not ok, "an unknown action slipped through validation"
    assert protocol.normalize_action("estop") == "emergency_stop", "alias broken"
    schema = protocol.schema()
    assert "properties" in schema, "machine-readable schema missing"
    return f"protocol {len(protocol.ACTIONS)} actions + schema"


def check_safety() -> str:
    cases = [
        ((5.0, 0.0, 1.0, (0, 0, 1.0)), "low_batt"),
        ((80.0, 0.0, 99.0, (0, 0, 1.0)), "lost_link"),
        ((80.0, 99.0, 99.5, (99, 0, 1.0)), "out_of_bounds"),
        ((80.0, 99.0, 99.5, (0, 0, 1.0)), "ok"),
    ]
    for args, want in cases:
        got = safety.decide_failsafe(*args)
        assert got == want, f"decide_failsafe{args} -> {got}, wanted {want}"
    clipped = safety.geofence_clip((99.0, -99.0, 99.0))
    assert safety.in_bounds(clipped), "geofence_clip left the box"
    return f"safety {len(cases)}/{len(cases)} failsafe verdicts + geofence"


def check_mission() -> str:
    from template_mission import build_plan, selftest
    from validate_mission import validate

    report = validate(build_plan, selftest)  # flies the template headless too
    return f"mission graph {report['states']} states (flown + validated)"


def check_world_model() -> str:
    if importlib.util.find_spec("torch") is None:
        return "world model skipped (torch-free run — contracts don't need it)"
    sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "29_world_model")))
    from eval_world_model_policy import onboard_budget
    from train_world_model import MODEL, load_model

    if not os.path.exists(MODEL):
        return "world model skipped (no checkpoint; run Lesson 29 first)"
    enc, pred, cheads, nhead, meta = load_model()
    b = onboard_budget(enc, pred, cheads, nhead)
    assert b["total_kb"] < 512, f"over the GAP8 budget ({b['total_kb']:.1f} KB)"
    return f"world model reloads, on-board budget {b['total_kb']:.1f} KB < 512 KB"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.parse_args()  # --selftest and the default run assert identically

    parts = [check_protocol(), check_safety(), check_mission(), check_world_model()]
    print("COURSE OK: " + " | ".join(parts))


if __name__ == "__main__":
    main()
    sys.exit(0)
