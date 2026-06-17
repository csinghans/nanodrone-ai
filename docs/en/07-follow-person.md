# Lesson 7 — Follow the pilot

**Goal:** drive a person around the sim and have the drone follow you on its own.

The "follow-me drone" everyone pictures. It fuses Lesson 5 (you driving the
person), Lesson 6 (visual following), and **yaw control**: each tick the drone
detects the orange person, computes your world position, **turns to face you**,
and trails a standoff point behind you. Turning to face you is what lets it
follow you *around*, not just side to side.

**Run**

```bash
pip install -r setup/requirements-extra.txt   # pygame (gamepad, from Lesson 5)
python lessons/07_follow_person/follow_person.py            # you drive, drone follows
python lessons/07_follow_person/follow_person.py --headless # scripted demo / CI
```

Drive the **person** with the right stick or arrow keys; the drone is autonomous.

**Checkpoint ✅** Headless walks the person in a circle and prints
`FOLLOW OK: ... mean bearing error 1.5 deg` — ~1° means it stayed locked on you.

➡️ Full lesson (code + walkthrough): [lessons/07_follow_person](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/07_follow_person)
