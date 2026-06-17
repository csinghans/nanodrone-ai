# Overview

**nanodrone-ai** teaches you to build on-device AI autonomy for a nano-drone,
starting entirely in simulation (free) and ending with a real Crazyflie that
flies itself offline.

## The mental model

Autonomy is a loop that runs forever: **sense → decide → act.**

- **Sense:** read sensors (camera, range, IMU, position).
- **Decide:** a planner or neural network chooses what to do next.
- **Act:** send a high-level command to the flight controller, which handles
  the fast, dangerous job of keeping the drone stable.

Self-driving cars do exactly this. We shrink it onto a 27 g quadcopter.

## Why simulation first

1. **It's free** — no hardware until Lesson 4.
2. **It's safe** — a bug crashes a sprite, not a propeller into your hand.
3. **It's fast** — train an AI over thousands of flights overnight.

We use [gym-pybullet-drones](https://github.com/utiasDSL/gym-pybullet-drones),
which models the real Crazyflie 2.x and runs natively on Apple Silicon.

## Why a nano-drone (Crazyflie)

The end goal is *on-board, offline* AI. The Crazyflie + AI-deck is the cheapest
credible platform that runs a real neural network on the drone itself, using the
GAP8 chip — the same approach as the academic [PULP-Dronet](https://github.com/pulp-platform/pulp-dronet) project.

## Course map

| Lesson | What you learn |
|--------|----------------|
| 0 | Set up Python + simulator on your Mac |
| 1 | Make the drone hover and follow waypoints |
| 2 | Detect obstacles from a camera |
| 3 | Let a neural network fly the drone (avoid obstacles) |
| 4 | Deploy to real hardware, flying fully offline |

Next: [Lesson 1 — Flight control basics](../../lessons/01_hover/README.md).
