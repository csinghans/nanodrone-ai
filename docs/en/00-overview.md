# Overview

**nanodrone-ai** teaches you to build on-device AI autonomy for a nano-drone,
starting entirely in simulation (free) and ending with a real Crazyflie that
flies itself offline.

(Looking for the install steps? They live in [Start here](START-HERE.md) —
two setup scripts, then your first flight.)

## The mental model

Autonomy is a loop that runs forever: **sense → decide → act.**

- **Sense:** read sensors (camera, range, IMU, position).
- **Decide:** a planner or neural network chooses what to do next.
- **Act:** send a high-level command to the flight controller, which handles
  the fast, dangerous job of keeping the drone stable.

Self-driving cars do exactly this. We shrink it onto a 27 g quadcopter.

## Why simulation first

1. **It's free** — the whole required track runs in the simulator; real
   hardware is an optional, clearly-priced step near the end (Track E).
2. **It's safe** — a bug crashes a sprite, not a propeller into your hand.
3. **It's fast** — train an AI over thousands of flights overnight.

We use [gym-pybullet-drones](https://github.com/utiasDSL/gym-pybullet-drones),
which models the real Crazyflie 2.x and runs natively on Apple Silicon.

## Why a nano-drone (Crazyflie)

The end goal is *on-board, offline* AI. The Crazyflie + AI-deck is the cheapest
credible platform that runs a real neural network on the drone itself, using the
GAP8 chip — the same approach as the academic [PULP-Dronet](https://github.com/pulp-platform/pulp-dronet) project.

## Course map

The course runs from Lesson 1 (your first hover) to Lesson 30 (the summary),
in five phases:

| Phase | Lessons | In plain words |
|---|---|---|
| Fly, see, decide | 1–10 | Hover, camera perception, first learned behaviours, gamepad + voice control |
| Missions | 11–13, 14a, 16 | Whole missions as guarded state machines, ending in a graded capstone (no Lesson 15 — 14 split into 14a/14b) |
| Onto the chip | 14b, 17–22 | Depth, optical flow, RL avoidance — each distilled small enough for the drone's own chip |
| The frontier | 23–30 | Flight recorder, real-drone stepping stone, one shared protocol, the nano world model (research preview — deep dive continues in [microdrone-world-model](https://github.com/csinghans/microdrone-world-model)), the summary |
| Side quest | DroneVoice | An iPhone app flying the drone by voice over the same protocol |

The one-page quickstart and reading order live in [Start here](START-HERE.md);
the full dependency graph and design rationale live in the
[Roadmap](ROADMAP.md).

Next: [Lesson 1 — Flight control basics](https://github.com/csinghans/nanodrone-ai/blob/main/lessons/01_hover/README.md).
