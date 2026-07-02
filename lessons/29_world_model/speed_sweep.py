"""
Lesson 29 (step 4c) — raise the speed until reaction breaks
===========================================================
Step 4b showed that at a gentle 0.8 m/s cruise, even the reactive baseline
stays crash-free — anticipation only buys *margin* there. This step turns the
margin into the metric that matters: **crash rate versus speed**.

The physics of why the curves must split: the reactive trigger fires at a
fixed visual *distance* (the danger-now head learned "planar < 0.7 m"), so as
speed rises, the time between trigger and impact shrinks — and with bounded
lateral authority, at some speed the evasion no longer fits in the time left.
The world model triggers at a fixed *time* (~0.7 s of look-ahead, because the
danger heads are conditioned on the commanded speed), which is a
speed-proportional distance. Reaction is a distance budget; anticipation is a
time budget. Speed spends the first and not the second.

Both policies fly the same threatened courses at each cruise speed (the same
seeds across speeds), with the whole command set scaled together — the same
model, trained across the 0.6–1.6 m/s envelope, powers every run.

Honest scope: these are *single-pillar* courses on purpose. The threat sits
where both policies can see it, so the sweep isolates the mechanism it claims
to measure. Step 4b's cluttered courses probe something else — the FOV blind
side — and there the hand-crafted planner still pays a measurable crash tail
(side pillars 60–90° off-axis are physically invisible to a fixed-yaw,
memoryless, forward camera; the same tail also grazes a few single-pillar
runs at walking pace). Those numbers are reported, not hidden, in the README —
and the roadmap's fix is learning the policy (Lesson 19) and adding memory,
not more cost-function tuning.

Run:
  python lessons/29_world_model/speed_sweep.py                # saves the plot
  python lessons/29_world_model/speed_sweep.py --seeds 30
  python lessons/29_world_model/speed_sweep.py --selftest     # 2 speeds, asserts
Needs output/world_model.pth (auto-trains a tiny one if missing).
"""

import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen_wm_dataset import make_env  # noqa: E402
from wm_closed_loop import (  # noqa: E402
    ReactivePolicy,
    WMPolicy,
    load_or_train,
    run_episode,
)

SPEEDS = (1.0, 1.25, 1.5, 1.75, 2.0)  # x 0.8 m/s base -> 0.8..1.6 m/s cruise
BASE_V = 0.8  # forward command at speed factor 1.0 (m/s)
OUT = os.path.join(HERE, "output", "speed_sweep.png")


def sweep(speeds, n_seeds: int, seed0: int) -> list:
    """Fly `n_seeds` single-pillar courses per speed with both policies. The
    same seeds repeat across speeds, so each speed step changes exactly one
    thing — and `solo` courses put the one threat where both policies can see
    it, so the sweep measures the anticipation mechanism, not the FOV limit."""
    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    env = make_env()
    rows = []
    for s in speeds:
        crashes = {"reactive": 0, "wm": 0}
        clears = {"reactive": [], "wm": []}
        for i in range(n_seeds):
            for name, policy in (
                ("reactive", ReactivePolicy(enc, nhead)),
                ("wm", WMPolicy(enc, pred, cheads, meta, speed=s)),
            ):
                run = run_episode(
                    env, policy, seed0 + i, in_path=True, speed=s, solo=True
                )
                crashes[name] += int(run["crashed"])
                clears[name].append(run["min_clear"])
        row = {
            "speed": s,
            "v": s * BASE_V,
            "crash_reactive": crashes["reactive"] / n_seeds,
            "crash_wm": crashes["wm"] / n_seeds,
            "clear_reactive": float(np.mean(clears["reactive"])),
            "clear_wm": float(np.mean(clears["wm"])),
        }
        rows.append(row)
        print(
            f"  v={row['v']:.1f} m/s: crash reactive {row['crash_reactive']:.0%} "
            f"vs wm {row['crash_wm']:.0%}, mean clearance "
            f"{row['clear_reactive']:.2f} -> {row['clear_wm']:.2f} m"
        )
    env.close()
    return rows


def _save_plot(rows) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    v = [r["v"] for r in rows]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 3.6))
    ax1.plot(
        v,
        [100 * r["crash_reactive"] for r in rows],
        "o-",
        color="tab:orange",
        label="reactive",
    )
    ax1.plot(
        v,
        [100 * r["crash_wm"] for r in rows],
        "o-",
        color="tab:green",
        label="wm (latent MPC)",
    )
    ax1.set_xlabel("cruise speed (m/s)")
    ax1.set_ylabel("crash rate (%)")
    ax1.set_title("Reaction is a distance budget")
    ax1.legend(fontsize=8)
    ax2.plot(
        v,
        [r["clear_reactive"] for r in rows],
        "o-",
        color="tab:orange",
        label="reactive",
    )
    ax2.plot(
        v,
        [r["clear_wm"] for r in rows],
        "o-",
        color="tab:green",
        label="wm (latent MPC)",
    )
    ax2.set_xlabel("cruise speed (m/s)")
    ax2.set_ylabel("mean min clearance (m)")
    ax2.set_title("Anticipation is a time budget")
    ax2.legend(fontsize=8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=110)
    print(f"[INFO] saved {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=30)
    ap.add_argument("--seed0", type=int, default=3000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    speeds, n = ((1.0, 2.0), 8) if args.selftest else (SPEEDS, args.seeds)

    rows = sweep(speeds, n, args.seed0)
    _save_plot(rows)
    lo, hi = rows[0], rows[-1]
    print(
        f"SPEED-SWEEP OK: {n} single-pillar courses/speed — at {lo['v']:.1f} m/s "
        f"crash reactive/wm = {lo['crash_reactive']:.0%}/{lo['crash_wm']:.0%}; "
        f"at {hi['v']:.1f} m/s crash reactive/wm = "
        f"{hi['crash_reactive']:.0%}/{hi['crash_wm']:.0%} — reaction pays a "
        f"distance, anticipation pays time"
    )
    if args.selftest:
        assert (
            hi["crash_wm"] < hi["crash_reactive"] - 0.25
        ), "the story did not hold: wm does not clearly out-survive reactive at speed"
        assert hi["clear_wm"] > hi["clear_reactive"], "no clearance edge at speed"
        # at walking pace both should be near-clean; the wm is allowed the
        # small planner tail the docstring's honest note documents
        assert (
            lo["crash_wm"] <= lo["crash_reactive"] + 2.0 / n + 1e-9
        ), "wm crashes at base speed beyond the documented planner tail"


if __name__ == "__main__":
    main()
    sys.exit(0)
