"""
Lesson 29 (step 1) — self-produce an *intervention* dataset for the world model
===============================================================================
Every earlier lesson learned a mapping from *one* frame (image -> bearing,
image -> depth). A world model is different: it learns how the world *changes*
— and, crucially, how it changes *because of what you do*. So the data is no
longer single frames, and it is no longer passive footage either. Each rollout
is a tiny controlled experiment:

  1. **Fresh trial.** The simulator is reset every rollout (drone back at the
     start, PID integrators cleared), so all rollouts really are independent
     passes through a fresh pillar layout — not one long drifting flight.
  2. **Approach.** The drone cruises forward under a *commanded* velocity
     setpoint (the same "forward" command the controller will use later).
  3. **Interventions.** The rest of the flight is a chain of held *segments*:
     every ~1 s we draw one of six high-level commands — forward / slow /
     veer_left / veer_right / climb / hover — and **hold it** for the whole
     segment before drawing the next.

Holding the command is the whole point. A world model that must answer "what
happens if I *keep doing this* for the next k steps?" needs training pairs
where one action really was kept for k steps — and every segment switch is one
more counterfactual contrast ("same view, different command, different
outcome"), which is exactly the action-conditioning the step-3 planner needs.
We record the **commanded setpoint**, not the measured velocity: the controller
can only ever feed the model a command, so that is what it must condition on.

Labels stay free (the simulator's signature move), and are now *multi-horizon*:
for each step we keep the nearest-pillar distance, so step 2 can derive
"dangerously close within 4 / 8 / 16 / 32 control steps" (~83 / 167 / 333 /
667 ms at 48 Hz) for any horizon. And the simulator hands out one more freebie:
**counterfactual** danger labels (`counterfactual_labels`) — for *every* frame
and *every* candidate command, roll the command forward kinematically through
the known pillar layout and label whether it would get dangerously close. The
executed action tells the model what *did* happen; the counterfactuals teach it
to *rank* the actions it did not take, which is exactly what a planner asks.
(Honest note: that oracle is straight-line kinematics — no PID transient — and
it exists only because sim labels are privileged anyway; with real-world data
you would be back to executed-action supervision and need far more of it.)

No pixel target anywhere: step 2 predicts in *latent* space. This file only
stores raw frames + held commands + distances (+ the pillar layout, used for
labels and evaluation — never for control).

Honest notes: pillars are visual-only (no contact physics), so "danger" is a
planar distance, measured even when the drone flies straight through — which
is exactly what makes the through-pass labels clean. And `climb` changes what
the camera sees but not the planar danger label; it is in the vocabulary for
action diversity, not as a labelled escape route.

Run:
  python lessons/29_world_model/gen_wm_dataset.py --rollouts 32 --len 120
  python lessons/29_world_model/gen_wm_dataset.py --selftest   # tiny, asserts (local)
Saves output/wm_dataset.npz (git-ignored).
"""

import argparse
import os
import sys

import numpy as np

IMG_RES = 64  # camera + network input (matches L3/L8/L17)
HORIZONS = (4, 8, 16, 32)  # label horizons in control steps (~83..667 ms @ 48 Hz)
H_MAX = HORIZONS[-1]
DANGER_R = 0.7  # planar distance (m) that counts as "dangerously close" soon
COLLISION_R = 0.22  # planar distance (m) that counts as a crash (matches L3/L19)
CTRL_HZ = 48
FOV_HALF_DEG = 28  # camera half-FOV (the sim renders 60 deg; keep a margin)
START = np.array([0.0, 0.0, 1.0])

# The six high-level commands (m/s + yaw-rate). World frame with yaw held at 0,
# so body frame == world frame throughout — the honest nano simplification that
# keeps dataset actions and the step-3/4 MPC candidates literally identical.
ACTIONS = {
    "forward": (0.80, 0.00, 0.00, 0.0),
    "slow": (0.30, 0.00, 0.00, 0.0),
    "veer_left": (0.50, 0.50, 0.00, 0.0),
    "veer_right": (0.50, -0.50, 0.00, 0.0),
    "climb": (0.40, 0.00, 0.40, 0.0),
    "hover": (0.00, 0.00, 0.00, 0.0),
}
ACTION_NAMES = list(ACTIONS)
ACTION_VECS = np.array([ACTIONS[n] for n in ACTION_NAMES], dtype=np.float32)
FORWARD = ACTION_NAMES.index("forward")
# Per-dim normaliser so every action feeds the network in ~[-1, 1].
A_NORM = np.maximum(np.abs(ACTION_VECS).max(axis=0), 1e-6).astype(np.float32)

