"""
Lesson 29 (step 4) — close the loop: the world model flies from vision alone
============================================================================
Step 3 (`proactive_avoid.py`) isolated the *timing* benefit of anticipation
with the simulator's privileged future geometry standing in for the model.
This step removes the crutch. Here the danger signal in the control loop comes
from the **camera alone**: frame -> encoder -> predictor -> collision heads.
The pillar positions are used to *score* the flight afterwards (min clearance,
crashes) — never to fly it.

Two controllers fly the same course (same seed, same pillars):

  * **reactive** — the danger-*now* head (same encoder, no look-ahead) says
    "too close!", and the drone evades. Honest note: we hand this baseline the
    evasion *direction* from privileged pillar positions — a deliberately
    generous opponent. If anticipation still wins on clearance while choosing
    its own direction from vision, the win is real.
  * **wm (proactive)** — a tiny **latent MPC**. At ~12 Hz (an on-board-honest
    decision rate) it encodes the frame once, then asks the predictor "and if
    I held *this* command?" for every candidate on its menu. Each answer costs
    one pass through a small MLP — the expensive encoder is shared — so on a
    GAP8 the whole deliberation is nearly free. It picks the cheapest action:

      cost = 6 * danger  +  1 * heading_error  +  0.5 * switch  -  1.5 * progress

    where danger is the worst collision probability across the four horizons.
    Anticipation means the danger term rises ~600 ms before the reactive one,
    so the veer starts earlier and the miss is wider — the whole lesson in one
    number.

Run:
  python lessons/29_world_model/wm_closed_loop.py             # saves the plot
  python lessons/29_world_model/wm_closed_loop.py --gui       # watch it fly
  python lessons/29_world_model/wm_closed_loop.py --selftest  # asserts (local)
Needs output/world_model.pth (auto-trains a tiny one if missing).
"""

import argparse
import os
import sys

import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen_wm_dataset import (  # noqa: E402
    ACTION_NAMES,
    ACTION_VECS,
    COLLISION_R,
    CTRL_HZ,
    DANGER_R,
    FORWARD,
    VelCommander,
    gen,
    grab_frame,
    make_ctrl,
    make_env,
    nearest_planar,
    spawn_pillars,
)
from train_world_model import MODEL, load_model, train  # noqa: E402

GOAL_X = 3.0  # finish line (m)
TMAX = 360  # step budget (7.5 s @ 48 Hz)
DECIDE_EVERY = 4  # decide at 12 Hz — an honest on-board rate; PID stays 48 Hz
THETA_NOW = 0.5  # reactive trigger on P(too close now)
EVADE_HOLD = 24  # reactive holds its evasion ~0.5 s before re-checking
W_DANGER, W_HEAD, W_SWITCH, W_PROG = 6.0, 1.0, 0.5, 1.5  # MPC cost weights
SCENARIO_SEED = 11  # the demo course (step-4 eval sweeps many seeds)
OUT = os.path.join(HERE, "output", "wm_closed_loop.png")


def _frame_tensor(frame: np.ndarray) -> torch.Tensor:
    x = torch.tensor(frame, dtype=torch.float32).permute(2, 0, 1) / 255.0
    return x.unsqueeze(0)  # (1, 3, 64, 64)


class WMPolicy:
    """Latent MPC from vision alone: encode once, imagine every candidate,
    pick the cheapest future. Never sees the pillar positions."""

    def __init__(self, enc, pred, cheads, meta):
        self.enc, self.pred, self.cheads = enc, pred, cheads
        names = list(meta["action_names"])
        vecs = np.array(meta["action_vecs"], dtype=np.float32)
        # The planner's menu. The corridor task is planar and `climb` games the
        # planar danger label (a slower planar approach scores "safer" without
        # ever engaging the visual task — traced: the MPC climbed over the
        # course), so the planner leaves it off the menu; the model itself
        # still knows the full six-command vocabulary.
        self.ids = [i for i, n in enumerate(names) if n != "climb"]
        sub = vecs[self.ids]
        self.cands = torch.tensor(sub / np.array(meta["a_norm"], dtype=np.float32))
        # per-candidate cost terms that never change: heading error vs the +x
        # goal direction, and forward progress (commanded vx)
        xy = sub[:, :2]
        speed = np.linalg.norm(xy, axis=1)
        self.heading = torch.tensor(
            np.where(speed > 1e-6, 1.0 - xy[:, 0] / np.maximum(speed, 1e-6), 1.0),
            dtype=torch.float32,
        )
        self.progress = torch.tensor(sub[:, 0])
        self.prev = FORWARD

    def begin(self, pillars) -> None:
        del pillars  # vision only — the whole point
        self.prev = FORWARD

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        del state  # no privileged pose-vs-pillar geometry either
        with torch.no_grad():
            z = self.enc(_frame_tensor(frame))  # encoder runs ONCE
            z_hat = self.pred(z.expand(len(self.cands), -1), self.cands)
            p = torch.sigmoid(self.cheads(z_hat))  # (n_cands, n_horizons)
        danger = p.max(dim=1).values  # worst case across 83..667 ms
        switch = torch.tensor([0.0 if a_id == self.prev else 1.0 for a_id in self.ids])
        cost = (
            W_DANGER * danger
            + W_HEAD * self.heading
            + W_SWITCH * switch
            - W_PROG * self.progress
        )
        self.prev = self.ids[int(cost.argmin())]
        return self.prev


