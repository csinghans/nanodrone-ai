"""A small multi-pillar obstacle course for Lesson 14a.

New for this lesson — *not* reused from Lesson 3, whose single pillar is wired
into the RL-only AvoidAviary. These are plain visual cylinders at known
positions, so we can check the map we build against the truth.
"""

import pybullet as p

# (x, y) world positions of the pillars — the ground truth the map is checked against.
PILLARS = [(1.5, 0.8), (-1.2, -1.0)]
PILLAR_R, PILLAR_H = 0.18, 1.4


def build_scene(client: int):
    """Drop the pillars into the world; return their (x, y) truth positions."""
    for x, y in PILLARS:
        vis = p.createVisualShape(
            p.GEOM_CYLINDER,
            radius=PILLAR_R,
            length=PILLAR_H,
            rgbaColor=[0.80, 0.32, 0.22, 1],
            physicsClientId=client,
        )
        p.createMultiBody(
            baseMass=0,
            baseVisualShapeIndex=vis,
            basePosition=[x, y, PILLAR_H / 2],
            physicsClientId=client,
        )
    return list(PILLARS)