OUT = os.path.join(os.path.dirname(__file__), "output", "wm_dataset.npz")


def make_env(gui: bool = False):
    """CtrlAviary at 48 Hz with the 64x64 on-board camera (shared by steps 1/3/4)."""
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=CTRL_HZ,
        gui=gui,
    )
    env.IMG_RES = np.array([IMG_RES, IMG_RES])
    return env


def make_ctrl():
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.utils.enums import DroneModel

    return DSLPIDControl(drone_model=DroneModel.CF2X)


def spawn_pillars(env, rng, in_path: bool):
    """Drop 2-3 visual pillars into a fresh (post-reset) arena and return their
    planar centres. `in_path=True` puts the first one in the forward corridor;
    otherwise all sit off to the sides. Bodies are wiped by the next env.reset()."""
    import pybullet as p

    pillars = []
    n = int(rng.integers(2, 4))
    for i in range(n):
        if in_path and i == 0:
            px, py = float(rng.uniform(1.3, 2.0)), float(rng.uniform(-0.2, 0.2))
        else:
            px, py = float(rng.uniform(0.9, 2.6)), float(rng.uniform(0.9, 1.5))
            py *= 1.0 if rng.random() < 0.5 else -1.0
        pillars.append((px, py))
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=0.18,
            length=1.4,
            rgbaColor=[0.80, 0.32, 0.22, 1],
            physicsClientId=env.CLIENT,
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[px, py, 0.7],
            physicsClientId=env.CLIENT,
        )
    return pillars


class VelCommander:
    """Track a held velocity command with the two-layer split intact: we integrate
    a reference position (re-anchored whenever the command changes) and let the
    PID flight controller chase it. The AI layer only ever emits (vx, vy, vz);
    the 48 Hz attitude loop stays the controller's job."""

    def __init__(self, ctrl, dt: float):
        self.ctrl, self.dt = ctrl, dt
        self.ref = None
        self.last = None

    def reset(self, pos) -> None:
        self.ctrl.reset()
        self.ref = np.array(pos, dtype=float)
        self.last = None

    def rpm(self, state, v_cmd):
        v = np.asarray(v_cmd[:3], dtype=float)
        if self.last is None or not np.allclose(v_cmd, self.last):
            self.ref = state[0:3].copy()  # re-anchor so a switch never jumps
            self.last = np.array(v_cmd, dtype=float)
        self.ref = self.ref + v * self.dt
        rpm, _, _ = self.ctrl.computeControlFromState(
            control_timestep=self.dt, state=state, target_pos=self.ref, target_vel=v
        )
        return rpm


def grab_frame(env) -> np.ndarray:
    """One 64x64x3 uint8 frame from the on-board camera."""
    rgb, _dep, _seg = env._getDroneImages(0, segmentation=False)
    return rgb[:IMG_RES, :IMG_RES, :3].astype(np.uint8)


def nearest_planar(pos_xy, pillars) -> float:
    """Planar distance from pos to the closest pillar centre (m)."""
    if not len(pillars):
        return 9.0
    return float(min(np.linalg.norm(np.asarray(pos_xy) - np.array(q)) for q in pillars))


def _schedule(rng, length: int, passive: bool):
    """Per-step (action-id, segment-id) arrays for one rollout: an all-forward
    approach, then ~1 s held segments each drawing a fresh random command."""
    ids = np.full(length, FORWARD, dtype=np.int16)
    seg = np.zeros(length, dtype=np.int16)
    if passive:
        return ids, seg
    t, s = int(rng.integers(24, 49)), 0
    while t < length:
        s += 1
        n = int(rng.integers(H_MAX + 8, H_MAX + 25))  # hold 40..56 steps (~1 s)
        ids[t : t + n] = int(rng.integers(0, len(ACTION_NAMES)))
        seg[t : t + n] = s
        t += n
    return ids, seg


