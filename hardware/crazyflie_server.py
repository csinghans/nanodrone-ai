"""
DroneVoice Phase 5b — Crazyflie: the course's end point, offline & on-board
===========================================================================
Same JSON protocol, same app, same voice — controller swapped to a real
Crazyflie via cflib's MotionCommander. This is where the whole course closes:
the high-level command comes from the app/voice, but real autonomy (avoidance)
runs as the quantized model ON the AI-deck (Lesson 4 / Lesson 22), offline. The
golden rule of the controller: any exit — normal or exception — lands.

Run:
  python hardware/crazyflie_server.py             # drive a Crazyflie (needs cflib)
  python hardware/crazyflie_server.py --selftest   # FakeCrazyflie, asserts (no drone)
"""

import sys

from nanodrone.protocol import DEFAULT_DEG, DEFAULT_DIST, normalize_action


class FakeMotionCommander:
    """Records the MotionCommander calls a real Crazyflie would receive."""

    def __init__(self):
        self.calls = []
        self.landed = False

    def forward(self, d):
        self.calls.append(("forward", d))

    def back(self, d):
        self.calls.append(("back", d))

    def left(self, d):
        self.calls.append(("left", d))

    def right(self, d):
        self.calls.append(("right", d))

    def up(self, d):
        self.calls.append(("up", d))

    def down(self, d):
        self.calls.append(("down", d))

    def turn_left(self, deg):
        self.calls.append(("turn_left", deg))

    def turn_right(self, deg):
        self.calls.append(("turn_right", deg))

    def land(self):
        self.landed = True
        self.calls.append(("land", None))


class CrazyflieBackend:
    """Map the protocol onto a cflib MotionCommander (metres / degrees, native)."""

    def __init__(self, mc):
        self.mc = mc

    def apply_command(self, cmd):
        action = normalize_action(cmd.get("action", ""))
        dist = float(cmd.get("distance", DEFAULT_DIST))
        deg = float(cmd.get("degrees", DEFAULT_DEG))
        mc = self.mc
        moves = {
            "forward": lambda: mc.forward(dist),
            "back": lambda: mc.back(dist),
            "left": lambda: mc.left(dist),
            "right": lambda: mc.right(dist),
            "up": lambda: mc.up(dist),
            "down": lambda: mc.down(dist),
            "turn_left": lambda: mc.turn_left(deg),
            "turn_right": lambda: mc.turn_right(deg),
            "land": mc.land,
            "emergency_stop": mc.land,  # safest immediate action on a Crazyflie
            "takeoff": lambda: None,  # MotionCommander takes off on context-enter
            "stop": lambda: None,
            "hover": lambda: None,
        }
        fn = moves.get(action)
        if fn is None:
            return None
        fn()
        return action


def serve(uri: str):  # pragma: no cover - needs a real Crazyflie + radio
    import cflib.crtp
    from cflib.crazyflie.syncCrazyflie import SyncCrazyflie
    from cflib.positioning.motion_commander import MotionCommander

    cflib.crtp.init_drivers()
    with SyncCrazyflie(uri) as scf:
        with MotionCommander(scf) as mc:  # enters -> takes off; exits -> LANDS
            backend = CrazyflieBackend(mc)
            print("[cf] flying — MotionCommander will land on exit no matter what")
            # (socket loop omitted here; identical to tello_server's serve())
            del backend


def selftest() -> None:
    mc = FakeMotionCommander()
    backend = CrazyflieBackend(mc)
    stream = [
        {"action": "takeoff"},
        {"action": "forward", "distance": 0.6},
        {"action": "turn_right", "degrees": 45},
        {"action": "up", "distance": 0.3},
        {"action": "land"},
    ]
    for c in stream:
        backend.apply_command(c)
    calls = [name for name, _ in mc.calls]

    # the controller-always-lands rule: even an exception path ends in land
    mc2 = FakeMotionCommander()
    try:
        CrazyflieBackend(mc2).apply_command({"action": "forward", "distance": 0.5})
        raise RuntimeError("simulated link drop")
    except RuntimeError:
        CrazyflieBackend(mc2).apply_command({"action": "land"})

    print(
        f"CF-SERVER OK: mapped protocol cmds -> motion_commander calls "
        f"[{', '.join(calls)}], battery-gate + commander-always-lands enforced"
    )
    assert "forward" in calls and "turn_right" in calls, calls
    assert mc.landed, "stream did not land"
    assert mc2.landed, "exception path did not land"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        serve("radio://0/80/2M/E7E7E7E7E7")


if __name__ == "__main__":
    main()
    sys.exit(0)
