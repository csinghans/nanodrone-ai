"""
Lesson 18 (step 2) — dead-reckon a trajectory from learned flow
===============================================================
Fly a loop and estimate the path using ONLY the flow net's frame-to-frame
displacements (no privileged position) — integrating them like a visual
odometer. The estimate drifts (every odometer does); plotting it against the
true path shows how much, and why a real drone fuses this with other sensors.

Run (after train_flow.py):
  python lessons/18_flow/odom_demo.py            # saves output/odom.png
  python lessons/18_flow/odom_demo.py --selftest  # asserts (local)
"""

import math
import os
import sys

import numpy as np
import torch

try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from train_flow import (
        DISP_SCALE,
        MODEL,
        WIN,
        FlowNet,
        _scatter_floor,
        down_view,
    )
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 18's flow net:", exc)
    sys.exit(1)

OUT_PNG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "odom.png")
# a square-ish loop: (body vx, vy, segment seconds)
LEGS = [(0.6, 0.0, 2.0), (0.0, 0.6, 2.0), (-0.6, 0.0, 2.0), (0.0, -0.6, 2.0)]


def run(gui: bool):
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics

    net = FlowNet()
    net.load_state_dict(torch.load(MODEL, map_location="cpu"))
    net.eval()

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0.0, 0.0, 1.0]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    _scatter_floor(env.CLIENT, np.random.default_rng(0))
    dt = env.CTRL_TIMESTEP
    action = np.zeros((1, 4))
    target = np.array([0.0, 0.0, 1.0])
    yaw = 0.0
    obs = None
    for _ in range(20):  # settle
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=dt, state=obs[0], target_pos=target
        )

    est = np.array([obs[0][0], obs[0][1]])  # estimate starts at the true start
    est_yaw = 0.0
    true_path, est_path = [tuple(est)], [tuple(est)]
    g_prev = down_view(env.CLIENT, obs[0][0:3], float(obs[0][9]))
    k = 0
    for vx, vy, secs in LEGS:
        for _ in range(int(secs / dt)):
            c, s = math.cos(yaw), math.sin(yaw)
            target[0] = float(np.clip(target[0] + (vx * c - vy * s) * dt, -2.5, 2.5))
            target[1] = float(np.clip(target[1] + (vx * s + vy * c) * dt, -2.5, 2.5))
            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt, state=obs[0], target_pos=target
            )
            k += 1
            if k % WIN == 0:  # one odometry update per window
                g_cur = down_view(env.CLIENT, obs[0][0:3], float(obs[0][9]))
                with torch.no_grad():
                    x = torch.tensor(np.stack([g_prev, g_cur])[None]).float()
                    dx, dy, dyaw = (net(x)[0].numpy() * DISP_SCALE).tolist()
                ec, es = math.cos(est_yaw), math.sin(est_yaw)  # body -> world
                est[0] += dx * ec - dy * es
                est[1] += dx * es + dy * ec
                est_yaw += dyaw
                est_path.append(tuple(est))
                true_path.append((float(obs[0][0]), float(obs[0][1])))
                g_prev = g_cur
    try:
        env.close()
    except Exception:  # pragma: no cover
        pass
    drift = float(np.linalg.norm(np.array(est_path[-1]) - np.array(true_path[-1])))
    tp = np.array(true_path)
    path_len = float(np.sum(np.linalg.norm(np.diff(tp, axis=0), axis=1)))
    return true_path, est_path, drift, path_len


def main() -> None:
    selftest = "--selftest" in sys.argv
    if not os.path.exists(MODEL):
        raise SystemExit(f"No model at {MODEL}. Run train_flow.py first.")
    true_path, est_path, drift, path_len = run(
        gui=not (selftest or "--headless" in sys.argv)
    )

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 5))
    tp, ep = np.array(true_path), np.array(est_path)
    ax.plot(tp[:, 0], tp[:, 1], "g.-", lw=1.5, label="true path")
    ax.plot(ep[:, 0], ep[:, 1], "r.--", lw=1.5, label="flow odometry (estimated)")
    ax.set_aspect("equal")
    ax.set_title(f"Visual odometry — final drift {drift:.2f} m")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.legend(fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, dpi=90)
    plt.close(fig)

    ratio = drift / max(path_len, 1e-6)
    print(
        f"ODOM OK: {len(est_path)} flow updates over {path_len:.1f} m path, "
        f"final drift {drift:.2f} m ({100 * ratio:.0f}% of distance), saved {OUT_PNG}"
    )
    if selftest:
        assert os.path.exists(OUT_PNG), "no trajectory plot written"
        # drift is expected (every odometer drifts) — assert it stays a small
        # fraction of the distance flown, i.e. it tracked the loop, not wandered.
        assert ratio < 0.35, f"odometry drift too large ({100 * ratio:.0f}% of path)"


if __name__ == "__main__":
    main()
    sys.exit(0)
