"""
Lesson 10 (step 2) — train your keyword-spotting model
======================================================
A small CNN learns to classify your recorded MFCC features into commands. Same
"train a small model on your own data" pattern as Lessons 3 and 8 — here the
data is your voice.

  python lessons/10_voice_train/train_kws.py --epochs 40

Output: output/kws_model.pth
"""

import argparse
import copy
import os
import sys

import numpy as np
import torch
import torch.nn as nn

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kws import LABELS, make_net, wav_to_feat  # noqa: E402

DATA = os.path.join(os.path.dirname(__file__), "output", "kws_dataset.npz")
MODEL = os.path.join(os.path.dirname(__file__), "output", "kws_model.pth")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=40)
    ap.add_argument("--batch", type=int, default=16)
    args = ap.parse_args()

    if not os.path.exists(DATA):
        raise SystemExit(f"No dataset at {DATA}. Run record_commands.py first.")

    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[INFO] training on {device}")
    blob = np.load(DATA)
    raw = blob["X"]  # raw int16 waveforms; features computed here
    feats = np.stack([wav_to_feat(raw[i]) for i in range(len(raw))])
    X = torch.tensor(feats).unsqueeze(1)  # (N, 1, frames, mfcc)
    y = torch.tensor(blob["y"]).long()

    n_val = max(len(LABELS), int(0.2 * len(X)))
    perm = torch.randperm(len(X))
    Xtr, ytr = X[perm[n_val:]].to(device), y[perm[n_val:]].to(device)
    Xva, yva = X[perm[:n_val]].to(device), y[perm[:n_val]].to(device)

    net = make_net().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3, weight_decay=1e-4)
    loss_fn = nn.CrossEntropyLoss()
    best_acc, best_state = 0.0, copy.deepcopy(net.state_dict())
    for epoch in range(1, args.epochs + 1):
        net.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), args.batch):
            xb, yb = Xtr[order[i : i + args.batch]], ytr[order[i : i + args.batch]]
            # Light augmentation squeezes more out of a few recordings: add noise
            # and shift in time (roll the MFCC frames a little).
            xb = xb + 0.06 * torch.randn_like(xb)
            xb = torch.roll(xb, shifts=int(torch.randint(-2, 3, (1,))), dims=2)
            opt.zero_grad()
            loss_fn(net(xb), yb).backward()
            opt.step()
        net.eval()
        with torch.no_grad():
            acc = (net(Xva).argmax(1) == yva).float().mean().item()
        if acc >= best_acc:  # keep the best model, not the last epoch's
            best_acc, best_state = acc, copy.deepcopy(net.state_dict())
        if epoch % 10 == 0 or epoch == args.epochs:
            print(f"  epoch {epoch:3d}  val accuracy = {acc * 100:.0f}%")

    torch.save(best_state, MODEL)
    print(f"[INFO] saved best model ({best_acc * 100:.0f}% val) to {MODEL}")


if __name__ == "__main__":
    main()
