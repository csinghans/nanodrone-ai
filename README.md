# nanodrone-ai

> **A beginner-friendly, step-by-step journey to on-device AI autonomy for nano-drones — start in simulation for $0, graduate to a real Crazyflie that flies itself fully offline.**

🌐 **Languages:** **English** · [繁體中文](README.zh-TW.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## What is this?

This is an open-source course. It teaches you to build **edge-AI autonomy for a nano-drone** — the same idea as a self-driving car, shrunk down to a 27-gram quadcopter that runs a neural network **on-board** and flies itself **offline** (no laptop, no Wi-Fi, no cloud).

You will start writing code **today, for free**, entirely in a physics simulator on your Mac. Hardware is optional and only needed for the very last lesson.

**Who is this for?** Total beginners. Every lesson explains *why*, not just *how*.

## The big idea: two layers (the AI never drives the motors directly)

```
┌─────────────────────────────────────────────────────────┐
│  Companion compute — YOUR AI                              │
│  Perception → Localization → Planning → high-level command │  ~10–30 Hz
│  (runs neural nets, reads the camera, decides where to go) │
└───────────────────────┬─────────────────────────────────┘
                        │ MAVLink-style setpoints (velocity / position)
┌───────────────────────▼─────────────────────────────────┐
│  Flight controller firmware (PX4 / ArduPilot / Crazyflie) │
│  Attitude stabilization, motor mixing, IMU feedback        │  ~400 Hz–1 kHz
└─────────────────────────────────────────────────────────┘
```

The **flight controller** keeps the drone from falling out of the sky (a hard real-time job — don't touch it). **Your AI** decides *where to go* and sends high-level commands. In simulation both layers run on your Mac; on real hardware your AI runs on the **AI-deck's GAP8 chip**.

## Learning path

| Lesson | Topic | Cost | You'll build |
|--------|-------|------|--------------|
| **0** | Setup & project skeleton | $0 | A working Python + simulator environment |
| **1** | Flight control basics | $0 | A script that flies a square path and lands |
| **2** | Perception | $0 | Obstacle detection from a simulated camera |
| **3** | Autonomous decision AI | $0 | A drone that avoids obstacles using *only* a neural net |
| **4** | Real hardware + on-board offline AI | ~US$545 | A Crazyflie flying itself with the laptop unplugged |

Each lesson follows the same five-part shape: **Why → Concept → Hands-on → Checkpoint → Going further.**

## Quickstart (Lesson 0)

> Requires an **Apple Silicon Mac** (M1–M4). See [setup/install_macos.sh](setup/install_macos.sh).

```bash
# 1. Install miniforge (conda for Apple Silicon) if you don't have it
bash setup/install_macos.sh

# 2. Create and activate the environment
conda env create -f environment.yml
conda activate nanodrone-ai

# 3. Verify the GPU (MPS) backend is available
python -c "import torch; print('MPS available:', torch.backends.mps.is_available())"

# 4. Run your first simulated drone (hovers for 10 s)
python lessons/01_hover/hover_demo.py
```

A PyBullet window should open and show a tiny quadcopter holding a hover at 1 m. 🎉

## Cost: how cheap can this be?

- **Lessons 0–3 cost nothing** beyond a Mac you already own.
- **Lesson 4** (truly on-board, offline neural-net inference on a nano-drone) needs the [Bitcraze "AI bundle"](https://store.bitcraze.io/products/the-ai-bundle): **≈ US$545** (Crazyflie 2.1+, AI-deck 1.1 with the GAP8 chip, Flow deck v2, Crazyradio 2.0).
- There is no cheaper *credible* way to run a neural network on-board a nano-drone. A DJI Tello (≈ US$100) is great for practice but runs the AI **off-board over Wi-Fi**, which is not the offline goal of this course.

## Safety & legal

Real drone flight is regulated. Before flying hardware (Lesson 4): check your local rules (e.g. Taiwan's CAA remote-drone regulations), always fit **failsafes** (return/land on link loss, geofence, low-battery land), test in open areas, and keep a manual RC override ready. **Always validate in simulation first.**

## Contributing & translations

Contributions welcome — especially translation review. See [CONTRIBUTING.md](CONTRIBUTING.md) ([繁中](CONTRIBUTING.zh-TW.md)). English is the source language; the Traditional Chinese version follows it.

## Credits

Stands on the shoulders of [gym-pybullet-drones](https://github.com/utiasDSL/gym-pybullet-drones), [Bitcraze Crazyflie](https://www.bitcraze.io/), and the [PULP-Dronet](https://github.com/pulp-platform/pulp-dronet) research (ETH Zürich / University of Bologna).

## License

[MIT](LICENSE).
