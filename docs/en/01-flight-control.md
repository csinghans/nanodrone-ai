# Lesson 1 — Flight control basics

**Goal:** make a simulated Crazyflie hover, then follow waypoints — free, no hardware.

A drone has two control layers. The **flight controller** (firmware) keeps it
stable and turns "go to point X" into motor speeds; **your code** picks the
target. That loop — **sense → decide → act** — recurs through the whole course.

**Run**

```bash
python lessons/01_hover/hover_demo.py
```

**Checkpoint ✅** A PyBullet window shows the quad rising to ~1 m and holding
steady; the console prints `Done: hovered at [0.0, 0.0, 1.0] for 10 s.`

➡️ Full lesson (code + walkthrough): [lessons/01_hover](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/01_hover)

Next: [Lesson 2 — Perception](02-perception.md)
