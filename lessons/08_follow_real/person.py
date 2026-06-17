"""A simple multi-colour 'person' (skin head, blue shirt, dark legs).

Deliberately NOT a single bright colour — the blue shirt even matches the
checkerboard floor — so Lesson 2's HSV threshold can't cleanly find it. That's
the whole reason Lesson 8 needs a learned detector instead of a colour rule.
"""

import math

import pybullet as p

HEAD_Z, TORSO_Z, LEGS_Z = 0.92, 0.55, 0.18


def build_person(client: int):
    """Return the body ids (head, torso, legs) of a little multi-colour figure."""
    head = p.createVisualShape(
        p.GEOM_SPHERE,
        radius=0.12,
        rgbaColor=[0.92, 0.76, 0.62, 1],
        physicsClientId=client,
    )
    torso = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[0.13, 0.09, 0.22],
        rgbaColor=[0.15, 0.35, 0.8, 1],
        physicsClientId=client,
    )
    legs = p.createVisualShape(
        p.GEOM_BOX,
        halfExtents=[0.11, 0.08, 0.18],
        rgbaColor=[0.2, 0.2, 0.25, 1],
        physicsClientId=client,
    )
    return tuple(
        p.createMultiBody(baseMass=0, baseVisualShapeIndex=v, physicsClientId=client)
        for v in (head, torso, legs)
    )


def move_person(ids, x: float, y: float, heading: float, client: int) -> None:
    """Place the person at (x, y) facing `heading` (radians, 0 = +x)."""
    head, torso, legs = ids
    quat = p.getQuaternionFromEuler([0, 0, heading])
    for body, z in ((head, HEAD_Z), (torso, TORSO_Z), (legs, LEGS_Z)):
        p.resetBasePositionAndOrientation(body, [x, y, z], quat, physicsClientId=client)


def true_bearing_deg(drone_pos, drone_yaw: float, px: float, py: float) -> float:
    """Ground-truth bearing of the person from the drone — the 'teacher' label.
    Matches nanodrone.world_point's convention (world +y -> negative bearing)."""
    theta = math.atan2(py - drone_pos[1], px - drone_pos[0])
    return math.degrees(drone_yaw - theta)
