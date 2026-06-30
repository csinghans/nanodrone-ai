"""
Lesson 27 — one flight protocol, reused everywhere (nanodrone.protocol)
=======================================================================
The DroneVoice bridge mixed the *protocol* (which actions exist, their defaults,
the body-frame math, the geofence) into the PyBullet loop. But the app, a Tello
and a Crazyflie all parse the same JSON — leave the contract welded to the sim
and each end re-implements it and they drift. This lesson pays that debt: the
contract now lives in `nanodrone.protocol` as pure data + pure functions + a JSON
Schema, and `bridge/sim_server.py` just imports it (behaviour unchanged).

Run:
  python lessons/27_protocol/protocol_demo.py            # show the contract
  python lessons/27_protocol/protocol_demo.py --selftest  # asserts (CI)
"""

import sys

import numpy as np

try:
    from nanodrone import protocol
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import nanodrone.protocol:", exc)
    sys.exit(1)

BAD = [
    {"action": "teleport"},  # unknown action
    {"action": "forward", "distance": -1.0},  # negative distance
    {"action": "up", "distance": float("nan")},  # not finite
    {"degrees": 30},  # missing action
]


def selftest() -> None:
    # 1. every known action validates
    good = [{"action": a} for a in protocol.ACTIONS]
    assert all(protocol.validate(c)[0] for c in good), "a known action was rejected"

    # 2. bad commands are rejected
    rejected = sum(0 if protocol.validate(c)[0] else 1 for c in BAD)
    assert rejected == len(BAD), f"only rejected {rejected}/{len(BAD)} bad commands"

    # 3. body-frame math: forward 1 m at yaw 0 moves +x by 1
    target = np.array(list(protocol.START), dtype=float)
    yaw, mode = protocol.step_target(
        {"action": "forward", "distance": 1.0}, target, 0.0
    )
    assert abs(target[0] - (protocol.START[0] + 1.0)) < 1e-6 and mode == "", target
    yaw, _ = protocol.step_target({"action": "turn_left", "degrees": 90}, target, yaw)
    assert abs(yaw - np.pi / 2) < 1e-6, yaw
    _, mode = protocol.step_target({"action": "land"}, target, yaw)
    assert mode == "land"
    _, mode = protocol.step_target({"action": "emergency"}, target, yaw)  # alias
    assert mode == "emergency"

    # 4. geofence clamps an out-of-box move
    far = np.array([0.0, 0.0, 1.0])
    protocol.step_target({"action": "forward", "distance": 99.0}, far, 0.0)
    assert far[0] <= protocol.BOX_XY + 1e-6, far

    # 5. schema is self-consistent
    sch = protocol.schema()
    assert sch["properties"]["action"]["enum"] == list(protocol.ACTIONS)

    print(
        f"PROTOCOL OK: {len(protocol.ACTIONS)} actions, "
        f"validate rejects {rejected}/{len(BAD)} bad cmds, schema valid, "
        f"body-frame + geofence correct"
    )


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        print(f"actions: {', '.join(protocol.ACTIONS)}")
        print(
            f"defaults: distance={protocol.DEFAULT_DIST} m, "
            f"degrees={protocol.DEFAULT_DEG}"
        )
        print(f"geofence: xy +/-{protocol.BOX_XY} m, z {protocol.BOX_Z} m")
        import json

        print("JSON Schema:\n" + json.dumps(protocol.schema(), indent=2))


if __name__ == "__main__":
    main()
    sys.exit(0)
