"""
Lesson 24 — Tello backend: same protocol, a real drone behind it
================================================================
Maps the course's flight protocol (nanodrone.protocol's 13 actions) onto a real
DJI/Ryze Tello via DJITelloPy. The Tello is the cheapest way to put the *same*
JSON commands on a real drone (~US$100, Wi-Fi, one pip) — the AI runs off-board,
so it's NOT the offline GAP8 goal, but it's the safe first real flight and proof
the protocol is portable: only the controller behind it changes.

FakeTello records the calls so CI / no-hardware runs verify the mapping and unit
conversion without a drone (or even DJITelloPy installed).
"""

from nanodrone.protocol import DEFAULT_DEG, DEFAULT_DIST, normalize_action

TELLO_MIN_CM, TELLO_MAX_CM = 20, 500  # Tello's move-distance limits


class FakeTello:
    """Stand-in for djitellopy.Tello that just records calls (for CI/tests)."""

    def __init__(self, battery: int = 80):
        self.calls: list = []
        self._battery = battery
        self.flying = False

    def _rec(self, name, arg=None):
        self.calls.append((name, arg))

    def takeoff(self):
        self.flying = True
        self._rec("takeoff")

    def land(self):
        self.flying = False
        self._rec("land")

    def emergency(self):
        self.flying = False
        self._rec("emergency")

    def move_forward(self, cm):
        self._rec("move_forward", cm)

    def move_back(self, cm):
        self._rec("move_back", cm)

    def move_left(self, cm):
        self._rec("move_left", cm)

    def move_right(self, cm):
        self._rec("move_right", cm)

    def move_up(self, cm):
        self._rec("move_up", cm)

    def move_down(self, cm):
        self._rec("move_down", cm)

    def rotate_clockwise(self, deg):
        self._rec("rotate_clockwise", deg)

    def rotate_counter_clockwise(self, deg):
        self._rec("rotate_counter_clockwise", deg)

    def send_rc_control(self, lr, fb, ud, yaw):
        self._rec("send_rc_control", (lr, fb, ud, yaw))

    def get_battery(self):
        return self._battery


def _cm(metres: float) -> int:
    """Metres -> Tello centimetres, clamped to its valid range."""
    return int(max(TELLO_MIN_CM, min(TELLO_MAX_CM, round(metres * 100))))


class TelloBackend:
    """Translate one protocol command into a Tello call. `apply_command` returns
    the (method, arg) it issued, so tests can check the mapping + units."""

    def __init__(self, tello):
        self.tello = tello

    def apply_command(self, cmd: dict):
        action = normalize_action(cmd.get("action", ""))
        dist = float(cmd.get("distance", DEFAULT_DIST))
        deg = int(round(float(cmd.get("degrees", DEFAULT_DEG))))
        t = self.tello
        table = {
            "takeoff": (t.takeoff, None),
            "land": (t.land, None),
            "emergency_stop": (t.emergency, None),
            "forward": (t.move_forward, _cm(dist)),
            "back": (t.move_back, _cm(dist)),
            "left": (t.move_left, _cm(dist)),
            "right": (t.move_right, _cm(dist)),
            "up": (t.move_up, _cm(dist)),
            "down": (t.move_down, _cm(dist)),
            "turn_left": (t.rotate_counter_clockwise, deg),
            "turn_right": (t.rotate_clockwise, deg),
        }
        if action in ("stop", "hover"):
            t.send_rc_control(0, 0, 0, 0)  # hold still
            return ("send_rc_control", (0, 0, 0, 0))
        if action not in table:
            return None
        fn, arg = table[action]
        fn() if arg is None else fn(arg)
        return (fn.__name__, arg)
