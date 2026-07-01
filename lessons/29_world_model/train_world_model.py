"""
Lesson 29 (step 2) — train a nano world model (V-JEPA style, latent prediction)
===============================================================================
This is the heart of the lesson. A *world model* answers "if I see this and take
this action, what will I see next?" The trap most people fall into is to answer
in *pixels* — predict the next image (or diffuse it). That is slow and it
hallucinates detail a drone can't act on. We do it the V-JEPA way instead:

  predict the *next latent embedding*, never the next pixels.

Three tiny networks (all reused from the course's conv stack, all int8-able):
  * Encoder f_theta : image -> z            (Lesson 3's TinyDronet conv stack)
  * Predictor g_phi : (z_t, action) -> z_hat_{t+k}   (a small MLP)
  * Collision head  : z_hat -> P(too close soon)      (one linear layer)

The target is produced by an **EMA copy** of the encoder (stop-gradient), the
JEPA/BYOL trick that lets us learn in latent space without a pixel loss and
without collapsing to a constant. A VICReg-style variance term is a second guard
against collapse. The loss is purely:

  ||g_phi(f_theta(x_t), a_t) - sg(f_ema(x_{t+k}))||^2   +  var_guard  +  BCE(collision)

Honest scope: the real V-JEPA / V-JEPA 2 is a billion-parameter ViT that needs a
GPU (an Orin-class board), not a GAP8. This is a *nano distillation of the idea* —
the same joint-embedding-prediction principle, shrunk under the 512 KB int8
budget so it keeps the course's north star. The signature move once more: the
generic (Orin-class) world model won't deploy, so you train your own tiny one.

Run:
  python lessons/29_world_model/train_world_model.py --epochs 80
  python lessons/29_world_model/train_world_model.py --selftest   # tiny, asserts
Saves output/world_model.pth (git-ignored).
"""

import argparse
import os
import sys

import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "03_autonomy_ai")))

from gen_wm_dataset import DANGER_R, HORIZON_K, gen  # noqa: E402
from gen_wm_dataset import OUT as DATA  # noqa: E402
from train_cnn import TinyDronet  # noqa: E402  (reuse Lesson 3's conv stack)

LATENT_D = 64  # embedding size (TinyDronet's conv stack already outputs 64)
ACTION_D = 4  # (vx, vy, vz, yaw-rate)
EMA_M = 0.99  # target-encoder momentum
LAMBDA_VAR = 1.0  # anti-collapse (VICReg-style variance hinge)
LAMBDA_COL = 1.0  # collision-head weight
GAP8_BUDGET_KB = 512
MODEL = os.path.join(HERE, "output", "world_model.pth")


class Encoder(nn.Module):
    """Image -> latent z. Reuses Lesson 3's TinyDronet conv stack verbatim (the
    same features Lesson 17's depth net used), then flattens the 64-ch pooled
    vector into a 64-d embedding."""

    def __init__(self):
        super().__init__()
        self.features = TinyDronet().features  # (B,3,64,64) -> (B,64,1,1)
        self.flat = nn.Flatten()

    def forward(self, x):  # x: (B, 3, 64, 64)
        return self.flat(self.features(x))  # (B, 64)


class Predictor(nn.Module):
    """Action-conditioned latent forecaster: z_hat_{t+k} = z_t + delta(z_t, a_t).

    Predicting the *residual* (how the latent moves) rather than the absolute
    next latent bakes in the right inductive bias: with a zero residual it
    reproduces 'the future looks like the present', so any learned motion can
    only improve on that baseline."""

    def __init__(self, d=LATENT_D, a=ACTION_D, h=128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d + a, h), nn.ReLU(), nn.Linear(h, d))

    def forward(self, z, a):  # z: (B,D)  a: (B,A)
        return z + self.net(torch.cat([z, a], dim=1))  # (B, D)


class CollisionHead(nn.Module):
    """Predicted-future latent -> logit for 'dangerously close within k steps'."""

    def __init__(self, d=LATENT_D):
        super().__init__()
        self.lin = nn.Linear(d, 1)

    def forward(self, z):  # z: (B, D)
        return self.lin(z).squeeze(-1)  # (B,)


@torch.no_grad()
def ema_update(target: nn.Module, online: nn.Module, m: float) -> None:
    """target = m*target + (1-m)*online (stop-gradient by construction)."""
    for pt, po in zip(target.parameters(), online.parameters()):
        pt.mul_(m).add_(po.detach(), alpha=1.0 - m)


