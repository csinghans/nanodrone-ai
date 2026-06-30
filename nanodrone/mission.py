"""nanodrone.mission — turn the flight loop into a state machine (Lesson 11).

Every flight script so far (Lessons 5–10, the DroneVoice bridge) copied the same
`CtrlAviary + DSLPIDControl` while-loop: build the env, each frame work out a
target position + heading, hand it to the PID controller, advance the physics.
To string behaviours together ("take off -> go somewhere -> hover -> land") you
first need something that knows *which phase you are in* and *when to move on*.

That something is a **state machine** — the mental model real autonomy stacks
(ROS, PX4) are built on. This module factors the shared loop out once so later
lessons stop copying it:

  * `State`     — one phase of a flight (Takeoff, Hover, GoTo, Land, Failsafe).
  * `Mission`   — the runner: owns the env + controller + the shared while-loop,
                  steps through a list of states, and watches a geofence the
                  whole time. If a state ever asks to leave the safe box (or you
                  trip it yourself), it drops everything into `Failsafe`.

The two-layer split the course keeps coming back to still holds: a `State` only
ever produces a *high-level setpoint* (target position + yaw); `DSLPIDControl`
(the firmware) turns that into motor speeds. A state never touches a motor.

Reused/aligned with the rest of the course: the run loop and the gentle landing
descent come from `bridge/sim_server.py`; the geofence box matches the bridge's
`BOX_XY`/`BOX_Z`; the GUI camera comes from `nanodrone.view`; the
"scripted + assert + print OK" self-test style comes from `nanodrone.input`.
"""

import math

import numpy as np

try:
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics
    from gym_pybullet_drones.utils.utils import sync
except ImportError as exc:  # pragma: no cover - friendly beginner message
    raise ImportError(
        "nanodrone.mission needs gym-pybullet-drones. Inside the conda env:\n"
        "  conda activate nanodrone-ai\n"
        "  pip install 'gym-pybullet-drones @ "
        "git+https://github.com/utiasDSL/gym-pybullet-drones.git'"
    ) from exc

from .view import chase_cam, setup_view

# Indoor geofence — same safe box as the DroneVoice bridge: 6x6 m, 0.3-2.5 m high.
FENCE_XY = 3.0
FENCE_Z = (0.3, 2.5)

HOVER_HEIGHT = 1.0  # default take-off / cruise height (m)
LAND_HEIGHT = FENCE_Z[0]  # "on the ground" for our purposes (m)
LAND_RATE = 0.4  # how fast Land lowers the target (m/s) — from the bridge
REACH_TOL = 0.12  # GoTo is "there" within this many metres
TAKEOFF_TOL = 0.08  # Takeoff is done within this of the target height


def in_fence(target, xy=FENCE_XY, z=FENCE_Z) -> bool:
    """Is this target position inside the safe box? (small epsilon for floats)"""
    return (
        abs(target[0]) <= xy + 1e-6
        and abs(target[1]) <= xy + 1e-6
        and z[0] - 1e-6 <= target[2] <= z[1] + 1e-6
    )


def clip_to_fence(target, xy=FENCE_XY, z=FENCE_Z) -> np.ndarray:
    """Clamp a target into the safe box (mirrors the bridge's np.clip)."""
    t = np.asarray(target, dtype=float).copy()
    t[0] = float(np.clip(t[0], -xy, xy))
    t[1] = float(np.clip(t[1], -xy, xy))
    t[2] = float(np.clip(t[2], *z))
    return t


# --- States ---------------------------------------------------------------
# A State is one phase. It reads the live drone state off the Mission (`m.pos`,
# `m.yaw_now`) and returns the setpoint it wants this frame: (target_pos, yaw).
# `on_enter` runs once when the phase begins; `is_done` says when to advance.


class State:
    """Base class. Subclass and override what you need."""

    name = "State"

    def on_enter(self, m: "Mission") -> None:
        """Called once when this phase starts. Often sets `m.target`."""

    def step(self, m: "Mission"):
        """Return the (target_pos, yaw) this phase wants this frame.
        Default: hold whatever the mission already commands."""
        return m.target, m.yaw

    def is_done(self, m: "Mission") -> bool:
        """Return True when ready to advance to the next phase."""
        return False


