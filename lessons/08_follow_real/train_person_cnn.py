"""
Lesson 8 (step 2) — train the person-detection CNN
==================================================
A small CNN learns to look at the camera image and say which way the person is
(their bearing), from the ground-truth-labelled dataset. This is the learned
replacement for Lesson 2's colour threshold — it keys on the person's shape and
appearance, not one bright colour.

Run gen_person_dataset.py first, then:
  python lessons/08_follow_real/train_person_cnn.py --epochs 120
Saves output/person_cnn.pth (git-ignored).
"""

import argparse
import os

import numpy as np
import torch
import torch.nn as nn

DATA = os.path.join(os.path.dirname(__file__), "output", "person_dataset.npz")
MODEL = os.path.join(os.path.dirname(__file__), "output", "person_cnn.pth")
BEARING_SCALE = 32.0  # labels are within ~+/-32 deg; scale to ~[-1, 1]


class PersonCNN(nn.Module):
    """Compact CNN: image -> bearing. Same spirit as Lesson 3's TinyDronet."""

    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 16, 5, stride=2, padding=2),
            nn.ReLU(),  # 64 -> 32
            nn.Conv2d(16, 32, 3, stride=2, padding=1),
            nn.ReLU(),  # 32 -> 16
            nn.Conv2d(32, 64, 3, stride=2, padding=1),
            nn.ReLU(),  # 16 -> 8
            nn.AdaptiveAvgPool2d(1),
        )
        self.head = nn.Sequential(
            nn.Flatten(), nn.Linear(64, 32), nn.ReLU(), nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.head(self.features(x)).squeeze(-1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    if not os.path.exists(DATA):
        raise SystemExit(f"No dataset at {DATA}. Run gen_person_dataset.py first.")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[INFO] training on {device}")
    blob = np.load(DATA)
    X = torch.tensor(blob["X"]).permute(0, 3, 1, 2)
    y = torch.tensor(blob["y"]) / BEARING_SCALE

    n_val = max(1, int(0.2 * len(X)))
    perm = torch.randperm(len(X))
    Xtr, ytr = X[perm[n_val:]].to(device), y[perm[n_val:]].to(device)
    Xva, yva = X[perm[:n_val]].to(device), y[perm[:n_val]].to(device)

    model = PersonCNN().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), args.batch):
            b = order[i : i + args.batch]
            opt.zero_grad()
            loss_fn(model(Xtr[b]), ytr[b]).backward()
            opt.step()
        if epoch % 20 == 0 or epoch == args.epochs:
            model.eval()
            with torch.no_grad():
                mae = (model(Xva) - yva).abs().mean().item() * BEARING_SCALE
            print(f"  epoch {epoch:3d}  val MAE = {mae:.2f} deg")

    torch.save(model.state_dict(), MODEL)
    print(f"[INFO] saved model to {MODEL}")


if __name__ == "__main__":
    main()