def roc_auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Rank-based AUC (Mann-Whitney U); 0.5 = chance."""
    pos, neg = scores[labels > 0.5], scores[labels < 0.5]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    order = np.concatenate([pos, neg]).argsort()
    ranks = np.empty(len(order), dtype=np.float64)
    ranks[order] = np.arange(1, len(order) + 1)
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def _load_or_make(selftest: bool) -> dict:
    if selftest:
        return gen(8, 60)  # self-contained tiny set (no prior npz needed)
    if os.path.exists(DATA):
        blob = np.load(DATA)
        return {k: blob[k] for k in ("X", "Xk", "A", "c")}
    print(f"[INFO] no dataset at {DATA}; generating a default one ...")
    return gen(20, 80)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=80)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    epochs = 40 if args.selftest else args.epochs

    data = _load_or_make(args.selftest)
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    print(f"[INFO] training on {device}, {len(data['c'])} sequences")

    # (N,H,W,3) -> (N,3,H,W)
    Xt = torch.tensor(data["X"]).permute(0, 3, 1, 2)
    Xk = torch.tensor(data["Xk"]).permute(0, 3, 1, 2)
    A = torch.tensor(data["A"])
    c = torch.tensor(data["c"])

    n_val = max(8, int(0.2 * len(Xt)))
    perm = torch.randperm(len(Xt))
    tr, va = perm[n_val:], perm[:n_val]

    enc = Encoder().to(device)
    tgt = Encoder().to(device)
    tgt.load_state_dict(enc.state_dict())
    for p in tgt.parameters():
        p.requires_grad_(False)
    pred = Predictor().to(device)
    head = CollisionHead().to(device)

    params = list(enc.parameters()) + list(pred.parameters()) + list(head.parameters())
    opt = torch.optim.Adam(params, lr=1e-3)
    bce = nn.BCEWithLogitsLoss()

    Xt, Xk, A, c = Xt.to(device), Xk.to(device), A.to(device), c.to(device)

    for epoch in range(1, epochs + 1):
        enc.train(), pred.train(), head.train()
        order = tr[torch.randperm(len(tr))]
        for i in range(0, len(order), args.batch):
            b = order[i : i + args.batch]
            opt.zero_grad()
            z_t = enc(Xt[b])
            z_hat = pred(z_t, A[b])
            with torch.no_grad():
                z_k_tgt = tgt(Xk[b])
            pred_loss = ((z_hat - z_k_tgt) ** 2).mean()
            var_loss = torch.relu(1.0 - z_t.std(dim=0)).mean()  # VICReg-style guard
            col_loss = bce(head(z_hat), c[b])
            (pred_loss + LAMBDA_VAR * var_loss + LAMBDA_COL * col_loss).backward()
            opt.step()
            ema_update(tgt, enc, EMA_M)

    # -- validation metrics -------------------------------------------------
    enc.eval(), pred.eval(), head.eval()
    with torch.no_grad():
        z_t = enc(Xt[va])
        z_hat = pred(z_t, A[va])
        z_k_tgt = tgt(Xk[va])
        pred_mse = float(((z_hat - z_k_tgt) ** 2).mean())
        noop_mse = float(((z_t - z_k_tgt) ** 2).mean())  # predictor does nothing
        scores = torch.sigmoid(head(z_hat)).cpu().numpy()
    auc = roc_auc(scores, c[va].cpu().numpy())

    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(
        {
            "encoder": enc.state_dict(),
            "predictor": pred.state_dict(),
            "collision_head": head.state_dict(),
            "meta": {
                "D": LATENT_D,
                "A": ACTION_D,
                "k": HORIZON_K,
                "danger_r": DANGER_R,
            },
        },
        MODEL,
    )
    n_params = sum(p.numel() for p in params)
    int8_kb = n_params / 1024  # GAP8 stores int8 weights (same formula as L4/L17)
    print(
        f"WORLD-MODEL OK: trained {len(tr)} seqs, latent MSE={pred_mse:.4f} "
        f"(no-op baseline {noop_mse:.4f}), collision AUC={auc:.2f}, "
        f"int8 footprint={int8_kb:.1f} KB (<{GAP8_BUDGET_KB} fits), saved {MODEL}"
    )
    if args.selftest:
        assert pred_mse < noop_mse, "predictor no better than 'future == present'"
        assert auc > 0.70, f"collision head barely predicts danger (AUC {auc:.2f})"
        assert int8_kb < GAP8_BUDGET_KB, f"too big for GAP8 ({int8_kb:.1f} KB)"


if __name__ == "__main__":
    main()
    sys.exit(0)
