"""
Lesson 3 (Route B) — generate an imitation-learning dataset
===========================================================
Route B trains a neural network to do what Lesson 2's hand-written detector
does: look at the camera image and say which way the obstacle is. But where do
the training *labels* come from? From Lesson 2's detector itself -- it is the
"teacher" (this is imitation / supervised learning).

For each sample we:
  1. Move the red box to a random spot in front of the drone.
  2. Capture the onboard camera image.
  3. Run the HSV detector to get the obstacle's bearing -> that's the label.
  4. Save the (downscaled image, bearing) pair.

Output: output/imitation_dataset.npz  (git-ignored)

Usage:  python gen_dataset.py --samples 500
"""

import argparse
import math
import os
import sys

import cv2
import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics

HOVER_POS = np.array([0.0, 0.0, 1.0])
IMG_W, IMG_H = 160, 160
NET_RES = 64  # the CNN input size (downscaled)
CAMERA_FOV_DEG = 60.0
OUT = os.path.join(os.path.dirname(__file__), "output", "imitation_dataset.npz")


def detect_bearing(rgb: np.ndarray):
    """Lesson 2's detector, reused as the 'teacher'. Returns bearing in degrees
    (or None if the red obstacle isn't visible)."""
    bgr = cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.bitwise_or(
        cv2.inRange(hsv, (0, 120, 80), (10, 255, 255)),
        cv2.inRange(hsv, (170, 120, 80), (180, 255, 255)),
    )
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    blob = max(contours, key=cv2.contourArea)
    if cv2.contourArea(blob) < 30:
        return None
    m = cv2.moments(blob)
    cx = m["m10"] / m["m00"]
    half_fov = math.radians(CAMERA_FOV_DEG / 2)
    norm_x = (2.0 * cx / rgb.shape[1]) - 1.0
    return math.degrees(math.atan(norm_x * math.tan(half_fov)))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--samples", type=int, default=500)
    args = parser.parse_args()

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([HOVER_POS]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    env.IMG_RES = np.array([IMG_W, IMG_H])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)

    # One red box we reposition each sample.
    half = [0.18, 0.18, 0.18]
    col = p.createCollisionShape(
        p.GEOM_BOX, halfExtents=half, physicsClientId=env.CLIENT
    )
    vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=half, rgbaColor=[1, 0, 0, 1], physicsClientId=env.CLIENT
    )
    box = p.createMultiBody(
        baseMass=0,
        baseCollisionShapeIndex=col,
        baseVisualShapeIndex=vis,
        basePosition=[1.5, 0, 1.0],
        physicsClientId=env.CLIENT,
    )

    rng = np.random.default_rng(0)
    images, labels = [], []
    action = np.zeros((1, 4))
    attempts = 0
    while len(images) < args.samples and attempts < args.samples * 4:
        attempts += 1
        # Random obstacle pose in front of the (forward-facing) camera.
        ox = float(rng.uniform(1.0, 2.2))
        oy = float(rng.uniform(-0.7, 0.7))
        p.resetBasePositionAndOrientation(
            box, [ox, oy, 1.0], [0, 0, 0, 1], physicsClientId=env.CLIENT
        )
        # Hold a steady hover for a few steps so the capture is clean.
        for _ in range(6):
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=HOVER_POS
            )
        rgb, _dep, _seg = env._getDroneImages(0, segmentation=False)
        bearing = detect_bearing(rgb)
        if bearing is None:
            continue  # obstacle drifted out of view -> skip
        small = cv2.resize(rgb[:, :, :3].astype(np.uint8), (NET_RES, NET_RES))
        images.append(small.astype(np.float32) / 255.0)
        labels.append(bearing)
        if len(images) % 100 == 0:
            print(f"  collected {len(images)}/{args.samples}")

    env.close()
    X = np.array(images, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, X=X, y=y)
    print(
        f"Saved {len(y)} samples to {OUT}  "
        f"(image {X.shape[1:]}; bearing range "
        f"{y.min():.1f}..{y.max():.1f} deg)"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