def gen(n_rollouts: int, length: int, seed: int = 0) -> dict:
    """Fly `n_rollouts` fresh intervention trials and return the raw sequences:
    frames (uint8), held commands, nearest-pillar distances, drone positions,
    plus per-rollout metadata (pillar layout, per-step segment ids, in-path flag)."""
    env = make_env()
    cmd = VelCommander(make_ctrl(), env.CTRL_TIMESTEP)
    rng = np.random.default_rng(seed)

    R, L = n_rollouts, length
    frames = np.zeros((R, L, IMG_RES, IMG_RES, 3), dtype=np.uint8)
    actions = np.zeros((R, L, 4), dtype=np.float32)
    act_id = np.zeros((R, L), dtype=np.int16)
    seg = np.zeros((R, L), dtype=np.int16)
    dists = np.zeros((R, L), dtype=np.float32)
    pos = np.zeros((R, L, 3), dtype=np.float32)
    pillars_meta = np.full((R, 3, 2), np.nan, dtype=np.float32)
    in_path = np.zeros(R, dtype=bool)

    for r in range(R):
        obs, _ = env.reset(seed=int(rng.integers(2**31 - 1)))
        cmd.reset(START)
        in_path[r] = r % 2 == 0
        pillars = spawn_pillars(env, rng, in_path=bool(in_path[r]))
        pillars_meta[r, : len(pillars)] = pillars
        act_id[r], seg[r] = _schedule(rng, L, passive=(r % 3 == 2))

        state = obs[0]
        for t in range(L):
            frames[r, t] = grab_frame(env)
            pos[r, t] = state[0:3]
            dists[r, t] = nearest_planar(state[0:2], pillars)
            v_cmd = ACTION_VECS[act_id[r, t]]
            actions[r, t] = v_cmd
            obs, _, _, _, _ = env.step(cmd.rpm(state, v_cmd).reshape(1, 4))
            state = obs[0]
        held = sorted({ACTION_NAMES[i] for i in act_id[r][seg[r] > 0]})
        print(
            f"  rollout {r + 1}/{R} ({'in-path' if in_path[r] else 'clear'}, "
            f"{'passive' if seg[r].max() == 0 else '+'.join(held)})"
        )

    env.close()
    return {
        "frames": frames,
        "actions": actions,
        "act_id": act_id,
        "seg": seg,
        "dists": dists,
        "pos": pos,
        "pillars": pillars_meta,
        "in_path": in_path,
        "horizons": np.array(HORIZONS, dtype=np.int16),
        "a_norm": A_NORM,
        "danger_r": np.float32(DANGER_R),
    }


def window_valid(seg_row, t: int, k: int) -> bool:
    """True when the command really was held over [t, t+k]: the window fits in
    the rollout and stays inside one held segment."""
    return t + k < len(seg_row) and seg_row[t] == seg_row[t + k]


