"""
Lesson 7 — Follow the pilot (drive a person, the drone follows you)
==================================================================
This combines two earlier lessons into something that feels like a real
follow-me drone:

  * You drive a little **person** around with the gamepad/keyboard
    (reusing Lesson 5's input backends).
  * The drone **follows you by camera** (Lesson 6's visual servoing) and now
    also **yaws to face you**, so it can trail you wherever you go — even in
    circles, not just side to side.

Each perception tick the drone detects the orange person, works out where you
are in the world, turns to face you, and flies to a standoff point a fixed
distance behind you.

Run:
  python lessons/07_follow_person/follow_person.py            # you drive (window)
  python lessons/07_follow_person/follow_person.py --headless # scripted, no window (CI)
"""

import math
import sys
import time

import cv2
import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

START = np.array([0.0, 0.0, 1.0])
DESIRED_DIST = 1.3  # how far behind the person the drone trails (m)
FOLLOW_ALT = 1.0  # drone altitude while following (m)
PERSON_SPEED = 0.9  # how fast you can drive the person (m/s)
IMG_W, IMG_H = 160, 160
FOV_DEG = 60.0
PERCEPTION_EVERY = 6  # camera runs every N control steps (perception is slow)
BOX_XY, BOX_Z = 3.0, (0.3, 2.5)


def build_person(client: int):
    """A minimal orange 'person' (torso + head) the camera can pick out."""
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
    torso = p.createMultiBody(
        baseMass=0, baseVisualShapeIndex=torso_vis, physicsClientId=client
    )
    head = p.createMultiBody(
        baseMass=0, baseVisualShapeIndex=head_vis, physicsClientId=client
    )
    return torso, head


def move_person(ids, x: float, y: float, client: int) -> None:
    torso, head = ids
    p.resetBasePositionAndOrientation(
        torso, [x, y, 0.42], [0, 0, 0, 1], physicsClientId=client
    )
    p.resetBasePositionAndOrientation(
        head, [x, y, 0.87], [0, 0, 0, 1], physicsClientId=client
    )


def detect_person(rgb, dep, near, far):
    """Find the orange person. Returns (found, bearing_deg, elev_deg, distance_m)."""
    bgr = cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (8, 120, 120), (25, 255, 255))  # orange
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return False, 0.0, 0.0, 0.0
    blob = max(contours, key=cv2.contourArea)
    if cv2.contourArea(blob) < 20:
        return False, 0.0, 0.0, 0.0
    m = cv2.moments(blob)
    cx, cy = m["m10"] / m["m00"], m["m01"] / m["m00"]
    half = math.radians(FOV_DEG / 2)
    bearing = math.degrees(math.atan(((2 * cx / IMG_W) - 1) * math.tan(half)))
    elev = math.degrees(math.atan(-((2 * cy / IMG_H) - 1) * math.tan(half)))
    distance = far * near / (far - (far - near) * float(dep[int(cy), int(cx)]))
    return True, bearing, elev, distance


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
    person_x, person_y = (2.5, 0.0)  # gui start; headless overrides via script
    move_person(person, person_x, person_y, env.CLIENT)

    backend = None
    if gui:
        # Reuse Lesson 5's gamepad/keyboard input to drive the person.
        sys.path.insert(
            0, __file__.rsplit("/", 2)[0] + "/05_teleop"  # lessons/05_teleop
        )
        from teleop_xbox import make_input

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
            move_person(person, person_x, person_y, env.CLIENT)

            obs, _, _, _, _ = env.step(action)
            state = obs[0]
            drone_pos, drone_yaw = state[0:3], state[9]

            if i % PERCEPTION_EVERY == 0:
                rgb, dep, _ = env._getDroneImages(0, segmentation=False)
                found, bearing, _elev, dist = detect_person(rgb, dep, near, far)
                if found:
                    # World angle to the person: camera faces drone_yaw, and a
                    # left-of-frame target reads as negative bearing (Lesson 2).
                    theta = drone_yaw - math.radians(bearing)
                    target_yaw = theta  # turn to face the person
                    # Stand off DESIRED_DIST behind them, along the same line.
                    reach = dist - DESIRED_DIST
                    drone_target = np.array(
                        [
                            drone_pos[0] + reach * math.cos(theta),
                            drone_pos[1] + reach * math.sin(theta),
                            FOLLOW_ALT,
                        ]
                    )
                    drone_target[0] = np.clip(drone_target[0], -BOX_XY, BOX_XY)
                    drone_target[1] = np.clip(drone_target[1], -BOX_XY, BOX_XY)
                    if t > 5:  # measure tracking after the drone catches up
                        bearing_errs.append(abs(bearing))

            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=state,
                target_pos=drone_target,
                target_rpy=np.array([0.0, 0.0, target_yaw]),
            )
            if gui:
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
