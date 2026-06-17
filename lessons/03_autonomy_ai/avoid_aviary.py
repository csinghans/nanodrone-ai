"""
Lesson 3 (Route A) — the RL environment
=======================================
A custom gym-pybullet-drones environment where the drone must fly from a START
to a GOAL while avoiding a tall obstacle in between. We subclass BaseRLAviary
(which gives us the physics, the kinematic observation, and a velocity action)
and only define the *task*: the reward and the episode-ending conditions.

Key simplification: the layout (start / obstacle / goal) is FIXED every episode.
That way the kinematic observation -- the drone's own position and velocity --
is enough for the policy to learn the detour. (Randomizing the layout would
require feeding the obstacle's position into the observation; see the README.)

The obstacle is a tall pillar (z from 0 to 2 m) so the drone cannot cheat by
flying over it -- it must go *around*, which is the whole point.
"""

import numpy as np
import pybullet as p
from gym_pybullet_drones.envs.BaseRLAviary import BaseRLAviary
from gym_pybullet_drones.utils.enums import (
    ActionType,
    DroneModel,
    ObservationType,
    Physics,
)


class AvoidAviary(BaseRLAviary):
    """Fly START -> GOAL around a fixed obstacle. Reward = progress toward the
    goal, a crash penalty on touching the pillar, and a bonus for arriving."""

    START_POS = np.array([0.0, 0.0, 1.0])
    OBSTACLE_POS = np.array([0.7, 0.0, 1.0])
    GOAL_POS = np.array([1.4, 0.0, 1.0])

    GOAL_R = 0.20  # within this distance of the goal -> success
    COLLISION_R = 0.22  # within this planar distance of the pillar -> crash

    def __init__(
        self,
        gui=False,
        record=False,
        obs: ObservationType = ObservationType.KIN,
        act: ActionType = ActionType.VEL,
        pyb_freq: int = 240,
        ctrl_freq: int = 30,
    ):
        self.EPISODE_LEN_SEC = 10
        self._obstacle_id = None
        # Distance to the goal on the previous step, for progress-based reward.
        self._prev_d_goal = float(np.linalg.norm(self.GOAL_POS - self.START_POS))
        super().__init__(
            drone_model=DroneModel.CF2X,
            num_drones=1,
            initial_xyzs=np.array([self.START_POS]),
            physics=Physics.PYB,
            pyb_freq=pyb_freq,
            ctrl_freq=ctrl_freq,
            gui=gui,
            record=record,
            obs=obs,
            act=act,
        )

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _planar_dist(a, b) -> float:
        return float(np.linalg.norm(a[0:2] - b[0:2]))

    def _spawn_obstacle(self) -> None:
        """Add the red pillar to the freshly-reset world."""
        half = [0.15, 0.15, 1.0]  # tall: spans z in [0, 2] -> can't fly over
        col = p.createCollisionShape(
            p.GEOM_BOX, halfExtents=half, physicsClientId=self.CLIENT
        )
        vis = p.createVisualShape(
            p.GEOM_BOX,
            halfExtents=half,
            rgbaColor=[1, 0, 0, 1],
            physicsClientId=self.CLIENT,
        )
        self._obstacle_id = p.createMultiBody(
            baseMass=0,  # static
            baseCollisionShapeIndex=col,
            baseVisualShapeIndex=vis,
            basePosition=self.OBSTACLE_POS.tolist(),
            physicsClientId=self.CLIENT,
        )

    # ------------------------------------------------------------------ gym API
    def reset(self, seed=None, options=None):
        obs, info = super().reset(seed=seed, options=options)
        self._spawn_obstacle()  # super().reset() wiped the world, so re-add it
        self._prev_d_goal = float(np.linalg.norm(self.GOAL_POS - self.START_POS))
        return obs, info

    def _computeReward(self):
        pos = self._getDroneStateVector(0)[0:3]
        d_goal = float(np.linalg.norm(self.GOAL_POS - pos))
        d_obs = self._planar_dist(pos, self.OBSTACLE_POS)

        # Progress reward: positive for moving *toward* the goal this step. This
        # dense signal is what makes navigation learnable -- absolute-distance
        # rewards let the policy settle for "park somewhere comfortable".
        progress = self._prev_d_goal - d_goal
        self._prev_d_goal = d_goal
        reward = 25.0 * progress
        reward -= 0.02  # tiny time penalty -> prefer reaching the goal sooner
        # NOTE: no wide repulsive barrier here -- it would punish the sideways
        # exploration the detour requires, trapping the policy in "don't move".
        # Hitting the pillar is handled as a crash (penalty + episode end below).
        if d_obs < self.COLLISION_R:  # crashed into the pillar
            reward -= 30.0
        if d_goal < self.GOAL_R:  # reached the goal
            reward += 50.0
        return reward

    def _computeTerminated(self):
        pos = self._getDroneStateVector(0)[0:3]
        return bool(np.linalg.norm(self.GOAL_POS - pos) < self.GOAL_R)

    def _computeTruncated(self):
        state = self._getDroneStateVector(0)
        pos = state[0:3]
        if self._planar_dist(pos, self.OBSTACLE_POS) < self.COLLISION_R:
            return True  # crashed into the pillar
        if abs(pos[0]) > 2.5 or abs(pos[1]) > 2.0 or pos[2] > 2.0 or pos[2] < 0.2:
            return True  # flew out of bounds
        if abs(state[7]) > 0.5 or abs(state[8]) > 0.5:
            return True  # tilted too far (about to flip)
        if self.step_counter / self.PYB_FREQ > self.EPISODE_LEN_SEC:
            return True  # ran out of time
        return False

    def _computeInfo(self):
        pos = self._getDroneStateVector(0)[0:3]
        d_goal = float(np.linalg.norm(self.GOAL_POS - pos))
        return {"d_goal": d_goal, "is_success": bool(d_goal < self.GOAL_R)}
