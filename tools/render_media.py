"""
Render the demo media used in the README/docs (all headless, no GUI window).

Produces, into assets/:
  * hover.gif      - Lesson 1: the drone holding a hover (orbit-ish view)
  * avoid.gif      - Lesson 3: the trained RL policy arcing around the pillar
  * detection.png  - Lesson 2: the obstacle detection overlay

Run:  python tools/render_media.py
Requires the Lesson 3 model (lessons/03_autonomy_ai/output/ppo_avoid.zip);
run train_rl.py first for avoid.gif (it is skipped if the model is missing).
"""

import os
import sys

import numpy as np
import pybullet as p
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
sys.path.insert(0, os.path.join(ROOT, "lessons", "03_autonomy_ai"))
sys.path.insert(0, os.path.join(ROOT, "lessons", "02_perception"))

from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl  # noqa: E402
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary  # noqa: E402
from gym_pybullet_drones.utils.enums import DroneModel, Physics  # noqa: E402

W, H = 360, 270


def _world_frame(client, target, distance, yaw, pitch) -> Image.Image:
    """Render one RGB frame from a fixed world camera."""
    view = p.computeViewMatrixFromYawPitchRoll(
        cameraTargetPosition=target,
        distance=distance,
        yaw=yaw,
        pitch=pitch,
        roll=0,
        upAxisIndex=2,
        physicsClientId=client,
    )
    proj = p.computeProjectionMatrixFOV(fov=60, aspect=W / H, nearVal=0.1, farVal=10.0)
    _, _, rgba, _, _ = p.getCameraImage(
        W, H, viewMatrix=view, projectionMatrix=proj, physicsClientId=client
    )
    arr = np.reshape(rgba, (H, W, 4))[:, :, :3].astype(np.uint8)
    return Image.fromarray(arr)


def _save_gif(frames, path, ms_per_frame=60) -> None:
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=ms_per_frame,
        loop=0,
        optimize=True,
    )
    print(f"  wrote {path} ({len(frames)} frames, {os.path.getsize(path)//1024} KB)")


def render_hover() -> None:
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0, 0, 0.1]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    target = np.array([0, 0, 1.0])
    action = np.zeros((1, 4))
    frames = []
    for i in range(int(4 * env.CTRL_FREQ)):
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=target
        )
        if i % 6 == 0:  # ~32 frames
            yaw = 40 + i * 0.25  # slowly orbit for a nicer view
            frames.append(_world_frame(env.CLIENT, [0, 0, 0.7], 1.6, yaw, -25))
    env.close()
    _save_gif(frames, os.path.join(ASSETS, "hover.gif"))


def render_avoid() -> None:
    from avoid_aviary import AvoidAviary

    model_path = os.path.join(
        ROOT, "lessons", "03_autonomy_ai", "output", "ppo_avoid.zip"
    )
    if not os.path.exists(model_path):
        print("  (skipping avoid.gif: no trained model -- run train_rl.py first)")
        return
    from stable_baselines3 import PPO

    model = PPO.load(model_path)
    env = AvoidAviary(gui=False)
    obs, _ = env.reset(seed=1000)
    frames = []
    done = False
    i = 0
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, _r, term, trunc, _info = env.step(action)
        if i % 3 == 0:  # angled close view so the drone arcing around is visible
            frames.append(_world_frame(env.CLIENT, [0.7, 0.05, 1.0], 1.5, 38, -28))
        i += 1
        done = term or trunc
    env.close()
    _save_gif(frames, os.path.join(ASSETS, "avoid.gif"))


def render_detection() -> None:
    import cv2
    from perception_demo import OBSTACLE_POS, add_red_box, detect_obstacle

    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0, 0, 1.0]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=False,
    )
    add_red_box(env.CLIENT)
    env.IMG_RES = np.array([160, 160])
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    action = np.zeros((1, 4))
    for _ in range(env.CTRL_FREQ):
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=np.array([0, 0, 1.0]),
        )
    rgb, dep, _ = env._getDroneImages(0, segmentation=False)
    _det, _dist, _bear, viz = detect_obstacle(rgb, dep, env.L, 1000.0)
    big = cv2.resize(viz, (320, 320), interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(os.path.join(ASSETS, "detection.png"), big)
    print(f"  wrote {os.path.join(ASSETS, 'detection.png')}")
    env.close()
    _ = OBSTACLE_POS  # (silence unused import; documents where the box sits)


if __name__ == "__main__":
    os.makedirs(ASSETS, exist_ok=True)
    print("Rendering media into assets/ ...")
    render_hover()
    render_detection()
    render_avoid()
    print("Done.")
