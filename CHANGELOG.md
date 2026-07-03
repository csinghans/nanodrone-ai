# Changelog

## 1.0.0 — 2026-07-03

The course is complete. One arc, thirty lessons, every claim measured:

- **Foundations (L0–L10)** — hover, perception, a first learned behaviour,
  gamepad and bilingual voice control; the two-layer split (AI sends
  setpoints, the flight controller keeps the aircraft alive) established in
  Lesson 1 and never broken.
- **Track A — orchestration (L11–L14a, L16)** — missions as guarded state
  machines, voice-driven plans, find-follow-land, capped by a graded capstone
  whose validator *flies* your mission graph before grading it.
- **Track B — on-device perception (L14b, L17–L22)** — monocular depth,
  optical flow, multi-obstacle RL, domain randomization, distillation — all
  squeezed toward int8 under the 512 KB GAP8 budget.
- **Track E — sim-to-real groundwork (L23–L26)** — telemetry black box, a
  $100 Tello stepping stone, gap measurement, field SOP + Taiwan CAA rules.
- **Protocol & DroneVoice (L27–L28, apple/)** — one 13-action JSON contract
  shared by the sim, a Tello, a Crazyflie and an iPhone app.
- **Lesson 29 (research preview)** — the nano V-JEPA world model:
  counterfactual-labelled intervention dataset, bearing-aware encoder,
  multi-horizon dual-ring collision heads (AUC ~0.96, veer-ranking 1.00),
  a vision-only latent MPC, closed-loop scoreboards, a priced-and-bought-back
  sim-to-real gap (0.96 → 0.82 → 0.92), and a learned policy that flies the
  entire 0.8–1.6 m/s sweep crash-free on a 137.3 KB on-board budget — plus a
  four-run memory-architecture control study (stacked vs LSTM).
- **Lesson 30** — the course summary and a graduation check that re-asserts
  the shared contracts end to end.
- **Guide layer** — START-HERE, glossary, per-lesson one-line boxes,
  bilingual docs site with strict builds and CI parity checks.

From v1.0 on, the repo accepts bug fixes, documentation and CI upkeep only —
see [COURSE_COMPLETE.md](COURSE_COMPLETE.md). The research continues in
[microdrone-world-model](https://github.com/csinghans/microdrone-world-model).
