"""
Lesson 29 (step 6) — learn the policy: RL over the world model's eyes
=====================================================================
Step 4 ended on a measured verdict: the model's rankings are perfect
(veer-ranking 1.00) and the hand-crafted cost function is the bottleneck —
eight tuned configurations each fixed one failure mode and exposed the next,
and the cluttered courses kept a 16 % crash tail. This step does what that
verdict asks: **stop tuning the cost, learn it.**

The recipe is Lesson 19's PPO, pointed at Lesson 29's world model:

  * **Observation** — not pixels, and not privileged pillar positions: the
    world model's own outputs. For each of the five candidate commands, the
    8 collision probabilities (4 horizons x warn/crit rings), plus the drone's
    own y and cruise speed and the previous command — 47 numbers per decision.
  * **Memory** — the last 12 decisions of that vector, stacked (~1 s of
    history at 12 Hz). A pillar that slides out of the 60° FOV stays in the
    observation for a second — the "tiny GRU" idea in its simplest honest
    form (an action/percept buffer, the same trick Lesson 19's base env uses
    for actions). No new dependency.
  * **Actions** — the same five-command menu the hand planner used
    (climb stays off: it games the planar labels).
  * **Reward** — Lesson 19's shape, unchanged in spirit: progress toward the
    goal line, a small time cost, a crash penalty, a goal bonus. No hand-tuned
    danger weights anywhere — that is the point.

Training randomizes what the policy must survive: cruise speed (0.6–1.6 m/s)
and course layout (mostly threatened, some clear) every episode. The learned
policy then drops into the *same* harnesses as every other policy in this
lesson (`run_episode`, the 4b scoreboard, the 4c sweep), so the comparison is
apples to apples.

Run:
  python lessons/29_world_model/learn_policy.py --timesteps 300000   # train (long!)
  python lessons/29_world_model/learn_policy.py --eval               # compare policies
  python lessons/29_world_model/learn_policy.py --selftest           # tiny, asserts
Saves output/ppo_wm_policy.zip (git-ignored). Like Lesson 19, the real
training run is a manual job, not a CI smoke test.
"""

import argparse
import os
import sys
from collections import deque

import gymnasium as gym
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from gen_wm_dataset import (  # noqa: E402
    ACTION_VECS,
    COLLISION_R,
    FORWARD,
    VelCommander,
    grab_frame,
    make_ctrl,
    make_env,
    nearest_planar,
    spawn_pillars,
)
from train_world_model import load_model  # noqa: E402
from wm_closed_loop import (  # noqa: E402
    DECIDE_EVERY,
    GOAL_X,
    TMAX,
    ReactivePolicy,
    WMPolicy,
    _frame_tensor,
    load_or_train,
    run_episode,
)

HISTORY = 12  # decisions of memory (~1 s @ 12 Hz) — the poor man's GRU
SPEED_RANGE = (0.75, 2.0)  # per-episode cruise factor, same envelope as the data
POLICY_ZIP = os.path.join(HERE, "output", "ppo_wm_policy.zip")


def _menu(meta):
    """The five-command menu (climb off, as in WMPolicy) -> original ids."""
    names = list(meta["action_names"])
    return [i for i, n in enumerate(names) if n != "climb"]


class ObsBuilder:
    """One decision's observation: the world model's 8 collision probabilities
    per candidate command + own y + cruise factor + previous command one-hot,
    stacked over the last HISTORY decisions. Shared verbatim by the training
    env and the deployed LearnedPolicy, so train and fly see the same thing."""

    def __init__(self, enc, pred, cheads, meta, speed: float):
        self.enc, self.pred, self.cheads = enc, pred, cheads
        self.ids = _menu(meta)
        vecs = float(speed) * np.array(meta["action_vecs"], dtype=np.float32)
        a_norm = np.array(meta["a_norm"], dtype=np.float32)
        self.cands = torch.tensor(vecs[self.ids] / a_norm)
        self.speed = float(speed)
        self.n_act = len(self.ids)
        self.per_step = self.n_act * 8 + 2 + self.n_act  # probs + y,speed + prev
        self.hist = deque(maxlen=HISTORY)
        self.reset()

    def reset(self) -> None:
        self.hist.clear()
        for _ in range(HISTORY):
            self.hist.append(np.zeros(self.per_step, dtype=np.float32))

    def push(self, frame: np.ndarray, y: float, prev_menu_idx: int) -> np.ndarray:
        with torch.no_grad():
            z = self.enc(_frame_tensor(frame))
            z_hat = self.pred(z.expand(len(self.cands), -1), self.cands)
            p = torch.sigmoid(self.cheads(z_hat)).numpy()  # (n_act, H, 2)
        prev = np.zeros(self.n_act, dtype=np.float32)
        prev[prev_menu_idx] = 1.0
        step = np.concatenate(
            [
                p.reshape(-1),
                np.array([y / 2.5, self.speed / SPEED_RANGE[1]], dtype=np.float32),
                prev,
            ]
        ).astype(np.float32)
        self.hist.append(step)
        return np.concatenate(self.hist)


