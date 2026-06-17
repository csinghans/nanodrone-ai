"""Shared vision helpers: colour-blob detection and pixel-to-world geometry.

This is the detector first written by hand in Lesson 2, factored out so Lessons
3, 6 and 7 reuse one implementation instead of copying it.
"""

import math
from dataclasses import dataclass

import cv2
import numpy as np

# HSV colour presets (OpenCV hue is 0-179). Each is a list of (low, high) ranges
# so colours that wrap around the hue circle (red) can use two ranges.
RED = [((0, 120, 80), (10, 255, 255)), ((170, 120, 80), (180, 255, 255))]
GREEN = [((40, 80, 60), (85, 255, 255))]
ORANGE = [((8, 120, 120), (25, 255, 255))]


@dataclass
class Blob:
    """A detected colour blob. `bearing`/`elevation` are degrees off the camera
    axis; `distance` is metres."""

    found: bool
    bearing: float = 0.0
    elevation: float = 0.0
    distance: float = 0.0
    cx: float = 0.0
    cy: float = 0.0
    area: float = 0.0


def linearize_depth(depth_buffer, near: float, far: float) -> float:
    """Convert PyBullet's non-linear [0,1] depth buffer into metres."""
    return far * near / (far - (far - near) * float(depth_buffer))


def detect_blob(rgb, dep, color, near, far, fov_deg=60.0, min_area=20) -> Blob:
    """Find the largest blob of `color` (a preset like RED/GREEN/ORANGE) and
    return its bearing, elevation, and distance. `rgb` is HxWx4, `dep` is HxW."""
    bgr = cv2.cvtColor(rgb[:, :, :3].astype(np.uint8), cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    mask = None
    for lo, hi in color:
        m = cv2.inRange(hsv, lo, hi)
        mask = m if mask is None else cv2.bitwise_or(mask, m)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return Blob(False)
    blob = max(contours, key=cv2.contourArea)
    area = cv2.contourArea(blob)
    if area < min_area:
        return Blob(False)
    mom = cv2.moments(blob)
    cx, cy = mom["m10"] / mom["m00"], mom["m01"] / mom["m00"]
    h, w = rgb.shape[0], rgb.shape[1]
    half = math.radians(fov_deg / 2)
    bearing = math.degrees(math.atan(((2 * cx / w) - 1) * math.tan(half)))
    elevation = math.degrees(math.atan(-((2 * cy / h) - 1) * math.tan(half)))
    distance = linearize_depth(dep[int(cy), int(cx)], near, far)
    return Blob(True, bearing, elevation, distance, cx, cy, area)


def world_point(drone_pos, drone_yaw: float, bearing_deg: float, distance: float):
    """World (x, y) of a detection from the drone's pose. The camera faces
    `drone_yaw`; a target left of frame reads as a negative bearing (Lesson 2).
    Returns (x, y, theta) where theta is the world angle drone->target."""
    theta = drone_yaw - math.radians(bearing_deg)
    return (
        drone_pos[0] + distance * math.cos(theta),
        drone_pos[1] + distance * math.sin(theta),
        theta,
    )
