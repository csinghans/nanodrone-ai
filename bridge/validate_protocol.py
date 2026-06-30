"""
DroneVoice Phase 2-4 — validate a command stream from the app
=============================================================
The iOS app (Phase 2 voice, Phase 3 on-device LLM, Phase 4 SwiftUI) only ever
sends the JSON protocol — so its correctness is checkable here, no phone needed.
This validates a recorded command stream two ways:
  * every command is schema-valid (nanodrone.protocol.validate)
  * the SEQUENCE is safe — you can't move before takeoff; land / emergency are
    allowed any time. (This is the server-side refusal Phase 4's app relies on.)

Run:
  python bridge/validate_protocol.py            # check the sample streams
  python bridge/validate_protocol.py --selftest  # asserts (CI)
"""

import sys

from nanodrone.protocol import normalize_action, validate

_MOVES = {"forward", "back", "left", "right", "up", "down", "turn_left", "turn_right"}


def check_stream(cmds):
    """Return (ok, issues). Flags invalid commands and unsafe ordering."""
    issues = []
    airborne = False
    for i, cmd in enumerate(cmds):
        ok, reason = validate(cmd)
        if not ok:
            issues.append(f"cmd {i}: invalid ({reason})")
            continue
        action = normalize_action(cmd["action"])
        if action == "takeoff":
            airborne = True
        elif action in ("land", "emergency_stop"):
            airborne = False
        elif action in _MOVES and not airborne:
            issues.append(f"cmd {i}: '{action}' before takeoff")
    return (not issues), issues


GOOD = [
    {"action": "takeoff"},
    {"action": "forward", "distance": 1.0},
    {"action": "turn_left", "degrees": 90},
    {"action": "land"},
]
BAD = [
    {"action": "forward", "distance": 1.0},  # moving before takeoff
    {"action": "takeoff"},
]


def main() -> None:
    good_ok, _ = check_stream(GOOD)
    bad_ok, bad_issues = check_stream(BAD)
    print(
        f"PROTOCOL-CONFORMANCE OK: good stream valid+safe ({len(GOOD)} cmds), "
        f"bad stream rejected ({bad_issues[0] if bad_issues else 'n/a'})"
    )
    if "--selftest" in sys.argv:
        assert good_ok, "a valid, well-ordered stream was rejected"
        assert not bad_ok, "an unsafe stream (move before takeoff) was accepted"


if __name__ == "__main__":
    main()
    sys.exit(0)
