"""
Lesson 29 (step 1) — self-produce a *sequence* dataset for the world model
==========================================================================
Every earlier lesson learned a mapping from *one* frame (image -> bearing,
image -> depth). A world model is different: it learns how the world *changes*.
So the data is no longer single frames — it is short clips: "here is what I see
now (x_t), here is the action I took (a_t), and here is what I saw a moment later
(x_{t+k})." The signature move is unchanged — the labels are free, the simulator
hands them to us — but now the "label" is the future itself.

How we make it, honestly:
  * We really fly the drone forward through a field of pillars (no cheating with
    teleports), streaming the on-board camera every control step. Real ego-motion
    is exactly what a world model must learn to anticipate.
  * We then pair frame t with frame t+K to form (x_t, a_t, x_{t+k}) triples, where
    a_t is the drone's own velocity (vx, vy, vz, yaw-rate) at t.
  * The *privileged* extra: for each triple we also record whether the drone comes
    dangerously close to a pillar within the next K steps (planar distance <
    DANGER_R). That 0/1 flag is the free future-collision label the collision head
    learns in step 2 — anticipation, not reaction.

Note there is NO pixel target anywhere: step 2 predicts in *latent* space. This
file only stores raw frames + actions + the free danger flag.

Run:
  python lessons/29_world_model/gen_wm_dataset.py --rollouts 20 --len 60
  python lessons/29_world_model/gen_wm_dataset.py --selftest   # tiny, asserts (local)
Saves output/wm_dataset.npz (git-ignored).
"""

import argparse
import os
import sys

import numpy as np

IMG_RES = 64  # camera + network input (matches L3/L8/L17)
HORIZON_K = 8  # predict this many control steps ahead
DANGER_R = 0.7  # planar distance (m) that counts as "dangerously close" soon
A_SCALE = 1.0  # velocity scale used to normalise the action vector (~[-1, 1])
START = np.array([0.0, 0.0, 1.0])
LOOKAHEAD = 0.6  # carrot distance for the go-to-goal setpoint
OUT = os.path.join(os.path.dirname(__file__), "output", "wm_dataset.npz")


def _nearest_dist(pos_xy, pillars) -> float:
    """Planar distance from pos to the closest pillar centre (m)."""
    if not pillars:
        return 9.0
    return float(min(np.linalg.norm(pos_xy - np.array(pv)) for pv in pillars))


def _rollout(env, ctrl, p, rng, in_path: bool):
    """Fly one straight-ish forward pass through a fresh pillar layout, streaming
    (frame, velocity, nearest-pillar-distance) every control step.

    `in_path=True` drops a pillar into the forward corridor (positive samples);
    `in_path=False` pushes the pillars to the sides (negative samples). Returns
    (frames [L,64,64,3], vels [L,4], dists [L])."""
    # --- lay out 2-3 visual pillars (same style as L14a / L17) --------------
    pillars = []
    n = int(rng.integers(2, 4))
    for i in range(n):
        if in_path and i == 0:
            px, py = float(rng.uniform(0.7, 1.3)), float(rng.uniform(-0.15, 0.15))
        else:
            px, py = float(rng.uniform(0.9, 2.4)), float(rng.uniform(1.0, 1.5))
            py *= 1.0 if rng.random() < 0.5 else -1.0
        pillars.append((px, py))
    bodies = []
    for px, py in pillars:
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=0.18,
            length=1.4,
            rgbaColor=[0.80, 0.32, 0.22, 1],
            physicsClientId=env.CLIENT,
        )
        bodies.append(
            p.createMultiBody(
                baseMass=0,
                baseVisualShapeIndex=vis,
                basePosition=[px, py, 0.7],
                physicsClientId=env.CLIENT,
            )
        )

    goal = np.array([3.0, pillars[0][1] if in_path else 0.0, 1.0])
    frames, vels, dists = [], [], []
    action = np.zeros((1, 4))
    L = _rollout.length
    for _ in range(L):
        obs, _, _, _, _ = env.step(action)
        state = obs[0]
        pos = state[0:3]
        carrot = pos + LOOKAHEAD * _unit(goal - pos)
        carrot[2] = 1.0
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=state, target_pos=carrot
        )
        rgb, _dep, _seg = env._getDroneImages(0, segmentation=False)
        frames.append(rgb[:IMG_RES, :IMG_RES, :3].astype(np.float32) / 255.0)
        # velocity (10:13) + yaw-rate (15) -> the action the world model conditions on
        vels.append([state[10], state[11], state[12], state[15]])
        dists.append(_nearest_dist(pos[0:2], pillars))

    for b in bodies:
        p.removeBody(b, physicsClientId=env.CLIENT)
    return (
        np.array(frames, dtype=np.float32),
        np.array(vels, dtype=np.float32),
        np.array(dists, dtype=np.float32),
    )


_rollout.length = 60  # overwritten by main()/gen()


def _unit(v):
    n = float(np.linalg.norm(v))
    return v / n if n > 1e-6 else v


def gen(n_rollouts: int, length: int, seed: int = 0) -> dict:
    """Fly `n_rollouts` forward passes and slice them into (x_t, a_t, x_{t+k}, c)
    training triples. Returns a dict with keys X, Xk, A, c."""
    import pybullet as p
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    _rollout.length = length
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    env.IMG_RES = np.array([IMG_RES, IMG_RES])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    rng = np.random.default_rng(seed)

    X, Xk, A, c = [], [], [], []
    for r in range(n_rollouts):
        frames, vels, dists = _rollout(env, ctrl, p, rng, in_path=(r % 2 == 0))
        for t in range(len(frames) - HORIZON_K):
            X.append(frames[t])
            Xk.append(frames[t + HORIZON_K])
            A.append(vels[t] / A_SCALE)
            window = dists[t : t + HORIZON_K + 1]
            c.append(1.0 if float(window.min()) < DANGER_R else 0.0)
        print(
            f"  rollout {r + 1}/{n_rollouts} ({'in-path' if r % 2 == 0 else 'clear'})"
        )
    env.close()
    return {
        "X": np.array(X, dtype=np.float32),
        "Xk": np.array(Xk, dtype=np.float32),
        "A": np.array(A, dtype=np.float32),
        "c": np.array(c, dtype=np.float32),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rollouts", type=int, default=20)
    ap.add_argument("--len", dest="length", type=int, default=80)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    n_roll, length = (8, 60) if args.selftest else (args.rollouts, args.length)

    print(f"[INFO] flying {n_roll} rollouts x {length} steps ...")
    data = gen(n_roll, length)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(OUT, **data)

    n = len(data["c"])
    rate = float(data["c"].mean()) if n else 0.0
    print(
        f"WM-DATA OK: {n} seqs, horizon k={HORIZON_K} steps, collide-rate={rate:.2f}, "
        f"img={tuple(data['X'].shape[1:])}, action-dim={data['A'].shape[1]}, "
        f"saved {OUT}"
    )
    if args.selftest:
        assert n > 0, "no sequences produced"
        assert (
            0.05 < rate < 0.95
        ), f"labels too imbalanced for a classifier ({rate:.2f})"
        assert data["X"].shape[1:] == (IMG_RES, IMG_RES, 3), "bad frame shape"


if __name__ == "__main__":
    main()
    sys.exit(0)
