"""
Lesson 18 (step 1) — learn visual odometry from optical flow
============================================================
Every flight loop so far read the simulator's *privileged* position
(`obs[0][0:3]`). The real drone has no such oracle indoors — to know it moved, it
must read its own camera: how the floor texture *flows* between two frames tells
you the motion. This trains a tiny CNN on a pair of stacked frames -> body
displacement (dx, dy, dyaw). Labels are free from the sim's true poses.

It's the same "train your own small model" move, on a new modality (motion), and
it's what an offline indoor drone needs for state estimation (a Flow deck does
this in hardware; here we learn it).

Run:
  python lessons/18_flow/train_flow.py --samples 320 --epochs 60
  python lessons/18_flow/train_flow.py --selftest    # tiny run, asserts (local)
Saves output/flow_net.pth (git-ignored).
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn

RES = 48  # grayscale frame size fed to the net
WIN = 8  # frames between the two snapshots
DISP_SCALE = np.array([0.25, 0.25, 0.4], dtype=np.float32)  # normalize (m, m, rad)
GAP8_BUDGET_KB = 512
MODEL = os.path.join(os.path.dirname(__file__), "output", "flow_net.pth")


class FlowNet(nn.Module):
    """Two stacked grayscale frames -> (dx, dy, dyaw). Same conv spirit as the
    other tiny nets; 2 input channels (before + after)."""

    def __init__(self):
        super().__init__()
        # NB: NO global pooling — flow is about *where* texture moved, so the
        # spatial layout of features must reach the head (avg-pooling it away
        # makes both frames look identical and the net can only predict the mean).
        self.features = nn.Sequential(
            nn.Conv2d(2, 16, 5, stride=2, padding=2),
            nn.ReLU(),  # 48 -> 24
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),  # 24 -> 12
            nn.Conv2d(32, 32, 3, stride=2, padding=1),
            nn.ReLU(),  # 12 -> 6
        )
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(32 * 6 * 6, 64), nn.ReLU(), nn.Linear(64, 3)
        )

    def forward(self, x):
        return self.head(self.features(x))


def _scatter_floor(client, rng, n=70):
    """Scatter small coloured tiles on the floor so the downward camera has
    texture to track. (The bare plane renders featureless.)"""
    import pybullet as p

    for _ in range(n):
        x, y = float(rng.uniform(-3, 3)), float(rng.uniform(-3, 3))
        col = [
            float(rng.uniform(0.1, 1)),
            float(rng.uniform(0.1, 1)),
            float(rng.uniform(0.1, 1)),
            1,
        ]
        vis = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=[0.09, 0.09, 0.01],
            rgbaColor=col,
            physicsClientId=client,
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[x, y, 0.02],
            physicsClientId=client,
        )


def down_view(client, pos, yaw):
    """A grayscale DOWNWARD camera over the textured floor — the geometry a real
    optical-flow deck uses, because a forward view has almost no translational
    flow. The up-vector rotates with yaw so turns are visible too."""
    import math

    import pybullet as p

    eye = [float(pos[0]), float(pos[1]), float(pos[2])]
    tgt = [eye[0], eye[1], eye[2] - 1.0]
    up = [math.cos(yaw), math.sin(yaw), 0.0]
    view = p.computeViewMatrix(eye, tgt, up, physicsClientId=client)
    proj = p.computeProjectionMatrixFOV(70.0, 1.0, 0.05, 5.0, physicsClientId=client)
    _, _, rgb, _, _ = p.getCameraImage(
        RES, RES, view, proj, renderer=p.ER_TINY_RENDERER, physicsClientId=client
    )
    arr = np.reshape(np.array(rgb, dtype=np.uint8), (RES, RES, 4))[:, :, :3].astype(
        np.float32
    )
    return (0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]) / 255.0


def gen_dataset(n_samples: int, seed: int = 0):
    """Hover, snap a frame, drift a random small velocity for WIN frames, snap
    again; the label is the true (dx, dy, dyaw) the drone actually moved."""
    import math

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
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    dt = env.CTRL_TIMESTEP
    rng = np.random.default_rng(seed)
    _scatter_floor(env.CLIENT, rng)  # texture for the downward camera to flow on
    action = np.zeros((1, 4))
    target = np.array([0.0, 0.0, 1.0])
    yaw = 0.0
    pairs, labels = [], []

    def settle(steps):
        nonlocal action
        obs = None
        for _ in range(steps):
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=obs[0],
                target_pos=target,
                target_rpy=np.array([0.0, 0.0, yaw]),
            )
        return obs

    obs = settle(20)
    while len(pairs) < n_samples:
        p0 = obs[0][0:3].copy()
        yaw0 = float(obs[0][9])
        g0 = down_view(env.CLIENT, p0, yaw0)
        # pick a random body velocity and drift for WIN frames
        vx, vy = rng.uniform(-0.8, 0.8), rng.uniform(-0.8, 0.8)
        vyaw = rng.uniform(-1.0, 1.0)
        for _ in range(WIN):
            yaw += vyaw * dt
            c, s = math.cos(yaw), math.sin(yaw)
            target[0] += (vx * c - vy * s) * dt
            target[1] += (vx * s + vy * c) * dt
            target[0] = float(np.clip(target[0], -2.5, 2.5))
            target[1] = float(np.clip(target[1], -2.5, 2.5))
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=obs[0],
                target_pos=target,
                target_rpy=np.array([0.0, 0.0, yaw]),
            )
        p1 = obs[0][0:3].copy()
        yaw1 = float(obs[0][9])
        g1 = down_view(env.CLIENT, p1, yaw1)
        # express the world displacement in the body frame at the start
        dwx, dwy = p1[0] - p0[0], p1[1] - p0[1]
        c0, s0 = math.cos(-yaw0), math.sin(-yaw0)
        dx = dwx * c0 - dwy * s0
        dy = dwx * s0 + dwy * c0
        dyaw = math.atan2(math.sin(yaw1 - yaw0), math.cos(yaw1 - yaw0))
        pairs.append(np.stack([g0, g1], axis=0))
        labels.append([dx, dy, dyaw])
    env.close()
    return np.array(pairs, dtype=np.float32), np.array(labels, dtype=np.float32)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=320)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n, e = (220, 60) if args.selftest else (args.samples, args.epochs)

    print(f"[INFO] generating {n} frame pairs ...")
    X, Y = gen_dataset(n)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    Xt = torch.tensor(X)
    scale = torch.tensor(DISP_SCALE)
    Yt = torch.tensor(Y) / scale  # normalized targets ~[-1, 1]
    n_val = max(4, int(0.2 * len(Xt)))
    perm = torch.randperm(len(Xt))
    Xtr, Ytr = Xt[perm[n_val:]].to(device), Yt[perm[n_val:]].to(device)
    Xva, Yva = Xt[perm[:n_val]].to(device), Yt[perm[:n_val]].to(device)

    net = FlowNet().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    vel_mae = 1.0
    for epoch in range(1, e + 1):
        net.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 32):
            b = order[i : i + 32]
            opt.zero_grad()
            loss_fn(net(Xtr[b]), Ytr[b]).backward()
            opt.step()
        if epoch % 10 == 0 or epoch == e:
            net.eval()
            with torch.no_grad():
                pred = net(Xva).cpu().numpy() * DISP_SCALE
            true = Yva.cpu().numpy() * DISP_SCALE
            # MAE on the translation (dx, dy), converted to m/s
            vel_mae = float(np.abs(pred[:, :2] - true[:, :2]).mean() / (WIN / 48.0))
            print(f"  epoch {epoch:3d}  translation vel MAE = {vel_mae:.3f} m/s")

    # baseline: predicting the training-mean displacement (learns nothing)
    base = Ytr.cpu().numpy().mean(axis=0) * DISP_SCALE
    base_mae = float(np.abs(base[:2] - true[:, :2]).mean() / (WIN / 48.0))

    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    int8_kb = sum(p.numel() for p in net.parameters()) / 1024
    print(
        f"FLOW OK: {len(Y)} pairs, vel MAE={vel_mae:.3f} m/s "
        f"(vs {base_mae:.3f} predict-mean baseline), "
        f"int8 footprint={int8_kb:.1f} KB (<{GAP8_BUDGET_KB} fits), saved {MODEL}"
    )
    if args.selftest:
        # the net must clearly beat the naive baseline — i.e. it learned flow,
        # not the mean. (A forward camera is a hard case; a downward Flow deck
        # would do far better — see the README.)
        assert (
            vel_mae < 0.8 * base_mae
        ), f"flow net no better than predict-mean ({vel_mae:.3f} vs {base_mae:.3f})"
        assert int8_kb < GAP8_BUDGET_KB, f"too big for GAP8 ({int8_kb:.1f} KB)"


if __name__ == "__main__":
    main()
    sys.exit(0)
