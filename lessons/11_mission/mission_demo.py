"""
Lesson 11 — Mission state machine
=================================
Up to now every flight script copied the same control loop. This lesson factors
it out into `nanodrone.mission`: a tiny **state machine** that strings phases
together — take off, fly somewhere, hover, land — and watches a geofence the
whole time, dropping into **Failsafe** if anything asks to leave the safe box.

This is the turning point of the course: Lessons 1–10 were about *building*
capabilities (training models, writing perception); from here on we *compose*
them. Everything later (voice-driven missions, find-and-follow, mapping, the
graduation project) is built on this runner.

Run:
  python lessons/11_mission/mission_demo.py            # GUI: takeoff->goto->hover->land
  python lessons/11_mission/mission_demo.py --headless  # same, no window
  python lessons/11_mission/mission_demo.py --selftest   # scripted checks (CI)
"""

import sys

try:
    from nanodrone.mission import GoTo, Hover, Land, Mission, Takeoff
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import the mission runner:", exc)
    sys.exit(1)


def demo(gui: bool) -> None:
    """Fly a simple plan: take off, go to a point (facing it), hover, land."""
    plan = [
        Takeoff(height=1.0),
        GoTo([1.0, 0.0, 1.2], face=True),
        Hover(seconds=2.0),
        Land(),
    ]
    result = Mission(plan, gui=gui).run()
    print(
        f"Done: {' > '.join(result['history'])}; "
        f"moved {result['moved']:.2f} m, landed at z={result['final_z']:.2f}."
    )


def selftest() -> None:
    """Headless checks: (1) a normal plan runs and lands; (2) an out-of-bounds
    goal trips Failsafe and still ends safe on the ground."""
    # 1. Normal mission ----------------------------------------------------
    plan = [
        Takeoff(height=1.0),
        GoTo([1.0, 0.0, 1.2], face=True),
        Hover(seconds=1.0),
        Land(),
    ]
    r = Mission(plan, gui=False).run(max_seconds=20.0)
    print(
        f"MISSION OK: ran {len(r['history'])} states "
        f"[{'>'.join(r['history'])}], moved {r['moved']:.2f} m, "
        f"landed at z={r['final_z']:.2f}"
    )
    assert r["history"] == ["Takeoff", "GoTo", "Hover", "Land"], r["history"]
    assert not r["in_failsafe"], "normal plan should not trip failsafe"
    assert r["moved"] > 0.2, f"commands didn't move the drone ({r['moved']:.2f} m)"
    assert r["landed"], f"did not land (z={r['final_z']:.2f})"

    # 2. Failsafe: a goal outside the geofence must be caught ---------------
    breach = [
        Takeoff(height=1.0),
        GoTo([5.0, 0.0, 1.2], safe=False),  # 5 m is outside the 3 m fence
    ]
    f = Mission(breach, gui=False).run(max_seconds=20.0)
    print(
        f"FAILSAFE OK: {f['failsafe_reason']} breach -> Hover -> Land, "
        f"ended safe (z={f['final_z']:.2f})"
    )
    assert f["in_failsafe"], "out-of-bounds goal should trip failsafe"
    assert f["failsafe_reason"] == "geofence", f["failsafe_reason"]
    assert f["history"][-1] == "Failsafe", f["history"]
    assert f["landed"], f"failsafe did not land safely (z={f['final_z']:.2f})"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        demo(gui="--headless" not in sys.argv)


if __name__ == "__main__":
    main()
    sys.exit(0)
