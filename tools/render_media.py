"""
Render every lesson's demo GIF (all headless, no GUI window) into assets/.

Each lesson README embeds assets/<name>.gif. Re-run this whenever a lesson's
behaviour changes:  python tools/render_media.py

Outputs:
  assets/lesson1.gif  hover            assets/lesson6.gif  follow a target
  assets/lesson2.gif  detection (POV)  assets/lesson7.gif  follow the pilot
  assets/lesson3.gif  RL avoidance     assets/lesson8.gif  follow a real person
  assets/lesson5.gif  teleop           (Lesson 0 reuses lesson1; Lesson 4 has no
                                         sim flight — it's model + hardware.)
Lesson 3 and 8 need their trained models (run those lessons' training first);
they are skipped with a note if the model is missing.
"""

import os
import sys

import cv2
import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from PIL import Image

from nanodrone import GREEN, ORANGE, SelftestInput, detect_blob, world_point

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
for d in (
    "02_perception",
    "03_autonomy_ai",
    "06_follow_me",
    "07_follow_person",
    "08_follow_real",
):
    sys.path.insert(0, os.path.join(ROOT, "lessons", d))

W, H = 360, 270


def new_env(gui=False):
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([[0.0, 0.0, 1.0]]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
    )
    env.IMG_RES = np.array([160, 160])
    return env, DSLPIDControl(drone_model=DroneModel.CF2X)


def world_frame(client, target, dist=2.4, yaw=50, pitch=-30) -> Image.Image:
    view = p.computeViewMatrixFromYawPitchRoll(
        list(target), dist, yaw, pitch, 0, 2, physicsClientId=client
    )
    proj = p.computeProjectionMatrixFOV(60, W / H, 0.1, 12.0)
    _, _, rgba, _, _ = p.getCameraImage(
        W, H, viewMatrix=view, projectionMatrix=proj, physicsClientId=client
    )
    return Image.fromarray(np.reshape(rgba, (H, W, 4))[:, :, :3].astype(np.uint8))


def save_gif(frames, name, ms=60) -> None:
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, name)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=ms,
        loop=0,
        optimize=True,
    )
    print(f"  {name}: {len(frames)} frames, {os.path.getsize(path) // 1024} KB")


def render_hover():  # Lesson 1 (and reused by Lesson 0)
    env, ctrl = new_env()
    target = np.array([0, 0, 1.0])
    action = np.zeros((1, 4))
    frames = []
    for i in range(int(4 * env.CTRL_FREQ)):
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=target
        )
        if i % 6 == 0:
            frames.append(world_frame(env.CLIENT, [0, 0, 0.7], 1.6, 40 + i * 0.25, -25))
    env.close()
    save_gif(frames, "lesson1.gif")


def render_detection():  # Lesson 2 — onboard camera POV with the detection box
    from perception_demo import add_red_box, detect_obstacle

    env, ctrl = new_env()
    add_red_box(env.CLIENT)
    action = np.zeros((1, 4))
    frames = []
    for i in range(int(3 * env.CTRL_FREQ)):
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=np.array([0, 0, 1.0]),
        )
        if i % 4 == 0:
            rgb, dep, _ = env._getDroneImages(0, segmentation=False)
            _d, _dist, _b, viz = detect_obstacle(rgb, dep, env.L, 1000.0)
            big = cv2.resize(viz, (W, W), interpolation=cv2.INTER_NEAREST)
            frames.append(Image.fromarray(cv2.cvtColor(big, cv2.COLOR_BGR2RGB)))
    env.close()
    save_gif(frames, "lesson2.gif", ms=90)


def render_avoid():  # Lesson 3 — trained RL policy arcing around the pillar
    from avoid_aviary import AvoidAviary

    model_path = os.path.join(
        ROOT, "lessons", "03_autonomy_ai", "output", "ppo_avoid.zip"
    )
    if not os.path.exists(model_path):
        print("  lesson3.gif skipped (no RL model — run train_rl.py)")
        return
    from stable_baselines3 import PPO

    model = PPO.load(model_path)
    env = AvoidAviary(gui=False)
    obs, _ = env.reset(seed=1000)
    frames = []
    done = False
    i = 0
    while not done:
        a, _ = model.predict(obs, deterministic=True)
        obs, _r, term, trunc, _ = env.step(a)
        if i % 3 == 0:
            frames.append(world_frame(env.CLIENT, [0.7, 0.05, 1.0], 1.5, 38, -28))
        i += 1
        done = term or trunc
    env.close()
    save_gif(frames, "lesson3.gif")


def render_teleop():  # Lesson 5 — scripted "stick" input flying the drone
    env, ctrl = new_env()
    backend = SelftestInput(steps_per_phase=40)
    target = np.array([0.0, 0.0, 1.0])
    tyaw = 0.0
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    frames = []
    for i in range(170):
        fwd, strafe, up, yaw_in = backend.read()
        tyaw += yaw_in * 1.5 * dt
        c, s = np.cos(tyaw), np.sin(tyaw)
        target[0] = float(np.clip(target[0] + (fwd * c - strafe * s) * dt, -2, 2))
        target[1] = float(np.clip(target[1] + (fwd * s + strafe * c) * dt, -2, 2))
        target[2] = float(np.clip(target[2] + up * dt, 0.2, 2.5))
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=dt,
            state=obs[0],
            target_pos=target,
            target_rpy=np.array([0, 0, tyaw]),
        )
        if i % 4 == 0:
            frames.append(world_frame(env.CLIENT, obs[0][0:3], 2.2, 50, -30))
    env.close()
    save_gif(frames, "lesson5.gif")


