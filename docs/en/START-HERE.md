# Start here — from zero to a drone that flies itself

## The goal, in one sentence

**Teach a 27-gram drone to fly itself — camera in, decisions out — fully
offline, on a chip with 512 KB of memory.**

Every lesson in this course serves that sentence. You will start in a physics
simulator (free, on your Mac), teach a tiny neural network to see and decide,
and keep everything small enough and honest enough that it could run on the
drone itself — no laptop, no Wi-Fi, no cloud. Real hardware is an optional
last step, not an entry fee.

## What you need

- A Mac with Apple Silicon (M1 or newer). That's it — **$0**.
- No robotics or machine-learning background. Every lesson explains *why*
  before *how*, and a [Glossary](GLOSSARY.md) covers the terms you'll meet
  in plain words.

## Your first flight

```bash
git clone https://github.com/csinghans/nanodrone-ai.git
cd nanodrone-ai
bash setup/install_macos.sh        # first time only: installs conda (skip if you have it)
bash setup/install_env.sh          # one-time: conda env + simulator
conda activate nanodrone-ai
python lessons/01_hover/hover_demo.py             # watch it fly
python lessons/01_hover/hover_demo.py --selftest  # let the computer verify it
```

The one-time install downloads a few gigabytes and can take a while; the
flight itself is under a minute. A window opens, a small quadcopter takes
off and holds a steady hover at 1 metre — and the second command re-flies
it headless and prints a line that starts with `HOVER OK`. That line is
the course's habit: **every lesson ends with a checkpoint the computer
verifies for you** — if the `OK` line prints, you did it right.

## The map

Do Lessons 1–10 in order — each builds on the last. After that, follow
your curiosity: every lesson's README starts with a one-line summary and a
"builds on" note, so you always know what to read first.

| Phase | Lessons | In plain words |
|---|---|---|
| **Fly, see, decide** | 1–10 | Hover, find things with the camera, learn your first behaviours, control by gamepad and by voice — the foundations. |
| **Missions** | 11–13, 14a, 16 | Turn single skills into whole missions with safety built in, ending in a graded capstone you design. |
| **Onto the chip** | 14b, 17–22 | Depth from one camera, optical flow, obstacle-dodging by reinforcement learning — each squeezed into a model tiny enough for the drone's own chip. |
| **The frontier** | 23–30 | Flight recorders, a $100 real-drone stepping stone, one command protocol for every drone, a nano *world model* that dodges obstacles before they're close — and the course summary. |
| **Side quest** | DroneVoice | An iPhone app that flies the drone by voice, sharing the same command contract. |

(You didn't miss Lesson 15 — there isn't one. Lesson 14 split into 14a,
which belongs with the missions, and 14b, which opens the on-chip track.)

Two rules carry the whole course, and you'll meet them everywhere:

1. **The two-layer split** — your AI never drives the motors. It sends simple
   commands ("go forward at 0.8 m/s"); a proven flight controller keeps the
   aircraft alive. That's how real autonomous drones are built.
2. **Measure, don't claim** — the simulator hands you training labels for
   free, you train your own tiny models, and every result is a number printed
   by a script you can rerun.

## When you want more

- Stuck on a word? → [Glossary](GLOSSARY.md)
- Want the full dependency graph, tracks and design rationale? →
  [Roadmap](ROADMAP.md)
- Want the mental model behind it all first? → [Overview](00-overview.md)

Now go fly. Lesson 1 is waiting.
