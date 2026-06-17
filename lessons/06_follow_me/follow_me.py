"""
Lesson 6 — Follow-me tracking
=============================
The drone follows a moving target using only its camera — a closed visual loop
that ties together Lesson 1 (control), Lesson 2 (perception), and a simple
"decide" rule. This is *visual servoing*: see the target, work out where it is,
move to keep it centred and a fixed distance ahead.

Detection and the pixel-to-world geometry come from the shared `nanodrone`
core (the detector first written in Lesson 2), so this lesson is just the
"follow" rule.

Run:  python lessons/06_follow_me/follow_me.py
      python lessons/06_follow_me/follow_me.py --headless   # no window (CI)
"""

import math
import sys
import time

import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

from nanodrone import GREEN, detect_blob, setup_view, world_point

START = np.array([0.0, 0.0, 1.0])
DESIRED_DIST = 1.0  # how far behind the target the drone tries to stay (m)
IMG_W, IMG_H = 160, 160
PERCEPTION_EVERY = 6  # run the camera every N control steps (perception is slow)
BOX_XY, BOX_Z = 2.0, (0.3, 2.5)


def target_position(t: float) -> list:
    """Scripted motion of the green target: a lateral sweep that stays in view."""
    return [1.5 + 0.15 * math.sin(0.7 * t), 0.5 * math.sin(0.5 * t), 1.0]


def main(gui: bool = True) -> None:
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
        user_debug_gui=False,
    )
    env.IMG_RES = np.array([IMG_W, IMG_H])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    near, far = env.L, 1000.0
    if gui:
        setup_view(env.CLIENT)

    # The bright-green target the drone will chase.
    vis = p.createVisualShape(
        p.GEOM_SPHERE, radius=0.12, rgbaColor=[0, 1, 0, 1], physicsClientId=env.CLIENT
    )
    target_id = p.createMultiBody(
        baseMass=0,
        baseVisualShapeIndex=vis,
        basePosition=target_position(0.0),
        physicsClientId=env.CLIENT,
    )

    drone_target = START.copy()
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    duration = 12 * env.CTRL_FREQ if not gui else 10**9
    bearing_errs = []

    i = 0
    try:
        while i < duration:
            t = i * dt
            p.resetBasePositionAndOrientation(
                target_id, target_position(t), [0, 0, 0, 1], physicsClientId=env.CLIENT
            )
            obs, _, _, _, _ = env.step(action)
            drone_pos = obs[0][0:3]

            if i % PERCEPTION_EVERY == 0:
                rgb, dep, _ = env._getDroneImages(0, segmentation=False)
                blob = detect_blob(rgb, dep, GREEN, near, far)
                if blob.found:
                    # Drone yaw is fixed at 0 here (it doesn't turn — Lesson 7
                    # adds yaw). Trail DESIRED_DIST behind in x, match y and z.
                    px, py, _theta = world_point(
                        drone_pos, 0.0, blob.bearing, blob.distance
                    )
                    pz = drone_pos[2] + blob.distance * math.sin(
                        math.radians(blob.elevation)
                    )
                    drone_target = np.array([px - DESIRED_DIST, py, pz])
                    drone_target[0] = np.clip(drone_target[0], -BOX_XY, BOX_XY)
                    drone_target[1] = np.clip(drone_target[1], -BOX_XY, BOX_XY)
                    drone_target[2] = np.clip(drone_target[2], BOX_Z[0], BOX_Z[1])
                    if t > 4:  # measure tracking after the initial catch-up
                        bearing_errs.append(abs(blob.bearing))

            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt, state=obs[0], target_pos=drone_target
            )
            if gui:
                env.render()
                sync(i, start_t, dt)
            i += 1
    except KeyboardInterrupt:
        print("\nStopping (you quit).")
    except p.error:
        print("\nSimulator window closed — stopping.")

    try:
        env.close()
    except p.error:
        pass

    if not gui:
        mean_err = float(np.mean(bearing_errs)) if bearing_errs else 99.0
        print(
            f"FOLLOW OK: tracked {len(bearing_errs)} frames, "
            f"mean bearing error {mean_err:.1f} deg."
        )
        assert mean_err < 12.0, f"drone did not keep target centred ({mean_err:.1f})"


if __name__ == "__main__":
    main(gui="--headless" not in sys.argv)
    sys.exit(0)
