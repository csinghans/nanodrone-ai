# Lesson 2 — Perception

**Goal:** give the drone a camera and detect an obstacle — *how far* and *which way*.

We mount a forward camera, place a red obstacle ahead, and run the classic
computer-vision pipeline (the "sense" stage): threshold the red pixels (OpenCV
HSV) → find the blob's centroid → **bearing** from its position in the field of
view, **distance** from the depth image (converted from PyBullet's depth buffer
to metres).

**Run**

```bash
python lessons/02_perception/perception_demo.py
```

**Checkpoint ✅** Prints e.g. `Obstacle detected: 1.80 m ahead, bearing -12.2 deg (left).`
and saves an annotated `detection.png`.

➡️ Full lesson (code + walkthrough): [lessons/02_perception](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/02_perception)

Next: [Lesson 3 — Autonomous decision AI](03-autonomy-ai.md)
