# Lesson 8 — Follow a real person (learned detector)

**Goal:** follow a realistic person no colour rule can isolate — so we train a CNN.

This is the course's first capability that needs **training** first. The person
is a multi-colour figure (its blue shirt even blends with the floor), so instead
of a colour threshold we train a small `PersonCNN` to answer "which way is the
person?". Labels are free from the simulator's ground truth. Range comes from the
depth sensor, and the yaw-follow loop is reused from Lesson 7.

**Run (train, then fly)**

```bash
python lessons/08_follow_real/gen_person_dataset.py    # 1. data (ground-truth labels)
python lessons/08_follow_real/train_person_cnn.py      # 2. train (MPS)
python lessons/08_follow_real/follow_real.py           # 3. you drive, drone follows
python lessons/08_follow_real/follow_real.py --headless # scripted demo / verify
```

**Checkpoint ✅** Training reaches ~1.2° validation MAE; headless follow prints
`FOLLOW OK (CNN): ... mean true bearing error 14.1 deg` — the drone tracks the
person with a detector it learned, no colour rule anywhere.

➡️ Full lesson (code + walkthrough): [lessons/08_follow_real](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/08_follow_real)
