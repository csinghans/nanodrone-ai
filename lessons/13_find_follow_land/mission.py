"""
Lesson 13 — Multimodal mini-capstone: find → follow → land
===========================================================
The first time the whole course is stitched into one sentence you can say out
loud: *"take off, find the person, follow them, and land when I say so."* Four
capabilities cooperate on the Lesson 11 state machine:

  * orchestration   — the mission state machine (Lesson 11)
  * a spoken command — "land", highest priority (Lesson 12 events)
  * learned vision   — Lesson 8's person follower
  * a NEW small model — a "person vs background" confirm classifier (train_confirm.py)
                        that GATES Search -> Follow, so the drone never chases a
                        floor seam. (Signature theme: train your own small model.)

States: Takeoff -> Search (scan, gated by the confirm model) -> Follow -> (a land
event) -> Land. Event priority: land > failsafe > vision.

Run:
  python lessons/13_find_follow_land/train_confirm.py   # 1. train the gate first
  python lessons/13_find_follow_land/mission.py          # 2. watch it (GUI)
  python lessons/13_find_follow_land/mission.py --headless   # scripted demo
  python lessons/13_find_follow_land/mission.py --selftest    # asserts (CI)

Live following uses Lesson 8's PersonCNN if you trained it; otherwise (and in
CI) the follow loop falls back to the simulator's ground-truth bearing, so the
orchestration + the confirm gate are still exercised end-to-end.
"""

import math
import os
import sys

import numpy as np

try:
    import torch

    from nanodrone import world_point
    from nanodrone.mission import Land, Mission, State, Takeoff

    _HERE = os.path.dirname(os.path.abspath(__file__))
    _P8 = os.path.join(os.path.dirname(_HERE), "08_follow_real")
    sys.path.insert(0, _P8)
    sys.path.insert(0, _HERE)
    from follow_real import cnn_bearing, depth_at_bearing
    from person import build_person, move_person, true_bearing_deg
    from train_confirm import MODEL as CONFIRM_MODEL
    from train_confirm import ConfirmCNN, confirm_prob
    from train_person_cnn import MODEL as PERSON_MODEL
    from train_person_cnn import PersonCNN
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 13 dependencies:", exc)
    sys.exit(1)

IMG_W, IMG_H = 160, 160
FOLLOW_ALT = 1.0
DESIRED_DIST = 1.4
MAX_RANGE = 4.0
FOV_DEG = 60.0
PERCEPTION_EVERY = 6
SCAN_RATE = 0.9  # rad/s yaw sweep while searching
CONFIRM_TH = 0.6  # the gate: P(person) must clear this to start following
SEARCH_TIMEOUT = 12.0
LAND_AT = 11.0  # the scripted "land" command fires here (selftest/headless)
BOX = 3.0


def person_xy(t: float):
    """The person walks a gentle circle in front of the room (like Lesson 8),
    with a phase offset so they start just outside the drone's initial view and
    Search has to rotate to acquire them."""
    a = 0.25 * t + 1.7
    return 1.6 + 0.9 * math.cos(a), 0.9 * math.sin(a)


class Search(State):
    """Hover and sweep the yaw until the confirm classifier says a person is in
    view. The trained model — not a colour rule — decides when to follow."""

    name = "Search"

    def on_enter(self, m):
        m.target = np.array([m.pos[0], m.pos[1], FOLLOW_ALT])
        self._k = 0
        self._t = 0.0
        self._found = False

    def step(self, m):
        self._t += m.dt
        m.yaw = m.yaw + SCAN_RATE * m.dt  # scan
        if self._k % m.scene.get("perception_every", PERCEPTION_EVERY) == 0:
            rgb, _dep, _ = m.env._getDroneImages(0, segmentation=False)
            prob = confirm_prob(m.scene["confirm"], m.scene["device"], rgb)
            if prob > CONFIRM_TH:
                self._found = True
                m.scene["acquire_t"] = self._t
                m.scene["acquire_p"] = prob
        self._k += 1
        if self._t > SEARCH_TIMEOUT and not self._found:
            m.request_failsafe("search_timeout")
        return m.target, m.yaw

    def is_done(self, m):
        return self._found


