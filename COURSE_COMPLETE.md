# Course complete — v1.0

🌐 **English** · [繁體中文](COURSE_COMPLETE.zh-TW.md)

Thirty lessons ago the goal fit in one sentence: **a 27 g drone that flies
itself, offline, on a 512 KB chip — starting from $0 in a simulator.** As of
v1.0 the course is complete: every lesson is implemented, bilingual, and
verified by a `--selftest` that prints an `XXX OK` line and asserts it.

## What's in scope

| Tier | Lessons | What they are |
|---|---|---|
| **Core path** | 1–13, 14a, 16 | Fly, see, decide — then whole missions as guarded state machines, capped by a graded capstone. Do these in order. |
| **On-chip track** | 4, 14b, 17–22 | Depth, optical flow, RL avoidance, domain randomization, distillation — everything squeezed toward int8 under 512 KB. |
| **Sim-to-real track** | 23–26 | Flight black box, a $100 Tello stepping stone, gap measurement, field SOP + Taiwan regulations. |
| **Protocol & apps** | 27–28, DroneVoice | One 13-action JSON contract shared by the sim, a Tello, a Crazyflie and an iPhone app. |
| **Research preview** | 29 | The nano V-JEPA world model — latent prediction, collision heads, a vision-only latent MPC and a learned policy, all measured. |
| **Summary** | 30 | The whole arc by the numbers + a graduation check that re-asserts the shared contracts. |

## The crown numbers (all measured, all reproducible)

| claim | number |
|---|---|
| the model can *choose*, not just detect | veer-ranking **1.00** (chance 0.5) |
| a learned policy over the world model | **0 %** crashes across the 0.8–1.6 m/s sweep (150 courses) *and* the cluttered courses |
| reaction, for comparison | up to **60–70 %** crashes at speed |
| the whole stack on a GAP8 budget | **137.3 KB < 512 KB**, ~8 ms/decision |
| the sim-to-real gap, priced then bought back | AUC 0.96 → 0.82 → **0.92** |

## Freeze policy

v1.0 freezes the course's scope. After this release the repo accepts **bug
fixes, documentation improvements and CI upkeep** — but no new large lessons.
A course that keeps growing never finishes teaching; this one is a finished
book. (Propose fixes via issues — see [CONTRIBUTING.md](CONTRIBUTING.md).)

## Where the story continues

Lesson 29 is deliberately a *preview*: it teaches the concepts and proves
them in simulation. The deep dive — harder worlds, model-side memory,
metric-grounded latents, and real hardware on a Crazyflie + AI-deck — lives
in the follow-up research project:

**→ [microdrone-world-model](https://github.com/csinghans/microdrone-world-model)**

The course repo is the proof you can learn it; the research repo is where it
gets sharp.
