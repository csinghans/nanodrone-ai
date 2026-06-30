"""
Lesson 14a — Simple mapping & autonomous patrol
================================================
Every mission so far chased a single thing (a point, a person). Real autonomy
also has to *cover a space* and remember what's in it. This lesson gives the
drone its first **spatial memory**: it flies a patrol of the room's corners and,
from the depth camera, builds a 2D occupancy grid of where the obstacles are.

It runs on the Lesson 11 state machine — the patrol is just `GoTo` waypoints with
a `Scan` (turn in place) at each one — and uses `nanodrone.map.OccupancyGrid`,
which projects whole depth columns into the world (the same geometry the
follower used for a single point, Lesson 2/8).

Run:
  python lessons/14a_map_patrol/patrol.py            # GUI patrol, saves output/map.png
  python lessons/14a_map_patrol/patrol.py --headless  # same, no window
  python lessons/14a_map_patrol/patrol.py --selftest   # asserts the map (CI)
"""

import math
import os
import sys

import numpy as np

try:
    from nanodrone.map import OccupancyGrid
    from nanodrone.mission import GoTo, Land, Mission, State, Takeoff

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from scene import build_scene
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 14a dependencies:", exc)
    sys.exit(1)

PATROL_ALT = 1.1
CORNERS = [(1.6, 1.6), (-1.6, 1.6), (-1.6, -1.6), (1.6, -1.6)]
SCAN_RATE = 1.5  # rad/s turn-in-place while scanning a corner
PERCEPTION_EVERY = 8
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "map.png")


def _wrap(a: float) -> float:
    """Wrap an angle to [-pi, pi] so the yaw setpoint never grows unbounded
    (a huge yaw target makes the controller flip and the drone tumble)."""
    return (a + math.pi) % (2 * math.pi) - math.pi


class Scan(State):
    """Turn a full circle in place so the depth camera sweeps every direction."""

    name = "Scan"

    def on_enter(self, m):
        m.target = np.array([m.pos[0], m.pos[1], PATROL_ALT])
        self._acc = 0.0

    def step(self, m):
        m.yaw = _wrap(m.yaw + SCAN_RATE * m.dt)
        self._acc += SCAN_RATE * m.dt
        return m.target, m.yaw

    def is_done(self, m):
        return self._acc >= 2 * math.pi


def make_setup():
    def setup(m):
        m.env.IMG_RES = np.array([160, 160])
        m.scene["truth"] = build_scene(m.env.CLIENT)
        m.scene["grid"] = OccupancyGrid(extent=3.0, res=0.3)
        m.scene["near"] = m.env.L
        m.scene["far"] = 1000.0
        m.scene["path"] = []
        m.scene["k"] = 0

    return setup


def on_frame(m):
    m.scene["path"].append((float(m.pos[0]), float(m.pos[1])))
    if m.scene["k"] % PERCEPTION_EVERY == 0:
        _rgb, dep, _ = m.env._getDroneImages(0, segmentation=False)
        m.scene["grid"].integrate(
            m.pos, m.yaw_now, dep, m.scene["near"], m.scene["far"]
        )
    m.scene["k"] += 1


def fly(gui: bool):
    # GoTo with face=False: keep a fixed heading while translating (a quadcopter
    # flies any direction regardless of yaw), so there are no large yaw flips
    # between legs — the per-corner Scan provides the all-round map coverage.
    plan = [Takeoff(height=PATROL_ALT)]
    for cx, cy in CORNERS:
        plan.append(GoTo([cx, cy, PATROL_ALT]))
        plan.append(Scan())
    plan.append(Land())
    m = Mission(plan, start=(0.0, 0.0, 0.1), gui=gui)
    r = m.run(max_seconds=80.0, setup=make_setup(), on_frame=on_frame)
    grid = m.scene["grid"]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    grid.save_png(OUT, drone_path=m.scene["path"], truth=m.scene["truth"])
    return r, m


def selftest() -> None:
    r, m = fly(gui=False)
    grid, truth = m.scene["grid"], m.scene["truth"]
    cells = grid.occupied()
    visited = r["history"].count("Scan")
    found = [t for t in truth if grid.near(t[0], t[1], radius=0.5)]
    print(
        f"PATROL OK: visited {visited}/{len(CORNERS)} waypoints, "
        f"mapped {len(cells)} occupied cells, "
        f"found {len(found)}/{len(truth)} known obstacles, saved {OUT}"
    )
    assert visited == len(CORNERS), f"only reached {visited}/{len(CORNERS)} corners"
    assert r["landed"], f"did not land (z={r['final_z']:.2f})"
    assert len(found) == len(truth), f"missed obstacles: found {found} of {truth}"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        fly(gui="--headless" not in sys.argv)


if __name__ == "__main__":
    main()
    sys.exit(0)