class Takeoff(State):
    """Rise straight up to `height`, keeping the current x/y."""

    name = "Takeoff"

    def __init__(self, height: float = HOVER_HEIGHT):
        self.height = height

    def on_enter(self, m: "Mission") -> None:
        m.target = clip_to_fence([m.pos[0], m.pos[1], self.height])

    def is_done(self, m: "Mission") -> bool:
        return abs(m.pos[2] - self.height) < TAKEOFF_TOL


class Hover(State):
    """Hold the current target for `seconds`."""

    name = "Hover"

    def __init__(self, seconds: float = 1.0):
        self.seconds = seconds
        self._t = 0.0

    def on_enter(self, m: "Mission") -> None:
        self._t = 0.0  # keep the existing target — just sit there

    def step(self, m: "Mission"):
        self._t += m.dt
        return m.target, m.yaw

    def is_done(self, m: "Mission") -> bool:
        return self._t >= self.seconds


class GoTo(State):
    """Fly to a world point (x, y, z). Optionally face the direction of travel.

    Set `safe=False` to *deliberately* request a point outside the geofence —
    the Mission's watchdog will catch it and trip Failsafe. That is how the
    self-test exercises the safety net."""

    name = "GoTo"

    def __init__(
        self, xyz, face: bool = False, tol: float = REACH_TOL, safe: bool = True
    ):
        self.goal = np.asarray(xyz, dtype=float)
        self.face = face
        self.tol = tol
        self.safe = safe

    def on_enter(self, m: "Mission") -> None:
        m.target = self.goal.copy()  # left un-clipped so an unsafe goal is visible
        if self.face:
            dx, dy = self.goal[0] - m.pos[0], self.goal[1] - m.pos[1]
            if math.hypot(dx, dy) > 1e-3:
                m.yaw = math.atan2(dy, dx)

    def step(self, m: "Mission"):
        return self.goal, m.yaw

    def is_done(self, m: "Mission") -> bool:
        return float(np.linalg.norm(m.pos - self.goal)) < self.tol


class Land(State):
    """Lower the target gently to the ground, then settle."""

    name = "Land"

    def on_enter(self, m: "Mission") -> None:
        # keep current x/y; we will walk z down from wherever we are
        m.target = m.target.copy()

    def step(self, m: "Mission"):
        t = m.target.copy()
        t[2] = max(LAND_HEIGHT, t[2] - LAND_RATE * m.dt)
        return t, m.yaw

    def is_done(self, m: "Mission") -> bool:
        # Done only once the *drone itself* has settled near the ground — not the
        # moment the target reaches the floor (the drone lags the setpoint).
        return m.target[2] <= LAND_HEIGHT + 1e-3 and m.pos[2] <= LAND_HEIGHT + 0.1


class Failsafe(State):
    """The safety net. Freeze in place, hold briefly, then land — no matter what
    the rest of the plan wanted. Tripped by a geofence breach, a perception
    timeout, or `m.request_failsafe(...)` (e.g. a lost radio link)."""

    name = "Failsafe"

    def __init__(self, hover_seconds: float = 0.5):
        self.hover_seconds = hover_seconds
        self._t = 0.0
        self._landing = False
        self._land = Land()

    def on_enter(self, m: "Mission") -> None:
        # stop chasing whatever goal got us here; hold the current safe position
        m.target = clip_to_fence(m.pos)
        self._t = 0.0
        self._landing = False

    def step(self, m: "Mission"):
        self._t += m.dt
        if self._t >= self.hover_seconds:
            if not self._landing:
                self._landing = True
                self._land.on_enter(m)
            return self._land.step(m)
        return m.target, m.yaw

    def is_done(self, m: "Mission") -> bool:
        return self._landing and self._land.is_done(m)


# --- The runner ------------------------------------------------------------


