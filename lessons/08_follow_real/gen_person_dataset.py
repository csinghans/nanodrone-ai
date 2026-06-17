"""
Lesson 8 (step 1) — generate a person-detection dataset
=======================================================
We can't write a colour rule for a realistic person, so we teach a CNN instead.
The labels come from the simulator's ground truth: we know exactly where the
person is, so the true bearing is free. (No hand detector needed — this is a
"privileged teacher".)

For each sample: drop the person at a random spot in front of the hovering
drone, capture the camera image, and save (image, true_bearing).

Output: output/person_dataset.npz   (git-ignored)
Usage:  python lessons/08_follow_real/gen_person_dataset.py --samples 600
"""

import argparse
import os
import sys

import cv2
import numpy as np
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from person import build_person, move_person, true_bearing_deg  # noqa: E402

HOVER = np.array([0.0, 0.0, 1.0])
IMG_W, IMG_H = 160, 160
NET_RES = 64
OUT = os.path.join(os.path.dirname(__file__), "output", "person_dataset.npz")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=600)
    args = ap.parse_args()

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([HOVER]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    env.IMG_RES = np.array([IMG_W, IMG_H])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    person = build_person(env.CLIENT)

    rng = np.random.default_rng(0)
    action = np.zeros((1, 4))
    images, labels = [], []
    while len(images) < args.samples:
        px = float(rng.uniform(1.0, 2.6))
        py = float(rng.uniform(-1.0, 1.0))
        heading = float(rng.uniform(-np.pi, np.pi))
        move_person(person, px, py, heading, env.CLIENT)
        for _ in range(5):  # hold a steady hover so the capture is clean
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=HOVER
            )
        drone_pos = obs[0][0:3]
        rgb, _dep, _ = env._getDroneImages(0, segmentation=False)
        bearing = true_bearing_deg(drone_pos, obs[0][9], px, py)
        if abs(bearing) > 32:  # person out of the ~60 deg view -> skip
            continue
        small = cv2.resize(rgb[:, :, :3].astype(np.uint8), (NET_RES, NET_RES))
        images.append(small.astype(np.float32) / 255.0)
        labels.append(bearing)
        if len(images) % 150 == 0:
            print(f"  collected {len(images)}/{args.samples}")

    env.close()
    X = np.array(images, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, X=X, y=y)
    print(f"Saved {len(y)} samples to {OUT} (bearing {y.min():.0f}..{y.max():.0f} deg)")


if __name__ == "__main__":
    main()
    sys.exit(0)
