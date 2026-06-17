"""
Lesson 6 — Follow-me tracking
=============================
The drone follows a moving target using only its camera — a closed visual loop
that ties together Lesson 1 (control), Lesson 2 (perception), and a simple
"decide" rule. This is *visual servoing*: see the target, work out where it is,
move to keep it centred and a fixed distance ahead.

Each perception tick we:
  1. detect the bright-green target (HSV, like Lesson 2) -> bearing + elevation,
  2. read its distance from the depth image,
  3. reconstruct the target's world position from the drone's pose,
  4. set the drone's target to a standoff point DESIRED_DIST behind it.

The PID flight controller (Lesson 1's layer) then chases that target, so the
drone trails the object, keeping it centred in view.

Run:  python lessons/06_follow_me/follow_me.py
      python lessons/06_follow_me/follow_me.py --headless   # no window (CI)
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
DESIRED_DIST = 1.0  # how far behind the target the drone tries to stay (m)
IMG_W, IMG_H = 160, 160
FOV_DEG = 60.0  # matches BaseAviary._getDroneImages
PERCEPTION_EVERY = 6  # run the camera every N control steps (perception is slow)
BOX_XY, BOX_Z = 2.5, (0.3, 2.5)


def target_position(t: float) -> list:
    """Scripted motion of the green target: a lateral sweep that stays in view."""
    return [1.5 + 0.15 * math.sin(0.7 * t), 0.5 * math.sin(0.5 * t), 1.0]


def detect_target(rgb, dep, near, far):
    """Find the green target. Returns (found, bearing_deg, elev_deg, distance_m)."""
    bgr = cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (40, 80, 60), (85, 255, 255))  # green
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
    depth = dep[int(cy), int(cx)]
    distance = far * near / (far - (far - near) * float(depth))
    return True, bearing, elev, distance


def target_world_from_detection(drone_pos, bearing_deg, elev_deg, distance):
    """Reconstruct the target's world position (drone faces +x, yaw fixed at 0).

    Lesson 2 established: world +y appears LEFT of frame -> negative bearing,
    so the world y-offset is -d*sin(bearing)."""
    b, e = math.radians(bearing_deg), math.radians(elev_deg)
    return np.array(
        [
            drone_pos[0] + distance * math.cos(b),
            drone_pos[1] - distance * math.sin(b),
            drone_pos[2] + distance * math.sin(e),
        ]
    )


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
                found, bearing, elev, dist = detect_target(rgb, dep, near, far)
                if found:
                    tgt = target_world_from_detection(drone_pos, bearing, elev, dist)
                    # Standoff: trail DESIRED_DIST behind in x, match y and z.
                    drone_target = np.array([tgt[0] - DESIRED_DIST, tgt[1], tgt[2]])
                    drone_target[0] = np.clip(drone_target[0], -BOX_XY, BOX_XY)
                    drone_target[1] = np.clip(drone_target[1], -BOX_XY, BOX_XY)
                    drone_target[2] = np.clip(drone_target[2], BOX_Z[0], BOX_Z[1])
                    if t > 4:  # measure tracking after the initial catch-up
                        bearing_errs.append(abs(bearing))

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
