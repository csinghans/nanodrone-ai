"""
Lesson 8 — Follow a "real" person with a learned detector
=========================================================
Lesson 7 followed a bright-orange marker with a colour rule. Here the target is
a realistic multi-colour person that a colour threshold can't pin down, so the
"which way is the person?" question is answered by the **trained CNN** from
train_person_cnn.py instead. Range still comes from the depth sensor (no need to
learn metric distance), and the yaw-follow loop is reused from Lesson 7.

So this is the first capability in the course that needs *training* before it
works:
  python lessons/08_follow_real/gen_person_dataset.py     # 1. make data
  python lessons/08_follow_real/train_person_cnn.py       # 2. train the detector
  python lessons/08_follow_real/follow_real.py            # 3. fly (you drive)
  python lessons/08_follow_real/follow_real.py --headless # scripted demo / verify
"""

import math
import os
import sys
import time

import numpy as np
import pybullet as p
import torch
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

from nanodrone import chase_cam, linearize_depth, make_input, setup_view, world_point

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from person import build_person, move_person, true_bearing_deg  # noqa: E402
from train_person_cnn import BEARING_SCALE, MODEL, PersonCNN  # noqa: E402

START = np.array([0.0, 0.0, 1.0])
DESIRED_DIST = 1.4
FOLLOW_ALT = 1.0
PERSON_SPEED = 0.8
IMG_W, IMG_H = 160, 160
NET_RES = 64
FOV_DEG = 60.0
PERCEPTION_EVERY = 6
BOX_XY = 3.0
MAX_RANGE = 4.0  # depth beyond this means we saw background, not the person


def cnn_bearing(model, device, rgb) -> float:
    """Run the trained detector on a camera frame -> person bearing (degrees)."""
    import cv2

    small = cv2.resize(rgb[:, :, :3].astype(np.uint8), (NET_RES, NET_RES))
    t = torch.tensor(small.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        return float(model(t.to(device)).item()) * BEARING_SCALE


def depth_at_bearing(dep, bearing_deg: float, near: float, far: float) -> float:
    """Range from the depth sensor in a small patch at the image column for
    `bearing_deg`. A patch (not one pixel) avoids slipping past the thin person
    and reading the floor behind them. Returns the closest surface."""
    half = math.radians(FOV_DEG / 2)
    cx = int(((math.tan(math.radians(bearing_deg)) / math.tan(half)) + 1) / 2 * IMG_W)
    cx = max(0, min(IMG_W - 1, cx))
    c0, c1 = max(0, cx - 2), min(IMG_W, cx + 3)
    patch = dep[int(0.3 * IMG_H) : int(0.8 * IMG_H), c0:c1]  # person body rows
    return linearize_depth(float(np.min(patch)), near, far)


def scripted_person_xy(t: float):
    return 1.6 + 0.9 * math.cos(0.3 * t), 0.9 * math.sin(0.3 * t)


def main(gui: bool = True) -> None:
    if not os.path.exists(MODEL):
        print(f"No trained detector at {MODEL}.")
        print("Train it first:\n  python lessons/08_follow_real/gen_person_dataset.py")
        print("  python lessons/08_follow_real/train_person_cnn.py")
        return

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = PersonCNN().to(device)
    model.load_state_dict(torch.load(MODEL, map_location=device))
    model.eval()

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
    px, py, heading = 2.6, 0.0, math.pi
    move_person(person, px, py, heading, env.CLIENT)

    backend = None
    if gui:
        setup_view(env.CLIENT)
        backend, _ = make_input("xbox")
        print("Drive the person; the drone follows with its learned detector.")

    drone_target = START.copy()
    target_yaw = 0.0
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    duration = 16 * env.CTRL_FREQ if not gui else 10**9
    track_errs = []

    i = 0
    try:
        while i < duration:
            t = i * dt
            prev = (px, py)
            if gui:
                fwd, strafe, _u, _y = backend.read()
                px = float(np.clip(px + fwd * PERSON_SPEED * dt, -BOX_XY, BOX_XY))
                py = float(np.clip(py + strafe * PERSON_SPEED * dt, -BOX_XY, BOX_XY))
            else:
                px, py = scripted_person_xy(t)
            if (px - prev[0]) ** 2 + (py - prev[1]) ** 2 > 1e-8:
                heading = math.atan2(py - prev[1], px - prev[0])
            move_person(person, px, py, heading, env.CLIENT)

            obs, _, _, _, _ = env.step(action)
            state = obs[0]
            drone_pos, drone_yaw = state[0:3], state[9]

            if i % PERCEPTION_EVERY == 0:
                rgb, dep, _ = env._getDroneImages(0, segmentation=False)
                bearing = cnn_bearing(model, device, rgb)  # learned "which way"
                dist = depth_at_bearing(dep, bearing, near, far)  # sensed range
                if dist <= MAX_RANGE:  # ignore frames where we lost the range
                    _wx, _wy, theta = world_point(drone_pos, drone_yaw, bearing, dist)
                    target_yaw = theta
                    reach = float(
                        np.clip(dist - DESIRED_DIST, -0.5, 0.5)
                    )  # gentle step
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
                    if t > 6:  # true tracking error (independent of the CNN)
                        track_errs.append(
                            abs(true_bearing_deg(drone_pos, drone_yaw, px, py))
                        )

            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=state,
                target_pos=drone_target,
                target_rpy=np.array([0.0, 0.0, target_yaw]),
            )
            if gui:
                chase_cam(env.CLIENT, drone_pos)
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
        mean_err = float(np.mean(track_errs)) if track_errs else 99.0
        print(
            f"FOLLOW OK (CNN): tracked {len(track_errs)} frames, "
            f"mean true bearing error {mean_err:.1f} deg."
        )
        assert mean_err < 18.0, f"drone lost the person ({mean_err:.1f} deg)"


if __name__ == "__main__":
    main(gui="--headless" not in sys.argv)
    sys.exit(0)
