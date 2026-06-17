# Lesson 6 — Follow-me tracking

**Goal:** make the drone follow a moving target using only its camera.

This is *visual servoing* and it closes the full loop **see → locate → move**:
detect the green target (HSV, like Lesson 2), range it with the depth image,
reconstruct its world position from the drone's pose, and trail a standoff point
behind it with the PID controller. No training — just a clear rule.

**Run**

```bash
python lessons/06_follow_me/follow_me.py
python lessons/06_follow_me/follow_me.py --headless   # verify / CI
```

**Checkpoint ✅** Headless prints `FOLLOW OK: ... mean bearing error 5.3 deg` —
a few degrees means the drone kept the target centred and followed it.

➡️ Full lesson (code + walkthrough): [lessons/06_follow_me](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/06_follow_me)
