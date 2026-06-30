"""
Lesson 17 (step 2) — see what the depth CNN predicts
====================================================
Load the model you trained and look at it: hover in front of some pillars, run
the net on the camera image, and save a side-by-side of RGB | true depth |
predicted depth. The predicted map keys on shape and floor cues from one image —
no depth sensor — which is exactly what the on-board grayscale camera will need.

Run (after train_depth.py):
  python lessons/17_depth/depth_demo.py            # saves output/depth.png
  python lessons/17_depth/depth_demo.py --selftest  # asserts (local)
"""

import os
import sys

import numpy as np
import torch

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from train_depth import (
        IMG_RES,
        MAX_DEPTH,
        MODEL,
        OUT_RES,
        TinyDepthNet,
        abs_rel,
        linearize,
    )
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 17's depth model:", exc)
    sys.exit(1)

OUT_PNG = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "depth.png"
)
PILLARS = [(1.4, -0.6), (1.9, 0.5), (2.4, -0.1)]


def capture():
    import cv2
    import pybullet as p
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0.0, 0.0, 1.0]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    env.IMG_RES = np.array([IMG_RES, IMG_RES])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    for x, y in PILLARS:
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=0.18,
            length=1.4,
            rgbaColor=[0.8, 0.35, 0.25, 1],
            physicsClientId=env.CLIENT,
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[x, y, 0.7],
            physicsClientId=env.CLIENT,
        )
    action = np.zeros((1, 4))
    for _ in range(40):  # hold a steady hover
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=np.array([0.0, 0.0, 1.0]),
        )
    rgb, dep, _ = env._getDroneImages(0, segmentation=False)
    near = env.L
    env.close()
    true_m = np.clip(linearize(dep.astype(np.float32), near, 1000.0), near, MAX_DEPTH)
    true_small = cv2.resize(true_m, (OUT_RES, OUT_RES), interpolation=cv2.INTER_AREA)
    rgb_small = cv2.resize(rgb[:, :, :3], (IMG_RES, IMG_RES)).astype(np.float32) / 255.0
    return rgb_small, true_small


def main() -> None:
    selftest = "--selftest" in sys.argv
    if not os.path.exists(MODEL):
        raise SystemExit(f"No model at {MODEL}. Run train_depth.py first.")
    device = "cpu"
    net = TinyDepthNet().to(device)
    net.load_state_dict(torch.load(MODEL, map_location=device))
    net.eval()

    rgb, true_small = capture()
    with torch.no_grad():
        x = torch.tensor(rgb).permute(2, 0, 1).unsqueeze(0)
        pred = net(x)[0].numpy() * MAX_DEPTH
    rel = abs_rel(pred, true_small)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(1, 3, figsize=(10, 3.4))
    ax[0].imshow(rgb)
    ax[0].set_title("camera (RGB)")
    for a, img, t in (
        (ax[1], true_small, "true depth (sim)"),
        (ax[2], pred, "predicted depth (CNN)"),
    ):
        im = a.imshow(img, cmap="magma_r", vmin=0, vmax=MAX_DEPTH)
        a.set_title(t)
        fig.colorbar(im, ax=a, fraction=0.046, shrink=0.9, label="m")
    for a in ax:
        a.axis("off")
    fig.suptitle(f"Monocular depth — frame AbsRel = {rel:.3f}")
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, dpi=90)
    plt.close(fig)

    print(f"DEPTH-DEMO OK: saved {OUT_PNG}, frame AbsRel={rel:.3f}")
    if selftest:
        assert os.path.exists(OUT_PNG), "no heatmap written"
        assert rel < 0.35, f"prediction far off on this frame (AbsRel {rel:.3f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
