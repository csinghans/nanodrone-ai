"""
Lesson 1 — Hover demo
=====================
Your first simulated nano-drone. It takes off and holds a steady hover at
1 metre for 10 seconds, using gym-pybullet-drones' built-in PID controller.

This is the "hello world" of drone autonomy. Notice the two-layer split the
course keeps coming back to:

  * The PID *controller* (DSLPIDControl) = the low-level flight controller.
    It turns "I want to be at (0, 0, 1)" into motor commands. You don't write
    this; it ships with the simulator, just like real firmware (PX4/Crazyflie).

  * The loop below = your "companion AI". For now it just hands the controller
    a fixed target. In later lessons this is where perception + a neural net
    will decide the target instead.

Run:       python lessons/01_hover/hover_demo.py
Selftest:  python lessons/01_hover/hover_demo.py --selftest
"""

import sys
import time

import numpy as np

try:
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics
    from gym_pybullet_drones.utils.utils import sync
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import gym-pybullet-drones:", exc)
    print(
        "\nInstall it inside the conda env, then retry:\n"
        "  conda activate nanodrone-ai\n"
        "  pip install 'gym-pybullet-drones @ "
        "git+https://github.com/utiasDSL/gym-pybullet-drones.git'\n"
        "\nIf the pip line fails, clone and install from source:\n"
        "  git clone https://github.com/utiasDSL/gym-pybullet-drones\n"
        "  pip install -e ./gym-pybullet-drones"
    )
    sys.exit(1)


# --- Flight plan -----------------------------------------------------------
START_POS = np.array([[0.0, 0.0, 0.1]])  # start near the ground
TARGET_POS = np.array([0.0, 0.0, 1.0])  # hover target: 1 m straight up
DURATION_SEC = 10  # how long to hover
SELFTEST_SEC = 5  # selftest: enough time to climb and settle
HOVER_TOL_M = 0.1  # "steady hover" = within 10 cm of the target


def main(gui: bool = True, duration_sec: int = DURATION_SEC) -> np.ndarray:
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,  # the Crazyflie 2.x "X" frame
        num_drones=1,
        initial_xyzs=START_POS,
        physics=Physics.PYB,
        pyb_freq=240,  # physics steps per second
        ctrl_freq=48,  # control updates per second (your AI loop rate)
        gui=gui,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)

    action = np.zeros((1, 4))  # 4 motor RPMs for 1 drone
    start = time.time()
    total_steps = duration_sec * env.CTRL_FREQ

    for i in range(total_steps):
        # 1. Advance the physics with the latest motor command.
        obs, _reward, _terminated, _truncated, _info = env.step(action)

        # 2. "Companion AI" decides the target (here: a fixed hover point).
        #    obs[0] is this drone's full state (position, orientation, ...).
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=TARGET_POS,
        )

        # 3. Keep the GUI running at wall-clock speed so it looks real.
        if gui:
            env.render()
            sync(i, start, env.CTRL_TIMESTEP)

    final_pos = obs[0][:3].copy()
    env.close()
    print(f"Done: hovered at {TARGET_POS.tolist()} for {duration_sec} s.")
    return final_pos


def selftest() -> None:
    """Headless hover + assert — the course's `XXX OK` habit starts here."""
    final_pos = main(gui=False, duration_sec=SELFTEST_SEC)
    err = abs(float(final_pos[2]) - float(TARGET_POS[2]))
    assert (
        err < HOVER_TOL_M
    ), f"hover drifted: z={final_pos[2]:.2f} m, target {TARGET_POS[2]:.1f} m"
    print(
        f"HOVER OK: held z={final_pos[2]:.2f} m "
        f"(target {TARGET_POS[2]:.1f} ± {HOVER_TOL_M} m) for {SELFTEST_SEC} s"
    )


if __name__ == "__main__":
    # --selftest: headless short hover + height assert (what CI runs).
    # --headless: the full demo without a window.
    if "--selftest" in sys.argv:
        selftest()
    else:
        main(gui="--headless" not in sys.argv)