class Mission:
    """Run a list of `State`s on a simulated Crazyflie, watching a geofence.

    `num_drones` is *not* hard-coded to 1 in the loop (we index `obs[0]`, but the
    env is built for one drone here); the structure leaves room for more later.
    """

    def __init__(
        self,
        states,
        *,
        start=(0.0, 0.0, 0.1),
        gui: bool = False,
        fence_xy: float = FENCE_XY,
        fence_z=FENCE_Z,
        failsafe: "Failsafe | None" = None,
    ):
        self.plan = list(states)
        self.start = np.asarray(start, dtype=float)
        self.gui = gui
        self.fence_xy = fence_xy
        self.fence_z = fence_z
        self._failsafe = failsafe or Failsafe()

        # live state, filled in each frame and read by the States
        self.pos = self.start.copy()
        self.yaw_now = 0.0
        self.target = self.start.copy()
        self.yaw = 0.0
        self.dt = 0.0

        self.state: State | None = None
        self._idx = -1
        self.in_failsafe = False
        self.failsafe_reason = ""
        self.history: list[str] = []  # names of states entered, for assertions

    # -- transitions --
    def _enter(self, state: State) -> None:
        self.state = state
        self.history.append(state.name)
        state.on_enter(self)

    def _advance(self) -> bool:
        """Move to the next planned state. Returns False when the plan is done."""
        if self.in_failsafe:
            return False  # once in Failsafe we don't resume the plan
        self._idx += 1
        if self._idx >= len(self.plan):
            return False
        self._enter(self.plan[self._idx])
        return True

    def request_failsafe(self, reason: str) -> None:
        """Drop into Failsafe now (geofence, lost link, perception timeout...)."""
        if not self.in_failsafe:
            self.in_failsafe = True
            self.failsafe_reason = reason
            self._enter(self._failsafe)

    # -- the shared flight loop (this is what every lesson used to copy) --
    def run(self, max_seconds: float = 20.0) -> dict:
        import time

        env = CtrlAviary(
            drone_model=DroneModel.CF2X,
            num_drones=1,
            initial_xyzs=np.array([self.start]),
            physics=Physics.PYB,
            pyb_freq=240,
            ctrl_freq=48,
            gui=self.gui,
            user_debug_gui=False,
        )
        ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
        if self.gui:
            setup_view(env.CLIENT)

        self.dt = env.CTRL_TIMESTEP
        action = np.zeros((1, 4))
        max_steps = int(max_seconds * env.CTRL_FREQ)
        wall_start = time.time()

        # one step to get an initial observation, then enter the first phase
        obs, _, _, _, _ = env.step(action)
        self.pos = obs[0][0:3].copy()
        self.yaw_now = float(obs[0][9])
        self._advance()  # enter plan[0]

        i = 0
        try:
            while self.state is not None and i < max_steps:
                # 1. SENSE — read the live drone state
                self.pos = obs[0][0:3].copy()
                self.yaw_now = float(obs[0][9])

                # 2. DECIDE — ask the current phase what setpoint it wants
                want_target, want_yaw = self.state.step(self)

                # 2b. WATCHDOG — a phase asking to leave the box is a breach
                if not self.in_failsafe and not in_fence(
                    want_target, self.fence_xy, self.fence_z
                ):
                    self.request_failsafe("geofence")
                    want_target, want_yaw = self.state.step(self)

                self.target = clip_to_fence(want_target, self.fence_xy, self.fence_z)
                self.yaw = want_yaw

                # 3. ACT — firmware turns the setpoint into motor speeds
                action[0, :], _, _ = ctrl.computeControlFromState(
                    control_timestep=self.dt,
                    state=obs[0],
                    target_pos=self.target,
                    target_rpy=np.array([0.0, 0.0, self.yaw]),
                )
                obs, _, _, _, _ = env.step(action)

                if self.gui:
                    chase_cam(env.CLIENT, obs[0][0:3])
                    sync(i, wall_start, self.dt)

                # 4. TRANSITION — advance when the phase reports done
                if self.state.is_done(self):
                    if not self._advance():
                        break
                i += 1
        finally:
            try:
                env.close()
            except Exception:  # pragma: no cover - GUI window already closed
                pass

        moved = float(np.linalg.norm(self.pos[0:2] - self.start[0:2]))
        return {
            "history": self.history,
            "steps": i,
            "moved": moved,
            "final_z": float(self.pos[2]),
            "in_failsafe": self.in_failsafe,
            "failsafe_reason": self.failsafe_reason,
            "landed": self.pos[2] <= LAND_HEIGHT + 0.12,
        }
