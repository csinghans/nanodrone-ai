"""
Lesson 17 (step 1) — train a monocular depth-estimation CNN
===========================================================
Until now depth was only ever read at a single point (range to one target). But
the real AI-deck has a *grayscale camera and no depth sensor* — so to avoid
obstacles on-board you must **guess depth from a single image**. That's the
course's signature move again (Lesson 3/8/13): when there's no rule, train a
small model. And the labels are free — the simulator hands us a full depth image,
the "privileged teacher".

This trains a tiny encoder-decoder: image -> a small dense depth map. The encoder
is Lesson 3's TinyDronet conv stack; the decoder upsamples back to a depth grid.

Run:
  python lessons/17_depth/train_depth.py --samples 240 --epochs 60
  python lessons/17_depth/train_depth.py --selftest    # tiny run, asserts (local)
Saves output/depth_cnn.pth (git-ignored).
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn

IMG_RES = 64  # camera + network input
OUT_RES = 16  # predicted depth grid
MAX_DEPTH = 5.0  # clip metres (the horizon / empty sky is "far", not infinite)
GAP8_BUDGET_KB = 512
MODEL = os.path.join(os.path.dirname(__file__), "output", "depth_cnn.pth")


class TinyDepthNet(nn.Module):
    """Encoder (Lesson 3's TinyDronet conv stack, kept spatial) -> a small
    upsampling decoder -> a OUT_RES x OUT_RES depth map in [0, 1] (of MAX_DEPTH)."""

    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(3, 16, 5, stride=2, padding=2),
            nn.ReLU(),  # 64 -> 32
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),  # 32 -> 16
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.ReLU(),  # 16 -> 8
        )
        self.dec = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),  # 8->16
            nn.Conv2d(64, 16, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 1, 3, padding=1),
            nn.Sigmoid(),  # depth in [0, 1] of MAX_DEPTH
        )

    def forward(self, x):
        return self.dec(self.enc(x)).squeeze(1)  # (B, OUT_RES, OUT_RES)


def linearize(depth_buffer, near, far):
    return far * near / (far - (far - near) * depth_buffer)


def gen_dataset(n_samples: int, seed: int = 0):
    """Hover and snap (image, dense depth) with random pillars for structure."""
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
    near, far = env.L, 1000.0
    # a few movable pillars, re-placed each sample for varied depth maps
    pillars = []
    for _ in range(3):
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=0.18,
            length=1.4,
            rgbaColor=[0.8, 0.35, 0.25, 1],
            physicsClientId=env.CLIENT,
        )
        pillars.append(
            p.createMultiBody(
                baseMass=0, baseVisualShapeIndex=vis, physicsClientId=env.CLIENT
            )
        )
    rng = np.random.default_rng(seed)
    action = np.zeros((1, 4))
    images, depths = [], []
    while len(images) < n_samples:
        for body in pillars:
            px, py = float(rng.uniform(0.7, 2.6)), float(rng.uniform(-1.4, 1.4))
            p.resetBasePositionAndOrientation(
                body, [px, py, 0.7], [0, 0, 0, 1], physicsClientId=env.CLIENT
            )
        for _ in range(4):  # settle a clean hover
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=env.CTRL_TIMESTEP,
                state=obs[0],
                target_pos=np.array([0.0, 0.0, 1.0]),
            )
        rgb, dep, _ = env._getDroneImages(0, segmentation=False)
        metres = np.clip(linearize(dep.astype(np.float32), near, far), near, MAX_DEPTH)
        small = cv2.resize(metres, (OUT_RES, OUT_RES), interpolation=cv2.INTER_AREA)
        images.append(
            cv2.resize(rgb[:, :, :3], (IMG_RES, IMG_RES)).astype(np.float32) / 255.0
        )
        depths.append(small)
    env.close()
    return np.array(images, dtype=np.float32), np.array(depths, dtype=np.float32)


def abs_rel(pred_m, true_m) -> float:
    return float((np.abs(pred_m - true_m) / true_m).mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=240)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n, e = (160, 50) if args.selftest else (args.samples, args.epochs)

    print(f"[INFO] generating {n} samples ...")
    X, D = gen_dataset(n)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    Xt = torch.tensor(X).permute(0, 3, 1, 2)
    yt = torch.tensor(D / MAX_DEPTH)  # normalized target in [0, 1]
    n_val = max(4, int(0.2 * len(Xt)))
    perm = torch.randperm(len(Xt))
    Xtr, ytr = Xt[perm[n_val:]].to(device), yt[perm[n_val:]].to(device)
    Xva, yva = Xt[perm[:n_val]].to(device), yt[perm[:n_val]].to(device)

    net = TinyDepthNet().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.L1Loss()
    rel = 1.0
    for epoch in range(1, e + 1):
        net.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 32):
            b = order[i : i + 32]
            opt.zero_grad()
            loss_fn(net(Xtr[b]), ytr[b]).backward()
            opt.step()
        if epoch % 10 == 0 or epoch == e:
            net.eval()
            with torch.no_grad():
                pred = net(Xva).cpu().numpy() * MAX_DEPTH
            rel = abs_rel(pred, yva.cpu().numpy() * MAX_DEPTH)
            print(f"  epoch {epoch:3d}  val AbsRel = {rel:.3f}")

    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    n_params = sum(p.numel() for p in net.parameters())
    int8_kb = n_params / 1024
    print(
        f"DEPTH OK: trained {len(D)} samples, val AbsRel={rel:.3f}, "
        f"int8 footprint={int8_kb:.1f} KB (<{GAP8_BUDGET_KB} fits), saved {MODEL}"
    )
    if args.selftest:
        assert rel < 0.25, f"depth model too inaccurate (AbsRel {rel:.3f})"
        assert int8_kb < GAP8_BUDGET_KB, f"too big for GAP8 ({int8_kb:.1f} KB)"


if __name__ == "__main__":
    main()
    sys.exit(0)