def render_follow_me():  # Lesson 6 — follow a moving green target
    from follow_me import target_position

    env, ctrl = new_env()
    vis = p.createVisualShape(
        p.GEOM_SPHERE, radius=0.12, rgbaColor=[0, 1, 0, 1], physicsClientId=env.CLIENT
    )
    tid = p.createMultiBody(
        baseMass=0,
        baseVisualShapeIndex=vis,
        basePosition=target_position(0.0),
        physicsClientId=env.CLIENT,
    )
    target = np.array([0.0, 0.0, 1.0])
    action = np.zeros((1, 4))
    near, far = env.L, 1000.0
    frames = []
    for i in range(int(10 * env.CTRL_FREQ)):
        t = i * env.CTRL_TIMESTEP
        p.resetBasePositionAndOrientation(
            tid, target_position(t), [0, 0, 0, 1], physicsClientId=env.CLIENT
        )
        obs, _, _, _, _ = env.step(action)
        dpos = obs[0][0:3]
        if i % 6 == 0:
            rgb, dep, _ = env._getDroneImages(0, segmentation=False)
            b = detect_blob(rgb, dep, GREEN, near, far)
            if b.found:
                px, py, _th = world_point(dpos, 0.0, b.bearing, b.distance)
                target = np.array([np.clip(px - 1.0, -2, 2), np.clip(py, -2, 2), 1.0])
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=target
        )
        if i % 6 == 0:
            frames.append(world_frame(env.CLIENT, dpos, 2.4, 35, -32))
    env.close()
    save_gif(frames, "lesson6.gif")


def render_follow_person():  # Lesson 7 — follow the pilot you drive
    import follow_person as L7

    env, ctrl = new_env()
    person = L7.build_person(env.CLIENT)
    target_yaw = 0.0
    target = np.array([0.0, 0.0, 1.0])
    action = np.zeros((1, 4))
    near, far = env.L, 1000.0
    frames = []
    for i in range(int(14 * env.CTRL_FREQ)):
        t = i * env.CTRL_TIMESTEP
        px, py = L7.scripted_person_xy(t)
        L7.move_person(person, px, py, 0.0, env.CLIENT)
        obs, _, _, _, _ = env.step(action)
        dpos, dyaw = obs[0][0:3], obs[0][9]
        if i % 6 == 0:
            rgb, dep, _ = env._getDroneImages(0, segmentation=False)
            b = detect_blob(rgb, dep, ORANGE, near, far)
            if b.found:
                _x, _y, th = world_point(dpos, dyaw, b.bearing, b.distance)
                target_yaw = th
                reach = b.distance - 1.3
                target = np.array(
                    [
                        np.clip(dpos[0] + reach * np.cos(th), -3, 3),
                        np.clip(dpos[1] + reach * np.sin(th), -3, 3),
                        1.0,
                    ]
                )
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=target,
            target_rpy=np.array([0, 0, target_yaw]),
        )
        if i % 6 == 0:
            frames.append(world_frame(env.CLIENT, dpos, 2.6, 50, -32))
    env.close()
    save_gif(frames, "lesson7.gif")


def render_follow_real():  # Lesson 8 — follow a real person via the trained CNN
    import follow_real as L8
    import torch
    from person import build_person, move_person
    from train_person_cnn import MODEL, PersonCNN

    if not os.path.exists(MODEL):
        print("  lesson8.gif skipped (no CNN — run gen_person_dataset + train)")
        return
    device = "mps" if torch.backends.mps.is_available() else "cpu"
    model = PersonCNN().to(device)
    model.load_state_dict(torch.load(MODEL, map_location=device))
    model.eval()

    env, ctrl = new_env()
    person = build_person(env.CLIENT)
    target_yaw = 0.0
    target = np.array([0.0, 0.0, 1.0])
    action = np.zeros((1, 4))
    near, far = env.L, 1000.0
    frames = []
    for i in range(int(16 * env.CTRL_FREQ)):
        t = i * env.CTRL_TIMESTEP
        px, py = L8.scripted_person_xy(t)
        move_person(person, px, py, 0.0, env.CLIENT)
        obs, _, _, _, _ = env.step(action)
        dpos, dyaw = obs[0][0:3], obs[0][9]
        if i % 6 == 0:
            rgb, dep, _ = env._getDroneImages(0, segmentation=False)
            bearing = L8.cnn_bearing(model, device, rgb)
            dist = L8.depth_at_bearing(dep, bearing, near, far)
            if dist <= L8.MAX_RANGE:
                _x, _y, th = world_point(dpos, dyaw, bearing, dist)
                target_yaw = th
                reach = float(np.clip(dist - 1.4, -0.5, 0.5))
                target = np.array(
                    [
                        np.clip(dpos[0] + reach * np.cos(th), -3, 3),
                        np.clip(dpos[1] + reach * np.sin(th), -3, 3),
                        1.0,
                    ]
                )
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP,
            state=obs[0],
            target_pos=target,
            target_rpy=np.array([0, 0, target_yaw]),
        )
        if i % 6 == 0:
            frames.append(world_frame(env.CLIENT, dpos, 2.6, 50, -32))
    env.close()
    save_gif(frames, "lesson8.gif")


if __name__ == "__main__":
    print("Rendering lesson GIFs into assets/ ...")
    render_hover()
    render_detection()
    render_avoid()
    render_teleop()
    render_follow_me()
    render_follow_person()
    render_follow_real()
    print("Done.")
