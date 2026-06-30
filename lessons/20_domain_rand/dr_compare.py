"""
Lesson 20 — domain randomization: shrink the sim-to-real gap
============================================================
Lesson 17's depth CNN learned on clean sim renders — and on a different
appearance (a dimmer, noisier "camera" it never saw) it falls apart. The fix
isn't a fancier renderer; it's **domain randomization**: jitter the training
images so the model can't rely on exact pixels and learns robust cues instead.

This trains two depth CNNs on the same scene data — one on clean images
(baseline), one on randomized images (DR) — and scores both on a fixed
appearance-shifted test set. The DR model should be clearly more robust. That's
the principled answer to the honest gap Lessons 14b/17/18 keep flagging.

Run (depends on Lesson 17's network):
  python lessons/20_domain_rand/dr_compare.py
  python lessons/20_domain_rand/dr_compare.py --selftest   # tiny run, asserts (local)
"""

import os
import sys

import numpy as np
import torch
import torch.nn as nn

try:
    _L17 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "17_depth"
    )
    sys.path.insert(0, _L17)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from randomize import jitter, shift_appearance
    from train_depth import MAX_DEPTH, TinyDepthNet, abs_rel, gen_dataset
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 20 dependencies:", exc)
    sys.exit(1)


def train(X, D, epochs, device, rng=None):
    """Train a TinyDepthNet; if rng is given, randomize images each batch (DR)."""
    net = TinyDepthNet().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.L1Loss()
    y = torch.tensor(D / MAX_DEPTH).to(device)
    for _ in range(epochs):
        net.train()
        order = torch.randperm(len(X))
        for i in range(0, len(X), 32):
            b = order[i : i + 32].numpy()
            xb = jitter(X[b], rng) if rng is not None else X[b]
            xt = torch.tensor(xb).permute(0, 3, 1, 2).to(device)
            opt.zero_grad()
            loss_fn(net(xt), y[torch.tensor(b)]).backward()
            opt.step()
    net.eval()
    return net


def evaluate(net, X, D, device) -> float:
    with torch.no_grad():
        xt = torch.tensor(X).permute(0, 3, 1, 2).to(device)
        pred = net(xt).cpu().numpy() * MAX_DEPTH
    return abs_rel(pred, D)


def main() -> None:
    selftest = "--selftest" in sys.argv
    n, e = (180, 40) if selftest else (320, 60)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    rng = np.random.default_rng(0)

    print(f"[INFO] generating {n} samples ...")
    X, D = gen_dataset(n)
    n_val = max(8, int(0.25 * len(X)))
    Xtr, Dtr = X[n_val:], D[n_val:]
    # the held-out test set, seen through a different (dimmer, noisier) "camera"
    Xte, Dte = shift_appearance(X[:n_val]), D[:n_val]

    baseline = train(Xtr, Dtr, e, device, rng=None)  # clean training
    dr = train(Xtr, Dtr, e, device, rng=rng)  # domain-randomized training

    base_err = evaluate(baseline, Xte, Dte, device)
    dr_err = evaluate(dr, Xte, Dte, device)
    gain = 100 * (base_err - dr_err) / max(base_err, 1e-6)
    print(
        f"DR OK: baseline AbsRel={base_err:.3f} on shifted scene, "
        f"DR model={dr_err:.3f} (robustness up {gain:.0f}%)"
    )
    if selftest:
        assert (
            dr_err < base_err
        ), f"domain randomization didn't help (DR {dr_err:.3f} vs base {base_err:.3f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