class WMPolicyEnv(gym.Env):
    """Gymnasium wrapper around the lesson's own closed-loop harness: the sim
    steps at 48 Hz under the PID VelCommander, the agent decides at 12 Hz, and
    everything the agent sees comes from the camera through the world model —
    pillar positions only stage and score, exactly like `run_episode`."""

    metadata = {"render_modes": []}

    def __init__(self, seed0: int = 0):
        super().__init__()
        self.env = make_env()
        self.enc, self.pred, self.cheads, self.nhead, self.meta = load_model()
        self.rng = np.random.default_rng(seed0)
        self.obs_dim = None
        self.ob = None
        probe = ObsBuilder(self.enc, self.pred, self.cheads, self.meta, 1.0)
        self.obs_dim = probe.per_step * HISTORY
        self.observation_space = gym.spaces.Box(
            low=-np.inf, high=np.inf, shape=(self.obs_dim,), dtype=np.float32
        )
        self.action_space = gym.spaces.Discrete(probe.n_act)
        self.max_decisions = TMAX // DECIDE_EVERY

    def reset(self, seed=None, options=None):
        if seed is not None:
            self.rng = np.random.default_rng(seed)
        scenario = int(self.rng.integers(2**31 - 1))
        obs, _ = self.env.reset(seed=scenario)
        self.cmd = VelCommander(make_ctrl(), self.env.CTRL_TIMESTEP)
        self.cmd.reset(obs[0][0:3])
        rng = np.random.default_rng(scenario)
        # mostly threatened, some clear — the distribution the tail lives in
        self.pillars = spawn_pillars(
            self.env, rng, in_path=bool(self.rng.random() < 0.8)
        )
        speed = float(self.rng.uniform(*SPEED_RANGE))
        self.ob = ObsBuilder(self.enc, self.pred, self.cheads, self.meta, speed)
        self.vecs = speed * ACTION_VECS
        self.state = obs[0]
        self.prev_x = float(self.state[0])
        self.decisions = 0
        return self.ob.push(grab_frame(self.env), float(self.state[1]), 0), {}

    def step(self, action: int):
        a_id = self.ob.ids[int(action)]
        for _ in range(DECIDE_EVERY):  # the PID flies 4 control steps per decision
            rpm = self.cmd.rpm(self.state, self.vecs[a_id])
            obs, _, _, _, _ = self.env.step(rpm.reshape(1, 4))
            self.state = obs[0]
        self.decisions += 1
        x, y = float(self.state[0]), float(self.state[1])
        d = nearest_planar(self.state[0:2], self.pillars)

        # Lesson 19's reward shape: progress, small time cost, crash, goal —
        # and deliberately no danger-shaping term (that is what we learn)
        reward = 25.0 * (x - self.prev_x) - 0.02
        self.prev_x = x
        terminated, truncated = False, False
        if d < COLLISION_R:
            reward -= 30.0
            terminated = True
        elif x >= GOAL_X:
            reward += 50.0
            terminated = True
        elif abs(y) > 2.4 or self.decisions >= self.max_decisions:
            truncated = True

        next_obs = self.ob.push(grab_frame(self.env), y, int(action))
        return next_obs, float(reward), terminated, truncated, {}

    def close(self):
        self.env.close()


class LearnedPolicy:
    """The trained PPO policy behind the same interface as WMPolicy /
    ReactivePolicy, so `run_episode`, the 4b scoreboard and the 4c sweep can
    fly it unchanged. Vision only: frames -> world model -> stacked history ->
    network -> one of five commands."""

    def __init__(self, model, enc, pred, cheads, meta, speed: float = 1.0):
        self.model = model
        self.ob = ObsBuilder(enc, pred, cheads, meta, speed)
        self.prev = 0  # menu index of "forward"
        self.i_fwd = self.ob.ids.index(FORWARD)

    def begin(self, pillars) -> None:
        del pillars  # vision only — same rule as WMPolicy
        self.ob.reset()
        self.prev = self.i_fwd

    def decide(self, frame: np.ndarray, state: np.ndarray) -> int:
        obs = self.ob.push(frame, float(state[1]), self.prev)
        action, _ = self.model.predict(obs, deterministic=True)
        self.prev = int(action)
        return self.ob.ids[self.prev]