class ReactivePolicy:
    """The honest baseline: same encoder, but only the danger-*now* head — no
    look-ahead. Generous handicap: when it does trigger, we hand it the correct
    evasion direction from privileged pillar positions (a real reactive stack
    would need L17's depth net for that). It can only lose on *timing*."""

    def __init__(self, enc, nhead):
        self.enc, self.nhead = enc, nhead
        self.pillars = []
        self.hold = 0
        self.evade = FORWARD

    def begin(self, pillars) -> None:
        self.pillars = [np.array(q) for q in pillars]
        self.hold, self.evade = 0, FORWARD

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        if self.hold > 0:
            self.hold -= DECIDE_EVERY
            return self.evade
        with torch.no_grad():
            p_now = float(torch.sigmoid(self.nhead(self.enc(_frame_tensor(frame)))))
        if p_now > THETA_NOW:
            q = min(self.pillars, key=lambda q: np.linalg.norm(state[0:2] - q))
            away_left = state[1] > q[1]  # privileged direction (see class note)
            self.evade = ACTION_NAMES.index("veer_left" if away_left else "veer_right")
            self.hold = EVADE_HOLD
            return self.evade
        return FORWARD


def run_episode(
    env, policy, scenario_seed: int, tmax: int = TMAX, in_path: bool = True
) -> dict:
    """Fly START -> GOAL_X once under `policy`. The same seed reproduces the
    same pillar course, so two policies can fly literally the same test.
    `in_path=False` gives a course that is safe if flown straight — the
    step-4b eval uses those to count false-positive evasions."""
    rng = np.random.default_rng(scenario_seed)
    obs, _ = env.reset(seed=int(scenario_seed))
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    cmd.reset(obs[0][0:3])
    pillars = spawn_pillars(env, rng, in_path=in_path)
    policy.begin(pillars)

    state, a_id, trigger = obs[0], FORWARD, -1
    path, min_clear = [state[0:3].copy()], 9.0
    for t in range(tmax):
        if t % DECIDE_EVERY == 0:
            a_id = policy.decide(grab_frame(env), state)
            if a_id != FORWARD and trigger < 0:
                trigger = t
        obs, _, _, _, _ = env.step(cmd.rpm(state, ACTION_VECS[a_id]).reshape(1, 4))
        state = obs[0]
        path.append(state[0:3].copy())
        min_clear = min(min_clear, nearest_planar(state[0:2], pillars))
        if state[0] >= GOAL_X:
            break
    return {
        "path": np.array(path),
        "pillars": pillars,
        "min_clear": min_clear,
        "trigger": trigger,
        "crashed": min_clear < COLLISION_R,
        "steps": len(path) - 1,
        "reached": bool(state[0] >= GOAL_X),
    }


def load_or_train(device: str = "cpu"):
    """Course convention: every step runs on its own. No checkpoint -> train a
    tiny one right here (slower but self-contained)."""
    if not os.path.exists(MODEL):
        print(f"[INFO] no model at {MODEL}; training a tiny one first ...")
        ckpt, _ = train(gen(12, 100), epochs=40)
        os.makedirs(os.path.dirname(MODEL), exist_ok=True)
        torch.save(ckpt, MODEL)
    return load_model(MODEL, device=device)


def _save_plot(reactive: dict, wm: dict) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(6, 4))
    runs = ((reactive, "tab:orange", "reactive"), (wm, "tab:green", "wm (latent MPC)"))
    for run, color, name in runs:
        px = run["path"]
        ax.plot(px[:, 0], px[:, 1], "-", color=color, label=name)
        if run["trigger"] >= 0:
            ax.plot(*px[run["trigger"], :2], "o", color=color, markersize=6)
    ax.plot(0, 0, "ko", markersize=8, label="start")
    ax.axvline(GOAL_X, color="k", linestyle=":", linewidth=1)
    for q in wm["pillars"]:
        ax.add_patch(plt.Circle(q, COLLISION_R, color="red", alpha=0.6))
        ax.add_patch(plt.Circle(q, DANGER_R, color="red", alpha=0.10))
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Closed loop from vision: latent-MPC world model vs reactive")
    ax.legend(loc="best", fontsize=8)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.tight_layout()
    fig.savefig(OUT, dpi=110)
    print(f"[INFO] saved {OUT}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gui", action="store_true")
    ap.add_argument("--seed", type=int, default=SCENARIO_SEED)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    env = make_env(gui=args.gui)
    reactive = run_episode(env, ReactivePolicy(enc, nhead), args.seed)
    wm = run_episode(env, WMPolicy(enc, pred, cheads, meta), args.seed)
    env.close()
    _save_plot(reactive, wm)

    lead = reactive["trigger"] - wm["trigger"]
    print(
        f"WM-CLOSED-LOOP OK: reactive min-clear={reactive['min_clear']:.2f} m "
        f"(trigger@{reactive['trigger']}), wm min-clear={wm['min_clear']:.2f} m "
        f"(trigger@{wm['trigger']}), lead=+{lead} steps "
        f"(~{lead * 1000 / CTRL_HZ:.0f} ms earlier), crashes reactive/wm = "
        f"{int(reactive['crashed'])}/{int(wm['crashed'])}, goal steps = "
        f"{reactive['steps']}/{wm['steps']} — danger signal from camera alone "
        f"(no privileged look-ahead in control)"
    )
    if args.selftest:
        assert wm["trigger"] >= 0, "wm never deviated from cruise"
        assert reactive["trigger"] >= 0, "reactive never triggered"
        assert lead > 0, "wm did not trigger earlier than reactive"
        assert wm["min_clear"] > reactive["min_clear"], "no clearance gain"
        assert not wm["crashed"], "wm crashed"
        assert wm["reached"], "wm never reached the goal line"


if __name__ == "__main__":
    main()
    sys.exit(0)