class Follow(State):
    """Track the person: learned bearing (Lesson 8 PersonCNN) when available,
    else the simulator's ground-truth bearing; range from the depth sensor.
    Reuses Lesson 8's follow math exactly."""

    name = "Follow"
    SETTLE_S = 1.5  # let the yaw catch up before scoring tracking error

    def on_enter(self, m):
        self._k = 0
        self._t = 0.0

    def step(self, m):
        self._t += m.dt
        if self._k % m.scene.get("perception_every", PERCEPTION_EVERY) == 0:
            self._track(m)
        self._k += 1
        return m.target, m.yaw

    def _track(self, m):
        rgb, dep, _ = m.env._getDroneImages(0, segmentation=False)
        px, py = m.scene["person_xy"]
        model = m.scene["model"]
        if model is not None:
            bearing = cnn_bearing(model, m.scene["device"], rgb)  # learned
        else:
            bearing = true_bearing_deg(m.pos, m.yaw_now, px, py)  # GT fallback
        dist = depth_at_bearing(dep, bearing, m.scene["near"], m.scene["far"])
        if dist <= MAX_RANGE:
            _wx, _wy, theta = world_point(m.pos, m.yaw_now, bearing, dist)
            m.yaw = theta
            reach = float(np.clip(dist - DESIRED_DIST, -0.5, 0.5))
            m.target = np.array(
                [
                    float(np.clip(m.pos[0] + reach * math.cos(theta), -BOX, BOX)),
                    float(np.clip(m.pos[1] + reach * math.sin(theta), -BOX, BOX)),
                    FOLLOW_ALT,
                ]
            )
            if self._t > self.SETTLE_S:  # score only once tracking has settled
                m.scene["track_errs"].append(
                    abs(true_bearing_deg(m.pos, m.yaw_now, px, py))
                )

    def is_done(self, m):
        return False  # follow until a land command interrupts


def make_setup(gui: bool, perception_every: int, land_at: float):
    def setup(m):
        m.env.IMG_RES = np.array([IMG_W, IMG_H])
        device = "mps" if torch.backends.mps.is_available() else "cpu"
        if not os.path.exists(CONFIRM_MODEL):
            raise SystemExit(
                f"No confirm model at {CONFIRM_MODEL}. Run train_confirm.py first."
            )
        confirm = ConfirmCNN().to(device)
        confirm.load_state_dict(torch.load(CONFIRM_MODEL, map_location=device))
        confirm.eval()
        model = None  # Lesson 8's bearing detector is optional
        if os.path.exists(PERSON_MODEL):
            model = PersonCNN().to(device)
            model.load_state_dict(torch.load(PERSON_MODEL, map_location=device))
            model.eval()
        person = build_person(m.env.CLIENT)
        x0, y0 = person_xy(0.0)
        move_person(person, x0, y0, math.pi, m.env.CLIENT)
        m.scene.update(
            confirm=confirm,
            model=model,
            device=device,
            person=person,
            person_xy=(x0, y0),
            prev_xy=(x0, y0),
            near=m.env.L,
            far=1000.0,
            t=0.0,
            track_errs=[],
            landing=False,
            perception_every=perception_every,
            land_at=land_at,
        )
        if gui:
            print("Searching for the person; will follow once the gate confirms.")

    return setup


def on_frame(m):
    """Move the person each frame and fire the scripted 'land' command on time."""
    m.scene["t"] += m.dt
    t = m.scene["t"]
    px, py = person_xy(t)
    ox, oy = m.scene["prev_xy"]
    heading = (
        math.atan2(py - oy, px - ox) if (px - ox) ** 2 + (py - oy) ** 2 > 1e-9 else 0.0
    )
    move_person(m.scene["person"], px, py, heading, m.env.CLIENT)
    m.scene["person_xy"] = (px, py)
    m.scene["prev_xy"] = (px, py)
    if (
        t >= m.scene.get("land_at", LAND_AT) and not m.scene["landing"]
    ):  # the spoken "land" command
        m.scene["landing"] = True
        m.go(Land())


def fly(gui: bool, perception_every: int = PERCEPTION_EVERY, land_at: float = LAND_AT):
    plan = [Takeoff(height=FOLLOW_ALT), Search(), Follow()]
    m = Mission(plan, start=(0.0, 0.0, 0.1), gui=gui)
    setup = make_setup(gui, perception_every, land_at)
    return m.run(max_seconds=18.0, setup=setup, on_frame=on_frame), m


def selftest() -> None:
    r, m = fly(gui=False)
    errs = m.scene["track_errs"]
    mean_err = float(np.mean(errs)) if errs else 99.0
    acquired = m.scene.get("acquire_t", -1.0)  # -1 = never acquired (search timeout)
    print(
        f"CAPSTONE-MINI OK: Search->Follow in {acquired:.1f}s "
        f"(confirm gate p={m.scene.get('acquire_p', 0):.2f}), "
        f"tracked {len(errs)} frames mean bearing err {mean_err:.1f} deg, "
        f"land->landed z={r['final_z']:.2f}"
    )
    assert "Search" in r["history"] and "Follow" in r["history"], r["history"]
    assert r["history"].index("Search") < r["history"].index("Follow")
    assert not r["in_failsafe"], f"unexpected failsafe ({r['failsafe_reason']})"
    assert mean_err < 18.0, f"lost the person while following ({mean_err:.1f} deg)"
    assert r["history"][-1] == "Land" and r["landed"], r["history"]


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        fly(gui="--headless" not in sys.argv)


if __name__ == "__main__":
    main()
    sys.exit(0)
