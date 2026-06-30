"""
Lesson 22 — distill multiple skills into ONE on-board policy (Track B capstone)
===============================================================================
Avoidance (Lesson 19) and following (Lesson 8) are separate networks/loops. On
GAP8 you can't run several nets and switch between them mid-flight — there's room
for one small policy. So we **distill**: let the specialist teachers demonstrate
(observation -> action), and train a single student network to imitate them all.
This closes the on-board AI thread — every self-trained small model from L17–L21
folded into one brain that fits.

For a robust, self-contained run the teachers here are compact reference
controllers (avoid the nearest obstacle / steer to the target); the same pipeline
takes Lesson 19's PPO policy and Lesson 8's follower as the teachers in a full run.

Run:
  python lessons/22_unified/distill_policy.py
  python lessons/22_unified/distill_policy.py --selftest   # asserts (local)
"""

import os
import sys

import numpy as np
import torch
import torch.nn as nn

GAP8_BUDGET_KB = 512
DANGER = 0.6  # within this range of an obstacle, avoidance takes over
MODEL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "unified_policy.pth"
)


def _unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-6 else v * 0.0


def avoid_teacher(goal_rel, obs_rel):
    """Steer directly away from the nearest obstacle."""
    return _unit(-obs_rel)


def follow_teacher(goal_rel, obs_rel):
    """Steer toward the target."""
    return _unit(goal_rel)


def combined(goal_rel, obs_rel):
    """The behaviour we want the one policy to learn: avoid when an obstacle is
    close, otherwise follow the target."""
    if np.linalg.norm(obs_rel) < DANGER:
        return avoid_teacher(goal_rel, obs_rel)
    return follow_teacher(goal_rel, obs_rel)


def gen_dataset(n, rng):
    """Random (goal, obstacle) geometries -> the combined teacher's action.
    Half the samples deliberately put the obstacle in the danger zone, so the
    policy gets enough avoidance demonstrations to learn from (uniform sampling
    almost never lands an obstacle that close)."""
    X, Y = [], []
    for i in range(n):
        goal_rel = rng.uniform(-2.5, 2.5, size=2)
        if i % 2 == 0:  # oversample close obstacles (the danger zone)
            ang = rng.uniform(-np.pi, np.pi)
            r = rng.uniform(0.1, DANGER)
            obs_rel = np.array([r * np.cos(ang), r * np.sin(ang)])
        else:
            obs_rel = rng.uniform(-2.5, 2.5, size=2)
        obs_features = np.array(
            [*goal_rel, np.linalg.norm(goal_rel), *obs_rel, np.linalg.norm(obs_rel)]
        )
        X.append(obs_features)
        Y.append(combined(goal_rel, obs_rel))
    return np.array(X, dtype=np.float32), np.array(Y, dtype=np.float32)


class UnifiedPolicy(nn.Module):
    """One small MLP: 6-D observation -> 2-D velocity command."""

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 32), nn.ReLU(), nn.Linear(32, 32), nn.ReLU(), nn.Linear(32, 2)
        )

    def forward(self, x):
        return self.net(x)


def main() -> None:
    selftest = "--selftest" in sys.argv
    n, e = (1500, 120) if selftest else (4000, 300)
    rng = np.random.default_rng(0)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    X, Y = gen_dataset(n, rng)
    Xt, Yt = torch.tensor(X).to(device), torch.tensor(Y).to(device)
    n_val = int(0.2 * len(Xt))
    net = UnifiedPolicy().to(device)
    opt = torch.optim.Adam(net.parameters(), lr=2e-3)
    loss_fn = nn.MSELoss()
    for _ in range(e):
        net.train()
        order = torch.randperm(len(Xt) - n_val) + n_val
        for i in range(0, len(order), 64):
            b = order[i : i + 64]
            opt.zero_grad()
            loss_fn(net(Xt[b]), Yt[b]).backward()
            opt.step()

    net.eval()
    with torch.no_grad():
        pred = net(Xt[:n_val])
        mse = float(loss_fn(pred, Yt[:n_val]))
        pred_np = pred.cpu().numpy()
    # behaviour split: well inside the danger zone the policy must point away
    # from the obstacle (the boundary band is intentionally ambiguous, so we
    # check states clearly closer than DANGER).
    Xv = X[:n_val]
    near = np.linalg.norm(Xv[:, 3:5], axis=1) < 0.45
    away = (pred_np[near] * (-Xv[near, 3:5])).sum(axis=1) > 0  # dot with away-dir
    avoid_rate = float(away.mean()) if near.any() else 1.0

    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    int8_kb = sum(p.numel() for p in net.parameters()) / 1024
    print(
        f"UNIFIED OK: distilled 2 teachers (avoid+follow) into one policy, "
        f"imitation MSE={mse:.3f}, avoids in {100 * avoid_rate:.0f}% of danger states, "
        f"single int8={int8_kb:.1f} KB (<{GAP8_BUDGET_KB} fits)"
    )
    if selftest:
        assert mse < 0.05, f"student didn't imitate the teachers (MSE {mse:.3f})"
        assert (
            avoid_rate > 0.8
        ), f"student doesn't avoid inside the danger zone ({avoid_rate:.2f})"
        assert int8_kb < GAP8_BUDGET_KB, f"policy too big ({int8_kb:.1f} KB)"


if __name__ == "__main__":
    main()
    sys.exit(0)