def train(timesteps: int, seed0: int = 0):
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    env = make_vec_env(lambda: WMPolicyEnv(seed0=seed0), n_envs=1)
    model = PPO("MlpPolicy", env, ent_coef=0.01, verbose=0)
    model.learn(total_timesteps=timesteps)
    os.makedirs(os.path.dirname(POLICY_ZIP), exist_ok=True)
    model.save(POLICY_ZIP)
    env.close()
    return model


def compare(n_seeds: int, seed0: int = 1000) -> dict:
    """Fly the learned policy against the hand-crafted MPC and the reactive
    baseline on identical cluttered courses (the 4b distribution, where the
    16 % tail lives), plus the 4c speed endpoints on single-pillar courses."""
    from stable_baselines3 import PPO

    model = PPO.load(POLICY_ZIP)
    enc, pred, cheads, nhead, meta = load_or_train(device="cpu")
    env = make_env()

    def fly(policy_fn, **kw):
        crash, clear = 0, []
        for i in range(n_seeds):
            run = run_episode(env, policy_fn(kw.get("speed", 1.0)), seed0 + i, **kw)
            crash += int(run["crashed"])
            clear.append(run["min_clear"])
        return crash / n_seeds, float(np.mean(clear))

    mk = {
        "reactive": lambda s: ReactivePolicy(enc, nhead),
        "wm-mpc": lambda s: WMPolicy(enc, pred, cheads, meta, speed=s),
        "learned": lambda s: LearnedPolicy(model, enc, pred, cheads, meta, speed=s),
    }
    out = {}
    for name, fn in mk.items():
        out[name] = {"cluttered": fly(fn, in_path=True)}
    for name, fn in mk.items():
        out[name]["fast"] = fly(fn, in_path=True, solo=True, speed=2.0)
    env.close()
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--timesteps", type=int, default=300_000)
    ap.add_argument("--eval", action="store_true")
    ap.add_argument("--seeds", type=int, default=40)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        env = WMPolicyEnv(seed0=7)
        obs, _ = env.reset()
        n_act = env.action_space.n
        per = env.obs_dim // HISTORY
        assert n_act == 5, f"menu should be 5 commands, got {n_act}"
        assert per == 5 * 8 + 2 + 5, f"per-step obs dim off ({per})"
        assert obs.shape == (env.obs_dim,), "stacked obs shape off"
        obs2, r, term, trunc, _ = env.step(0)
        assert obs2.shape == obs.shape and np.isfinite(r), "step broken"
        env.close()
        train(1500, seed0=7)  # smoke-train: wiring, not skill (Lesson 19 style)
        assert os.path.exists(POLICY_ZIP), "policy zip not saved"
        print(
            f"LEARN-POLICY OK: obs={HISTORY}x{per} (8 world-model probs x 5 "
            f"commands + y + speed + prev), 5 actions, smoke-trained 1500 steps, "
            f"saved {POLICY_ZIP}"
        )
        return

    if not args.eval:
        print(f"[INFO] PPO over world-model outputs, {args.timesteps} steps ...")
        train(args.timesteps)
        print(f"[INFO] saved {POLICY_ZIP}")

    res = compare(args.seeds)
    r, w, le = res["reactive"], res["wm-mpc"], res["learned"]
    print(
        f"LEARNED-POLICY OK: {args.seeds} cluttered courses @ 0.8 m/s — crash "
        f"reactive {r['cluttered'][0]:.0%} / wm-mpc {w['cluttered'][0]:.0%} / "
        f"learned {le['cluttered'][0]:.0%} (clearance "
        f"{r['cluttered'][1]:.2f} / {w['cluttered'][1]:.2f} / "
        f"{le['cluttered'][1]:.2f} m)\n"
        f"  single-pillar @ 1.6 m/s — crash reactive {r['fast'][0]:.0%} / "
        f"wm-mpc {w['fast'][0]:.0%} / learned {le['fast'][0]:.0%} — the cost "
        f"function is learned, the world model is the same"
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
