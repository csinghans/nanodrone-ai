"""nanodrone.degrade — make a clean sim image look like a real camera frame.

A model trained on pristine sim renders meets a different world on real hardware:
darker, noisier, slightly blurred. These primitives apply that degradation so you
can *measure* the sim-to-real gap (Lesson 25) without a real camera, and so
Lesson 20's domain randomization has something concrete to defend against.
"""

import numpy as np


def jitter_brightness(imgs, factor: float = 0.65):
    """Scale brightness (a dimmer real camera / different exposure)."""
    return np.clip(imgs * factor, 0.0, 1.0).astype(np.float32)


def add_noise(imgs, sigma: float = 0.12, seed: int = 7):
    """Add Gaussian sensor noise."""
    rng = np.random.default_rng(seed)
    out = imgs + rng.normal(0, sigma, size=imgs.shape).astype(np.float32)
    return np.clip(out, 0.0, 1.0).astype(np.float32)


def blur(imgs):
    """A light 3x3 box blur (cheap lens softness)."""
    import cv2

    out = np.empty_like(imgs)
    for i in range(len(imgs)):
        out[i] = cv2.blur(imgs[i], (3, 3))
    return out.astype(np.float32)


def degrade(imgs, brightness: float = 0.65, sigma: float = 0.12, seed: int = 7):
    """The combined real-camera mimic: dimmer + blurred + noisy."""
    return add_noise(blur(jitter_brightness(imgs, brightness)), sigma, seed)
