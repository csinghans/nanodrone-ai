"""
Lesson 3 (Route A) — train an obstacle-avoidance policy with PPO
================================================================
This is the main route: reinforcement learning. We hand the AvoidAviary
environment to Stable-Baselines3's PPO and let it discover, by trial and error,
how to fly from START to GOAL around the pillar. No hand-written rules for *how*
to avoid -- only the reward that says *what* good behaviour looks like.

Usage:
  python train_rl.py                      # train (default 200k steps) + evaluate
  python train_rl.py --timesteps 50000    # quicker, less reliable
  python train_rl.py --eval-only --gui    # watch the saved policy fly (window)

The model is saved to output/ppo_avoid.zip (git-ignored).
"""

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from avoid_aviary import AvoidAviary  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402
from stable_baselines3.common.env_util import make_vec_env  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "output", "ppo_avoid.zip")


def evaluate(model, episodes: int = 10, gui: bool = False) -> None:
    """Run the policy and report how often it reaches the goal without crashing.

    Also saves a top-down plot of the first episode's path to output/.
    """
    env = AvoidAviary(gui=gui)
    successes, crashes = 0, 0
    first_path = []
    for ep in range(episodes):
        obs, _ = env.reset(seed=1000 + ep)
        min_obs_dist = float("inf")
        done = False
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, _r, term, trunc, info = env.step(action)
            pos = env._getDroneStateVector(0)[0:3]
            if ep == 0:
                first_path.append(pos[0:2].copy())
            min_obs_dist = min(min_obs_dist, env._planar_dist(pos, env.OBSTACLE_POS))
            done = term or trunc
        if info.get("is_success"):
            successes += 1
        elif min_obs_dist < env.COLLISION_R:
            crashes += 1
    env.close()
    print(
        f"[EVAL] {episodes} episodes: "
        f"{successes} reached goal, {crashes} crashed "
        f"(success rate {100 * successes / episodes:.0f}%)."
    )
    _save_trajectory_plot(np.array(first_path))


def _save_trajectory_plot(path_xy: np.ndarray) -> None:
    """Top-down view: the learned path arcing around the pillar to the goal."""
    import matplotlib

    matplotlib.use("Agg")  # no display needed
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(5, 4))
    ax.plot(path_xy[:, 0], path_xy[:, 1], "-", color="tab:blue", label="drone path")
    ax.plot(*AvoidAviary.START_POS[0:2], "go", markersize=10, label="start")
    ax.plot(*AvoidAviary.GOAL_POS[0:2], "g*", markersize=16, label="goal")
    ax.add_patch(
        plt.Circle(
            AvoidAviary.OBSTACLE_POS[0:2],
            AvoidAviary.COLLISION_R,
            color="red",
            alpha=0.5,
            label="obstacle",
        )
    )
    ax.set_aspect("equal")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("Learned obstacle-avoidance path (top-down)")
    ax.legend(loc="best", fontsize=8)
    out = os.path.join(os.path.dirname(__file__), "output", "trajectory.png")
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    print(f"[EVAL] saved path plot to {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=200_000)
    parser.add_argument("--eval-episodes", type=int, default=10)
    parser.add_argument("--eval-only", action="store_true")
    parser.add_argument("--gui", action="store_true")
    args = parser.parse_args()

    if args.eval_only:
        if not os.path.exists(MODEL_PATH):
            print(f"No model at {MODEL_PATH}. Train first (run without --eval-only).")
            sys.exit(1)
        model = PPO.load(MODEL_PATH)
        evaluate(model, episodes=args.eval_episodes, gui=args.gui)
        return

    train_env = make_vec_env(AvoidAviary, n_envs=1)
    print("[INFO] action space:", train_env.action_space)
    print("[INFO] observation space:", train_env.observation_space)

    # ent_coef > 0 keeps the policy exploring long enough to stumble onto the
    # sideways detour (without it, PPO collapses to "hover in place").
    model = PPO("MlpPolicy", train_env, ent_coef=0.01, verbose=1)
    model.learn(total_timesteps=args.timesteps, progress_bar=False)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)
    print(f"[INFO] saved model to {MODEL_PATH}")

    evaluate(model, episodes=args.eval_episodes, gui=args.gui)


if __name__ == "__main__":
    main()
