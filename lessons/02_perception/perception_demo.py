"""
Lesson 2 — Perception
=====================
The drone now has eyes. We mount a forward-facing camera, place a bright red
obstacle ahead, and use OpenCV to answer the two questions every autonomous
robot must answer about an obstacle: **how far** and **which way**.

Pipeline (this is the "sense" stage of sense -> decide -> act):

  1. Hover steady (Lesson 1's controller) so the camera isn't blurry.
  2. Grab the drone's onboard RGB + depth image.
  3. OpenCV: threshold the red pixels -> find the obstacle blob -> its centroid.
  4. Bearing  = horizontal angle of the centroid (from the camera FOV).
     Distance = the depth image, sampled at the centroid, converted to metres.

Run:  python lessons/02_perception/perception_demo.py            # opens a window
      python lessons/02_perception/perception_demo.py --headless # no window (CI)

Saved output (annotated images you can open) goes to lessons/02_perception/output/.
"""

import math
import os
import sys

import numpy as np

try:
    import cv2
    import pybullet as p
    from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
    from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import a dependency:", exc)
    print("Activate the env first:  conda activate nanodrone-ai")
    sys.exit(1)


# --- Scene setup -----------------------------------------------------------
HOVER_POS = np.array([0.0, 0.0, 1.0])  # the drone holds here, facing +X
OBSTACLE_POS = [2.0, 0.4, 1.0]  # red box: 2 m ahead, a little to one side
OBSTACLE_HALF = 0.2  # half-size of the cube (so a 0.4 m box)
IMG_W, IMG_H = 160, 160  # camera resolution (square -> matches the 60 deg FOV)
CAMERA_FOV_DEG = 60.0  # must match BaseAviary._getDroneImages (fov=60, aspect=1)
OUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def add_red_box(client: int) -> None:
    """Place a static, bright-red cube in the world (easy to see + threshold)."""
    half = [OBSTACLE_HALF] * 3
    col = p.createCollisionShape(p.GEOM_BOX, halfExtents=half, physicsClientId=client)
    vis = p.createVisualShape(
        p.GEOM_BOX, halfExtents=half, rgbaColor=[1, 0, 0, 1], physicsClientId=client
    )
    p.createMultiBody(
        baseMass=0,  # mass 0 -> static, it won't fall
        baseCollisionShapeIndex=col,
        baseVisualShapeIndex=vis,
        basePosition=OBSTACLE_POS,
        physicsClientId=client,
    )


def linearize_depth(depth_buffer: float, near: float, far: float) -> float:
    """Convert PyBullet's non-linear [0,1] depth buffer into metres.

    PyBullet returns the raw OpenGL depth buffer, not a distance. This is the
    standard formula to recover the view-space distance along the camera axis.
    """
    return far * near / (far - (far - near) * depth_buffer)


def detect_obstacle(rgb: np.ndarray, dep: np.ndarray, near: float, far: float):
    """Find the red obstacle and return (detected, distance_m, bearing_deg, viz)."""
    # PyBullet gives RGBA; OpenCV works in BGR.
    bgr = cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Red wraps around the hue circle, so we need two ranges.
    lower = cv2.inRange(hsv, (0, 120, 80), (10, 255, 255))
    upper = cv2.inRange(hsv, (170, 120, 80), (180, 255, 255))
    mask = cv2.bitwise_or(lower, upper)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    viz = bgr.copy()
    if not contours:
        return False, None, None, viz

    blob = max(contours, key=cv2.contourArea)
    if cv2.contourArea(blob) < 30:  # too small -> ignore noise
        return False, None, None, viz

    m = cv2.moments(blob)
    cx = int(m["m10"] / m["m00"])
    cy = int(m["m01"] / m["m00"])

    # Bearing: where is the centroid horizontally within the field of view?
    # cx/W in [0,1] -> normalized [-1,1] -> angle through the pinhole model.
    half_fov = math.radians(CAMERA_FOV_DEG / 2)
    norm_x = (2.0 * cx / rgb.shape[1]) - 1.0
    bearing = math.degrees(math.atan(norm_x * math.tan(half_fov)))

    # Distance: sample the depth image at the centroid and convert to metres.
    distance = linearize_depth(float(dep[cy, cx]), near, far)

    # Draw what we found so a human can sanity-check it.
    x, y, w, h = cv2.boundingRect(blob)
    cv2.rectangle(viz, (x, y), (x + w, y + h), (0, 255, 0), 2)
    cv2.circle(viz, (cx, cy), 3, (255, 0, 0), -1)
    cv2.putText(
        viz,
        f"{distance:.2f}m {bearing:+.1f}deg",
        (5, 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 0),
        1,
    )
    return True, distance, bearing, viz


def main(gui: bool = True) -> None:
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([HOVER_POS]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
    )
    add_red_box(env.CLIENT)
    env.IMG_RES = np.array([IMG_W, IMG_H])  # enable on-demand camera capture
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)

    # Hover for ~1 s so the drone is steady before we look.
    action = np.zeros((1, 4))
    for _ in range(env.CTRL_FREQ):
        obs, _, _, _, _ = env.step(action)
        action[0, :], _, _ = ctrl.computeControlFromState(
            control_timestep=env.CTRL_TIMESTEP, state=obs[0], target_pos=HOVER_POS
        )

    # The camera's near/far planes are defined in BaseAviary._getDroneImages.
    near, far = env.L, 1000.0
    rgb, dep, _seg = env._getDroneImages(0, segmentation=False)
    detected, distance, bearing, viz = detect_obstacle(rgb, dep, near, far)

    os.makedirs(OUT_DIR, exist_ok=True)
    cv2.imwrite(
        os.path.join(OUT_DIR, "camera_rgb.png"),
        cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR),
    )
    cv2.imwrite(os.path.join(OUT_DIR, "detection.png"), viz)

    if detected:
        side = "right" if bearing > 0 else "left" if bearing < 0 else "centre"
        print(
            f"Obstacle detected: {distance:.2f} m ahead, "
            f"bearing {bearing:+.1f} deg ({side})."
        )
    else:
        print("No obstacle detected.")
    print(f"Saved camera_rgb.png and detection.png in {OUT_DIR}")

    env.close()


if __name__ == "__main__":
    main(gui="--headless" not in sys.argv)
