"""Shared GUI niceties: hide the side panels so the 3D view fills the window,
turn on shadows, and frame/chase the action. Use in any GUI lesson."""

import pybullet as p


def setup_view(client, target=(1.0, 0.0, 0.8), dist=2.6, yaw=50, pitch=-32) -> None:
    """Make the PyBullet GUI less bare and frame the scene."""
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0, physicsClientId=client)
    p.configureDebugVisualizer(p.COV_ENABLE_SHADOWS, 1, physicsClientId=client)
    chase_cam(client, target, dist, yaw, pitch)


def chase_cam(client, target, dist=2.6, yaw=50, pitch=-32) -> None:
    """Point the GUI camera at `target` (e.g. the drone, each frame)."""
    p.resetDebugVisualizerCamera(
        cameraDistance=dist,
        cameraYaw=yaw,
        cameraPitch=pitch,
        cameraTargetPosition=list(target),
        physicsClientId=client,
    )
