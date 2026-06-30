"""
Lesson 13 (step 1) — train a "person vs background" confirm classifier
======================================================================
Lesson 8's detector always answers "which way is the person?" — even when there
is no person, it points at *something* (a floor seam, a wall). For a mission that
must decide *whether to start following*, that is dangerous: it would chase
background. So we train one more tiny model — the course's signature move — a
binary classifier that says **is a person actually in view?** It gates the
Search -> Follow transition in mission.py.

Labels are free from the simulator (we know where the person is):
  * label 1 — person dropped in the forward view
  * label 0 — person behind / far away, so the view is empty floor (background)

Run:
  python lessons/13_find_follow_land/train_confirm.py --samples 400 --epochs 40
  python lessons/13_find_follow_land/train_confirm.py --selftest   # tiny run (CI)
Saves output/confirm_cnn.pth (git-ignored).
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn

_P8 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "08_follow_real"
)
sys.path.insert(0, _P8)
from person import build_person, move_person, true_bearing_deg  # noqa: E402

HOVER = np.array([0.0, 0.0, 1.0])
IMG_W, IMG_H = 160, 160
NET_RES = 64
FOV_DEG = 60.0
MODEL = os.path.join(os.path.dirname(__file__), "output", "confirm_cnn.pth")


class ConfirmCNN(nn.Module):
    """Tiny binary classifier: image -> logit (person in view?). Same backbone as
    Lesson 8's PersonCNN, a 2-class head instead of a bearing regressor."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.AdaptiveMaxPool2d(1),  # max, not avg: a person anywhere lights up
        )
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.head(self.features(x)).squeeze(-1)


def confirm_prob(net, device, rgb) -> float:
    """P(person in view) for a camera frame, in [0, 1]."""
    import cv2

    small = cv2.resize(rgb[:, :, :3].astype(np.uint8), (NET_RES, NET_RES))
    t = torch.tensor(small.astype(np.float32) / 255.0).permute(2, 0, 1).unsqueeze(0)
    with torch.no_grad():
        return float(torch.sigmoid(net(t.to(device))).item())


def gen_dataset(n_samples: int, seed: int = 0):
    """Capture camera frames with the person in view (1) or away (0)."""
    import cv2
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

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
    rng = np.random.default_rng(seed)
    action = np.zeros((1, 4))
    images, labels = [], []
    while len(images) < n_samples:
        present = len(images) % 2 == 0  # balanced classes
        if present:
            px = float(rng.uniform(1.0, 2.4))  # in front, sizeable in view
            py = float(rng.uniform(-1.0, 1.0))
        else:  # behind the drone -> forward camera sees empty floor (background)
            px = float(rng.uniform(-3.0, -1.0))
            py = float(rng.uniform(-1.5, 1.5))
        move_person(person, px, py, float(rng.uniform(-np.pi, np.pi)), env.CLIENT)
        for _ in range(5):  # settle into a clean hover
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=HOVER
            )
        drone_pos = obs[0][0:3]
        if (
            present
            and abs(true_bearing_deg(drone_pos, obs[0][9], px, py)) > FOV_DEG / 2
        ):
            continue  # claimed "present" but actually out of view -> skip
        rgb, _dep, _ = env._getDroneImages(0, segmentation=False)
        small = cv2.resize(rgb[:, :, :3].astype(np.uint8), (NET_RES, NET_RES))
        images.append(small.astype(np.float32) / 255.0)
        labels.append(1.0 if present else 0.0)
    env.close()
    return np.array(images, dtype=np.float32), np.array(labels, dtype=np.float32)


def train(X, y, epochs: int, batch: int = 32) -> float:
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    Xt = torch.tensor(X).permute(0, 3, 1, 2)
    yt = torch.tensor(y)
    n_val = max(2, int(0.2 * len(Xt)))
    perm = torch.randperm(len(Xt))
    Xtr, ytr = Xt[perm[n_val:]].to(device), yt[perm[n_val:]].to(device)
    Xva, yva = Xt[perm[:n_val]].to(device), yt[perm[:n_val]].to(device)

    net = ConfirmCNN().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.BCEWithLogitsLoss()
    acc = 0.0
    for epoch in range(1, epochs + 1):
        net.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), batch):
            b = order[i : i + batch]
            opt.zero_grad()
            loss_fn(net(Xtr[b]), ytr[b]).backward()
            opt.step()
        if epoch % 10 == 0 or epoch == epochs:
            net.eval()
            with torch.no_grad():
                pred = (torch.sigmoid(net(Xva)) > 0.5).float()
                acc = (pred == yva).float().mean().item()
            print(f"  epoch {epoch:3d}  val acc = {acc:.2f}")
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    return acc


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=400)
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--selftest", action="store_true", help="tiny run for CI")
    args = ap.parse_args()

    n, e = (160, 45) if args.selftest else (args.samples, args.epochs)
    print(f"[INFO] generating {n} samples ...")
    X, y = gen_dataset(n)
    acc = train(X, y, epochs=e)
    print(f"CONFIRM-CNN OK: trained {len(y)} samples, val acc={acc:.2f}, saved {MODEL}")
    if args.selftest:
        assert acc > 0.9, f"confirm classifier did not learn (val acc {acc:.2f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
