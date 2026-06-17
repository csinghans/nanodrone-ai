# Lesson 3 — Autonomous decision AI

**Goal:** let the drone *decide* for itself. Two routes, RL as the main one.

- **Route A (main) — reinforcement learning.** A custom environment rewards
  progress toward a goal and penalizes hitting the pillar; PPO discovers a path
  that arcs around. (Verified: 100% goal-reach, 0 crashes over 20 episodes.)
- **Route B — imitation learning.** Lesson 2's detector becomes the *teacher*:
  it labels camera images, and a small CNN (`TinyDronet`, PULP-Dronet inspired)
  learns to predict bearing from pixels. (Verified: ~2° validation error.)

**Run**

```bash
python lessons/03_autonomy_ai/train_rl.py                 # Route A: train + evaluate
python lessons/03_autonomy_ai/gen_dataset.py --samples 500  # Route B: dataset (teacher)
python lessons/03_autonomy_ai/train_cnn.py                 # Route B: train the CNN
```

**Checkpoint ✅** RL eval prints `20 reached goal, 0 crashed (success rate 100%)`
and a top-down `trajectory.png` showing the learned arc; the CNN reaches a low
validation MAE in degrees.

➡️ Full lesson (code + walkthrough): [lessons/03_autonomy_ai](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/03_autonomy_ai)

Next: [Lesson 4 — Real hardware & on-board offline AI](04-hardware.md)
