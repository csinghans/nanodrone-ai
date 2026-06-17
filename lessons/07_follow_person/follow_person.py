"""
Lesson 7 — Follow the pilot (drive a person, the drone follows you)
==================================================================
This combines two earlier lessons into something that feels like a real
follow-me drone:

  * You drive a little **person** around with the gamepad/keyboard
    (reusing the shared input backends — first written in Lesson 5).
  * The drone **follows you by camera** (Lesson 6's visual servoing) and now
    also **yaws to face you**, so it can trail you wherever you go — even in
    circles, not just side to side.

Vision, geometry, input and the GUI look all come from the shared `nanodrone`
core, so this lesson is mostly the *follow* rule plus the little person model.

Run:
  python lessons/07_follow_person/follow_person.py            # you drive (window)
  python lessons/07_follow_person/follow_person.py --headless # scripted, no window (CI)
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

from nanodrone import (
    ORANGE,
    chase_cam,
    detect_blob,
    make_input,
    setup_view,
    world_point,
)

START = np.array([0.0, 0.0, 1.0])
DESIRED_DIST = 1.3  # how far behind the person the drone trails (m)
FOLLOW_ALT = 1.0  # drone altitude while following (m)
PERSON_SPEED = 0.9  # how fast you can drive the person (m/s)
IMG_W, IMG_H = 160, 160
PERCEPTION_EVERY = 6  # camera runs every N control steps (perception is slow)
BOX_XY = 3.0


def build_person(client: int):
    """An orange 'person' (torso + head) plus a dark 'nose' marker that shows
    which way they face. The nose is non-orange so it doesn't bias the detector."""
    orange = [1.0, 0.5, 0.0, 1.0]
    torso_vis = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[0.12, 0.09, 0.32],
        rgbaColor=orange,
        physicsClientId=client,
    )
    head_vis = p.createVisualShape(
        p.GEOM_SPHERE, radius=0.13, rgbaColor=orange, physicsClientId=client
    )
    nose_vis = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[0.07, 0.04, 0.04],
        rgbaColor=[0.1, 0.15, 0.35, 1.0],
        physicsClientId=client,
    )
    return tuple(
        p.createMultiBody(baseMass=0, baseVisualShapeIndex=v, physicsClientId=client)
        for v in (torso_vis, head_vis, nose_vis)
    )


def move_person(ids, x: float, y: float, heading: float, client: int) -> None:
    """Place the person at (x, y) facing `heading` (radians, 0 = +x)."""
    torso, head, nose = ids
    quat = p.getQuaternionFromEuler([0, 0, heading])
    p.resetBasePositionAndOrientation(torso, [x, y, 0.42], quat, physicsClientId=client)
    p.resetBasePositionAndOrientation(head, [x, y, 0.87], quat, physicsClientId=client)
    nx, ny = x + 0.16 * math.cos(heading), y + 0.16 * math.sin(heading)
    p.resetBasePositionAndOrientation(nose, [nx, ny, 0.9], quat, physicsClientId=client)


def scripted_person_xy(t: float):
    """Headless path: the person walks a slow circle, so the drone must yaw to
    keep facing them (exercises the full follow loop without a controller)."""
    return 1.5 + 1.0 * math.cos(0.3 * t), 1.0 * math.sin(0.3 * t)


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

    person = build_person(env.CLIENT)
    person_x, person_y, person_heading = 2.5, 0.0, math.pi  # start facing the drone
    move_person(person, person_x, person_y, person_heading, env.CLIENT)

    backend = None
    if gui:
        setup_view(env.CLIENT)
        backend, _ = make_input("xbox")  # falls back to keyboard automatically
        print("Drive the person; the drone follows you. Ctrl-C to quit.")

    drone_target = START.copy()
    target_yaw = 0.0
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    duration = 14 * env.CTRL_FREQ if not gui else 10**9
    bearing_errs = []

    i = 0
    try:
        while i < duration:
            t = i * dt
            prev_x, prev_y = person_x, person_y
            if gui:
                fwd, strafe, _up, _yaw = backend.read()  # world-frame person drive
                person_x = float(
                    np.clip(person_x + fwd * PERSON_SPEED * dt, -BOX_XY, BOX_XY)
                )
                person_y = float(
                    np.clip(person_y + strafe * PERSON_SPEED * dt, -BOX_XY, BOX_XY)
                )
            else:
                person_x, person_y = scripted_person_xy(t)
            dx, dy = person_x - prev_x, person_y - prev_y
            if dx * dx + dy * dy > 1e-8:  # face the way you're walking
                person_heading = math.atan2(dy, dx)
            move_person(person, person_x, person_y, person_heading, env.CLIENT)

            obs, _, _, _, _ = env.step(action)
            state = obs[0]
            drone_pos, drone_yaw = state[0:3], state[9]

            if i % PERCEPTION_EVERY == 0:
                rgb, dep, _ = env._getDroneImages(0, segmentation=False)
                blob = detect_blob(rgb, dep, ORANGE, near, far)
                if blob.found:
                    px, py, theta = world_point(
                        drone_pos, drone_yaw, blob.bearing, blob.distance
                    )
                    target_yaw = theta  # turn to face the person
                    reach = blob.distance - DESIRED_DIST  # close the gap
                    drone_target = np.array(
                        [
                            np.clip(
                                drone_pos[0] + reach * math.cos(theta), -BOX_XY, BOX_XY
                            ),
                            np.clip(
                                drone_pos[1] + reach * math.sin(theta), -BOX_XY, BOX_XY
                            ),
                            FOLLOW_ALT,
                        ]
                    )
                    if t > 5:  # measure tracking after the drone catches up
                        bearing_errs.append(abs(blob.bearing))

            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=state,
                target_pos=drone_target,
                target_rpy=np.array([0.0, 0.0, target_yaw]),
            )
            if gui:
                chase_cam(env.CLIENT, drone_pos)  # camera follows the drone
                env.render()
                sync(i, start_t, dt)
            i += 1
    except KeyboardInterrupt:
        print("\nStopping (you quit).")
    except p.error:
        print("\nSimulator window closed — stopping.")

    if backend is not None:
        backend.close()
    try:
        env.close()
    except p.error:
        pass

    if not gui:
        mean_err = float(np.mean(bearing_errs)) if bearing_errs else 99.0
        print(
            f"FOLLOW OK: tracked {len(bearing_errs)} frames while the person "
            f"circled, mean bearing error {mean_err:.1f} deg."
        )
        assert mean_err < 15.0, f"drone lost the person ({mean_err:.1f} deg)"


if __name__ == "__main__":
    main(gui="--headless" not in sys.argv)
    sys.exit(0)