def counterfactual_labels(data: dict) -> tuple:
    """The simulator's counterfactual oracle: for every frame and every candidate
    command, would holding it get dangerously close within each horizon?

    Straight-line kinematics through the stored pillar layout (an approximation:
    no PID transient — stated, and symmetric across candidates, so rankings
    survive). Returns (labels, visible):
      labels  uint8 (R, L, n_actions, n_horizons)
      visible uint8 (R, L, n_actions) — 1 when the label is *answerable from
              this frame*: either it is negative ("see nothing -> safe"), or
              the threatening pillar sits inside the camera FOV. A single-frame
              model cannot know about a pillar beside or behind it, so training
              or grading it on those labels would only teach noise. (The real
              fix is memory or yaw-aligned flight — see the honest notes.)

    Valid at *every* step, because it never needs the flown future — this is
    what densifies the action-conditioning supervision beyond the executed
    command."""
    R, L = data["frames"].shape[:2]
    taus = np.arange(H_MAX + 1) / CTRL_HZ  # (K+1,)
    cf = np.zeros((R, L, len(ACTION_VECS), len(HORIZONS)), dtype=np.uint8)
    vis = np.ones((R, L, len(ACTION_VECS)), dtype=np.uint8)
    cos_fov = np.cos(np.radians(FOV_HALF_DEG))
    for r in range(R):
        pil = data["pillars"][r]
        pil = pil[~np.isnan(pil[:, 0])]
        if not len(pil):
            continue
        p0 = data["pos"][r, :, :2]  # (L, 2)
        for i, v in enumerate(ACTION_VECS):
            # paths: (L, K+1, 2) -> distances to every pillar: (L, K+1, P)
            path = p0[:, None, :] + taus[None, :, None] * v[:2]
            d = np.linalg.norm(path[:, :, None, :] - pil[None, None], axis=3)
            for j, k in enumerate(HORIZONS):
                cf[r, :, i, j] = (d[:, : k + 1].min(axis=(1, 2)) < DANGER_R).astype(
                    np.uint8
                )
            # visibility of the threat (camera looks along +x, yaw held at 0):
            # a positive label caused by an out-of-FOV pillar is unanswerable
            threat = pil[d.min(axis=1).argmin(axis=1)]  # (L, 2)
            rel = threat - p0
            in_fov = rel[:, 0] > np.linalg.norm(rel, axis=1) * cos_fov
            vis[r, :, i] = np.where(cf[r, :, i].any(axis=1) & ~in_fov, 0, 1)
    return cf, vis


def as_pairs(data: dict, k: int) -> dict:
    """Slice the sequence format into single-horizon (X, Xk, A, c) triples —
    only windows where the command was genuinely held for all k steps."""
    F, A, D = data["frames"], data["actions"], data["dists"]
    R, L = F.shape[:2]
    X, Xk, Aout, c = [], [], [], []
    for r in range(R):
        for t in range(L - k):
            if not window_valid(data["seg"][r], t, k):
                continue
            X.append(F[r, t])
            Xk.append(F[r, t + k])
            Aout.append(A[r, t] / A_NORM)
            c.append(1.0 if float(D[r, t : t + k + 1].min()) < DANGER_R else 0.0)
    return {
        "X": np.array(X, dtype=np.float32) / 255.0,
        "Xk": np.array(Xk, dtype=np.float32) / 255.0,
        "A": np.array(Aout, dtype=np.float32),
        "c": np.array(c, dtype=np.float32),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=32)
    ap.add_argument("--len", dest="length", type=int, default=120)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n_roll, length = (10, 100) if args.selftest else (args.rollouts, args.length)

    print(f"[INFO] flying {n_roll} intervention rollouts x {length} steps ...")
    data = gen(n_roll, length, seed=args.seed)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, **data)

    rates = {}
    for k in HORIZONS:
        pairs = as_pairs(data, k)
        rates[k] = (len(pairs["c"]), float(pairs["c"].mean()))
    rate_str = ", ".join(f"k={k}: n={n} pos={p:.2f}" for k, (n, p) in rates.items())
    n_seg = int(sum(data["seg"][r].max() for r in range(n_roll)))
    held = sorted({ACTION_NAMES[i] for r in range(n_roll) for i in data["act_id"][r]})
    print(
        f"WM-DATA OK: {n_roll} rollouts x {length} steps @ {CTRL_HZ} Hz, "
        f"{n_seg} held intervention segments, labels [{rate_str}], saved {OUT}"
    )
    print(f"  commands held: {held}")

    if args.selftest:
        assert data["frames"].dtype == np.uint8, "frames must be uint8"
        assert data["frames"].shape[2:] == (IMG_RES, IMG_RES, 3), "bad frame shape"
        # the v1 bug guard: every rollout must really restart at START
        drift = np.abs(data["pos"][:, 0, :] - START).max()
        assert drift < 0.1, f"rollouts do not reset to START (drift {drift:.2f} m)"
        # commands are commanded, not measured: they must live on the action set
        assert np.abs(data["actions"]).max() <= np.abs(ACTION_VECS).max() + 1e-6
        assert n_seg >= n_roll, "too few held segments for counterfactual contrast"
        assert len(held) >= 4, f"too little action diversity ({held})"
        for k, (n, p) in rates.items():
            assert n > 0, f"no valid windows at k={k}"
            assert 0.03 < p < 0.97, f"labels too imbalanced at k={k} ({p:.2f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
