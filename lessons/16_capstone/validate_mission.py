"""
Lesson 16 — mission validator
=============================
Grade the *structure* of any capstone mission before you fly it. The course's
rule "every script has a --selftest that asserts behaviour" now applies to the
mission you designed: this checks the plan is well-formed and safe, then runs it.

Checks (the hard gates from RUBRIC.md):
  * starts with Takeoff, ends with Land
  * every non-terminal phase is *guarded* — it overrides is_done, so the mission
    can actually advance (a phase left on the base State.is_done would hang)
  * a Failsafe is wired in (the runner always has one)
  * the mission's own --selftest is green (it really takes off, moves, lands)

Point it at your own mission by importing its build_plan(); by default it
validates template_mission.py.

Run:
  python lessons/16_capstone/validate_mission.py
  python lessons/16_capstone/validate_mission.py --selftest   # same, asserts (CI)
"""

import os
import sys

try:
    from nanodrone.mission import Failsafe, Land, Mission, State, Takeoff

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import template_mission
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 16 dependencies:", exc)
    sys.exit(1)


def validate(build_plan, run_selftest) -> dict:
    plan = build_plan()
    n_states = len(plan)
    n_trans = n_states - 1

    assert n_states >= 2, "a mission needs at least a Takeoff and a Land"
    assert isinstance(plan[0], Takeoff), "mission must start with Takeoff"
    assert isinstance(plan[-1], Land), "mission must end with Land"

    # Guarded transitions: a non-terminal phase must override is_done, or the
    # runner can never leave it. (Land is terminal; it ends the run.)
    unguarded = [
        type(s).__name__ for s in plan[:-1] if type(s).is_done is State.is_done
    ]
    assert not unguarded, f"unguarded phases (never advance): {unguarded}"

    # Failsafe is always wired into the runner.
    m = Mission(plan)
    assert isinstance(m._failsafe, Failsafe), "no Failsafe wired in"

    run_selftest()  # the mission's own --selftest must pass (really flies + lands)
    return {"states": n_states, "transitions": n_trans}


def main() -> None:
    info = validate(template_mission.build_plan, template_mission.selftest)
    print(
        f"CAPSTONE OK: graph valid ({info['states']} states, "
        f"{info['transitions']} transitions), has Takeoff+Land+Failsafe, "
        f"all transitions guarded, selftest green"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
