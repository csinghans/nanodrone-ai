"""
Lesson 23 — flight black box (step 2): replay a log
===================================================
Read a telemetry JSONL and re-fly it: feed each logged target back to the flight
controller and watch the drone retrace the flight. Replaying a recorded target
stream should land within centimetres of where the log ended — that's the check
that the black box is faithful, and the basis for "flight review" after a real
flight.

Run (after record_flight.py):
  python lessons/23_telemetry/replay_flight.py            # GUI replay
  python lessons/23_telemetry/replay_flight.py --headless  # no window
  python lessons/23_telemetry/replay_flight.py --selftest   # asserts (CI)
"""

import os
import sys
import time

import numpy as np

try:
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics
    from gym_pybullet_drones.utils.utils import sync

    from nanodrone import chase_cam, setup_view
    from nanodrone.telemetry import load_log
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 23 dependencies:", exc)
    sys.exit(1)

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs", "flight.jsonl")


def replay(gui: bool):
    rows = load_log(LOG)
    if not rows:
        raise SystemExit(f"No log at {LOG}. Run record_flight.py first.")

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[rows[0]["x"], rows[0]["y"], rows[0]["z"]]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
        user_debug_gui=False,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    if gui:
        setup_view(env.CLIENT)
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    pos = np.array([rows[0]["x"], rows[0]["y"], rows[0]["z"]])
    for i, row in enumerate(rows):  # feed each logged setpoint back in
        obs, _, _, _, _ = env.step(action)
        pos = obs[0][0:3]
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=dt,
            state=obs[0],
            target_pos=np.array([row["tx"], row["ty"], row["tz"]]),
            target_rpy=np.array([0.0, 0.0, row["yaw"]]),
        )
        if gui:
            chase_cam(env.CLIENT, obs[0][0:3])
            sync(i, start_t, dt)
    try:
        env.close()
    except Exception:  # pragma: no cover - GUI already closed
        pass
    logged_end = np.array([rows[-1]["x"], rows[-1]["y"], rows[-1]["z"]])
    return len(rows), float(np.linalg.norm(pos - logged_end))


def main() -> None:
    selftest = "--selftest" in sys.argv
    n, err = replay(gui=not (selftest or "--headless" in sys.argv))
    print(f"REPLAY OK: replayed {n} frames, end-pos within {err:.2f} m of logged end")
    if selftest:
        assert err < 0.15, f"replay drifted from the log ({err:.2f} m)"


if __name__ == "__main__":
    main()
    sys.exit(0)
