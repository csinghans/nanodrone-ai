# Lesson 5 (bonus) — Fly it yourself with an Xbox controller

**Goal:** teleoperate the simulated drone with a gamepad — a fun contrast to the
autonomy of Lessons 1–4, and a fast way to build flight intuition.

The pad doesn't drive the motors (same two-layer idea as Lesson 1): each frame
we read the sticks → a desired **velocity** → integrate into a moving **target
position** → the PID flight controller chases it. Release the sticks and the
drone hovers.

**Run**

```bash
pip install -r setup/requirements-extra.txt        # pygame (Lesson 5 only)
python lessons/05_teleop/teleop_xbox.py            # Xbox pad (else keyboard)
python lessons/05_teleop/teleop_xbox.py --list     # calibrate axes
```

Controls (world-frame): **right stick** moves horizontally, **left stick**
changes height. Keyboard fallback: arrow keys + `W`/`S`.

**Checkpoint ✅** A window opens and the drone flies under your sticks, hovering
when you let go. No controller needed to verify the loop:
`python lessons/05_teleop/teleop_xbox.py --input selftest`.

➡️ Full lesson (code + walkthrough): [lessons/05_teleop](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/05_teleop)
