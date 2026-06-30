"""
Lesson 16 — Graduation project: design your own mission
=======================================================
Every lesson so far handed you the task. The capstone flips it: *you* assemble a
mission from the blocks you built, and grade it against a rubric (see RUBRIC.md).

This file is a minimal, valid template to copy and grow. It composes the Lesson
11 state machine into "take off, fly a little patrol, come home, land" — and,
crucially, it stays inside the course's rules: $0, sim-first, a `--selftest` that
prints `XXX OK` and asserts behaviour, and a built-in Failsafe.

To make it *your* capstone, combine at least three capabilities, e.g.:
  * voice-driven transitions   (Lesson 12: nanodrone.mission_events)
  * find / follow a person     (Lesson 13)
  * map the room while patrolling (Lesson 14a: nanodrone.map)
Then run validate_mission.py to check the structure, and grade with RUBRIC.md.

Run:
  python lessons/16_capstone/template_mission.py            # GUI
  python lessons/16_capstone/template_mission.py --headless  # no window
  python lessons/16_capstone/template_mission.py --selftest   # asserts (CI)
"""

import sys

try:
    from nanodrone.mission import GoTo, Hover, Land, Mission, Takeoff
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import the mission runner:", exc)
    sys.exit(1)

CRUISE = 1.1


def build_plan():
    """The mission as a list of states — this is what you redesign for your own
    capstone. Keep a Takeoff first and a Land last; the runner adds Failsafe."""
    return [
        Takeoff(height=CRUISE),
        GoTo([1.3, 0.0, CRUISE], face=True),
        GoTo([1.3, 1.3, CRUISE], face=True),
        Hover(seconds=1.0),
        GoTo([0.0, 0.0, CRUISE]),  # come home
        Land(),
    ]


def fly(gui: bool):
    m = Mission(build_plan(), start=(0.0, 0.0, 0.1), gui=gui)
    return m.run(max_seconds=40.0)


def selftest() -> None:
    expected = ["Takeoff", "GoTo", "GoTo", "Hover", "GoTo", "Land"]
    r = fly(gui=False)
    print(
        f"CAPSTONE-DEMO OK: ran {len(r['history'])} states "
        f"[{'>'.join(r['history'])}], returned home, landed at z={r['final_z']:.2f}"
    )
    assert r["history"] == expected, r["history"]
    assert not r["in_failsafe"], f"unexpected failsafe ({r['failsafe_reason']})"
    assert r["landed"], f"did not land (z={r['final_z']:.2f})"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        fly(gui="--headless" not in sys.argv)


if __name__ == "__main__":
    main()
    sys.exit(0)
