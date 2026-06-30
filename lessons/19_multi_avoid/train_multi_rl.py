"""
Lesson 19 — train avoidance over RANDOM layouts (PPO + perception in the obs)
=============================================================================
Like Lesson 3's RL, but the obstacle course is randomized every episode and the
nearest-obstacle vector is part of the observation, so the policy must generalize
rather than memorize one detour.

Real RL training is a long run (hundreds of k steps) — like Lesson 3's train_rl,
it's a manual job, not a CI smoke test. So:
  python lessons/19_multi_avoid/train_multi_rl.py --timesteps 300000   # real
  python lessons/19_multi_avoid/train_multi_rl.py --selftest           # smoke (local)
The self-test only proves the env + augmented observation + PPO loop are wired
correctly and a policy rollout runs — not that the (barely-trained) policy is good.
"""

import argparse
import os
import sys

from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from multi_avoid_aviary import MultiAvoidAviary  # noqa: E402

_L3 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "03_autonomy_ai"
)
sys.path.insert(0, _L3)
from avoid_aviary import AvoidAviary  # noqa: E402

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "ppo_multi.zip"
)


def evaluate(model, episodes: int) -> int:
    env = MultiAvoidAviary(seed=123)
    success = 0
    for _ in range(episodes):
        obs, _ = env.reset()
        done, steps, info = False, 0, {}
        while not done and steps < 400:
            action, _ = model.predict(obs, deterministic=True)
            obs, _, term, trunc, info = env.step(action)
            done = term or trunc
            steps += 1
        success += int(info.get("is_success", False))
    env.close()
    return success


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=300_000)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    steps = 2000 if args.selftest else args.timesteps

    # the augmented observation must be exactly 2 wider than the base env's
    base_dim = AvoidAviary().observation_space.shape[-1]
    multi_dim = MultiAvoidAviary().observation_space.shape[-1]

    env = make_vec_env(MultiAvoidAviary, n_envs=1)
    model = PPO("MlpPolicy", env, ent_coef=0.01, verbose=0)
    model.learn(total_timesteps=steps)
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    model.save(MODEL_PATH)

    episodes = 4 if args.selftest else 10
    success = evaluate(model, episodes)
    print(
        f"MULTI-AVOID OK: obs adds obstacle dims ({base_dim}->{multi_dim}), "
        f"trained {steps} steps, eval {success}/{episodes} reached goal "
        f"{'(smoke — train longer for a good policy)' if args.selftest else ''}"
    )
    if args.selftest:
        assert multi_dim == base_dim + 2, "obstacle info not in the observation"
        assert os.path.exists(MODEL_PATH), "policy was not saved"


if __name__ == "__main__":
    main()
    sys.exit(0)
