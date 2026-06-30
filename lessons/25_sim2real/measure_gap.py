"""
Lesson 25 — measure the sim-to-real gap, honestly
==================================================
The course's models (L3/L8/L13/L17) were all trained and scored in clean sim.
The honest question before trusting one on hardware: how much accuracy do you
lose on a real camera? This measures it — run a sim-trained depth model on clean
sim frames vs the *same* frames degraded to look like a real camera
(`nanodrone.degrade`: dimmer + blur + noise), and report the gap. It turns the
hand-wave "it'll be worse on real hardware" into a number, and motivates Lesson
20's domain randomization (which should shrink this gap).

Run (uses Lesson 17's network):
  python lessons/25_sim2real/measure_gap.py
  python lessons/25_sim2real/measure_gap.py --selftest   # tiny run, asserts (local)
"""

import os
import sys

import torch
import torch.nn as nn

try:
    from nanodrone.degrade import degrade

    _L17 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "17_depth"
    )
    sys.path.insert(0, _L17)
    from train_depth import MAX_DEPTH, TinyDepthNet, abs_rel, gen_dataset
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 25 dependencies:", exc)
    sys.exit(1)


def main() -> None:
    selftest = "--selftest" in sys.argv
    n, e = (160, 45) if selftest else (320, 60)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print(f"[INFO] generating {n} samples ...")
    X, D = gen_dataset(n)
    n_val = max(8, int(0.25 * len(X)))
    Xtr = torch.tensor(X[n_val:]).permute(0, 3, 1, 2).to(device)
    ytr = torch.tensor(D[n_val:] / MAX_DEPTH).to(device)

    # train on CLEAN sim images (as every earlier lesson did)
    net = TinyDepthNet().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.L1Loss()
    for _ in range(e):
        net.train()
        order = torch.randperm(len(Xtr))
        for i in range(0, len(Xtr), 32):
            b = order[i : i + 32]
            opt.zero_grad()
            loss_fn(net(Xtr[b]), ytr[b]).backward()
            opt.step()
    net.eval()

    # evaluate on clean test vs the SAME frames seen through a real-ish camera
    Xte, Dte = X[:n_val], D[:n_val]
    Xdeg = degrade(Xte)
    with torch.no_grad():
        clean = abs_rel(
            net(torch.tensor(Xte).permute(0, 3, 1, 2).to(device)).cpu().numpy()
            * MAX_DEPTH,
            Dte,
        )
        real = abs_rel(
            net(torch.tensor(Xdeg).permute(0, 3, 1, 2).to(device)).cpu().numpy()
            * MAX_DEPTH,
            Dte,
        )
    gap = real - clean
    print(
        f"SIM2REAL OK: sim AbsRel={clean:.3f}, degraded(real-ish) AbsRel={real:.3f}, "
        f"gap={gap:.3f} measured over {n_val} frames"
    )
    if selftest:
        assert gap > 0.02, f"degradation should measurably hurt (gap {gap:.3f})"
        assert clean < 0.25, f"model didn't even fit clean sim (AbsRel {clean:.3f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
