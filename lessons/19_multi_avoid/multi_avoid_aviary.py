"""
Lesson 19 — a harder, randomized obstacle course (perception in the observation)
================================================================================
Lesson 3's RL flew around ONE pillar in a FIXED spot — so the drone's own
position was enough to memorize the detour. Real avoidance is many obstacles,
different every time. This subclass randomizes 1-3 pillars each episode AND feeds
the nearest obstacle's relative position into the observation, so the policy can
*generalize* instead of memorizing. (That's the missing piece Lesson 3's own
comments call out.) It's also where Lesson 17's depth could supply that obstacle
cue on real hardware.
"""

import os
import sys

import numpy as np
import pybullet as p
from gymnasium import spaces

_L3 = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "03_autonomy_ai"
)
sys.path.insert(0, _L3)
from avoid_aviary import AvoidAviary  # noqa: E402


class MultiAvoidAviary(AvoidAviary):
    """1-3 random pillars per episode; nearest-obstacle vector added to the obs."""

    def __init__(self, n_min: int = 1, n_max: int = 3, seed: int = 0, **kw):
        self._n_min, self._n_max = n_min, n_max
        self._rng = np.random.default_rng(seed)
        self._obs_xy: list = []
        super().__init__(**kw)

    # -- random multi-pillar layout --
    def _spawn_obstacle(self) -> None:
        self._obs_xy = []
        n = int(self._rng.integers(self._n_min, self._n_max + 1))
        for _ in range(n):
            x = float(self._rng.uniform(0.4, 1.1))
            y = float(self._rng.uniform(-0.6, 0.6))
            half = [0.15, 0.15, 1.0]
            col = p.createCollisionShape(
                p.GEOM_BOX, halfExtents=half, physicsClientId=self.CLIENT
            )
            vis = p.createVisualShape(
                p.GEOM_BOX,
                halfExtents=half,
                rgbaColor=[1, 0, 0, 1],
                physicsClientId=self.CLIENT,
            )
            p.createMultiBody(
                baseMass=0,
                baseCollisionShapeIndex=col,
                baseVisualShapeIndex=vis,
                basePosition=[x, y, 1.0],
                physicsClientId=self.CLIENT,
            )
            self._obs_xy.append(np.array([x, y]))

    def _nearest(self, pos):
        """Nearest pillar centre and its planar distance from pos. Before the
        first spawn (e.g. during env __init__) report a far placeholder."""
        if not self._obs_xy:
            return np.array([9.0, 9.0]), 9.0
        best, best_d = self._obs_xy[0], 1e9
        for o in self._obs_xy:
            d = float(np.linalg.norm(pos[0:2] - o))
            if d < best_d:
                best, best_d = o, d
        return best, best_d

    # -- reward / termination use the nearest pillar --
    def _computeReward(self):
        pos = self._getDroneStateVector(0)[0:3]
        d_goal = float(np.linalg.norm(self.GOAL_POS - pos))
        _, d_obs = self._nearest(pos)
        progress = self._prev_d_goal - d_goal
        self._prev_d_goal = d_goal
        reward = 25.0 * progress - 0.02
        if d_obs < self.COLLISION_R:
            reward -= 30.0
        if d_goal < self.GOAL_R:
            reward += 50.0
        return reward

    def _computeTruncated(self):
        state = self._getDroneStateVector(0)
        pos = state[0:3]
        if self._nearest(pos)[1] < self.COLLISION_R:
            return True
        if abs(pos[0]) > 2.5 or abs(pos[1]) > 2.0 or pos[2] > 2.0 or pos[2] < 0.2:
            return True
        if abs(state[7]) > 0.5 or abs(state[8]) > 0.5:
            return True
        if self.step_counter / self.PYB_FREQ > self.EPISODE_LEN_SEC:
            return True
        return False

    # -- observation: base KIN(+action buffer) PLUS nearest-obstacle (dx, dy) --
    def _observationSpace(self):
        base = super()._observationSpace()
        extra_lo = np.full((self.NUM_DRONES, 2), -np.inf)
        extra_hi = np.full((self.NUM_DRONES, 2), np.inf)
        return spaces.Box(
            low=np.concatenate([base.low, extra_lo], axis=1).astype(np.float32),
            high=np.concatenate([base.high, extra_hi], axis=1).astype(np.float32),
            dtype=np.float32,
        )

    def _computeObs(self):
        base = super()._computeObs()
        pos = self._getDroneStateVector(0)[0:3]
        near, _ = self._nearest(pos)
        rel = (near - pos[0:2]).reshape(1, 2)
        return np.concatenate([base, rel], axis=1).astype(np.float32)
