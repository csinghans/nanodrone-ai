# Roadmap — beyond Lesson 10

> This document is the blueprint for the post-Lesson-10 course — **L11–L29 and DroneVoice are now all implemented** (see each lesson folder and the `nanodrone/` modules). It carries forward nanodrone-ai's signature themes and ground rules: everything stays **$0 and sim-first**, every lesson follows the **five-part structure** (Why / Concept / Hands-on / Checkpoint / Going further), the docs stay **bilingual (en + zh-TW)**, and every script ships a `--selftest` that prints `XXX OK` + asserts. The end goal is unchanged: int8 on GAP8, an offline on-board self-flight under 512KB.

## 1. Status & design principles

Up to L10, the course has walked the full "sense→decide→act single-behaviour" chain end to end: perception (L2), autonomous obstacle avoidance (L3), real-hardware on-board int8 deployment (L4), visual following (L6/L7/L8), and voice with self-trained KWS (L9/L10). It has also opened the DroneVoice Apple App bridge side-track (phase 1 shipped `bridge/sim_server.py`, a TCP server that receives newline-JSON and drives the PyBullet sim). The course's signature theme is "the generic model isn't good enough → train a small model on your own data" (L3/L8/L10), and the end goal is unchanged: int8 on GAP8, an offline on-board self-flight under 512KB.

This plan rests on five design principles:

1. **Pay down technical debt before talking integration** — 11+ flight scripts each copied an almost word-for-word identical `CtrlAviary+DSLPIDControl` while loop; that must first be factored into a shared skeleton (L11 `nanodrone.mission`; on the protocol side the debt is paid down by L27 `nanodrone.protocol`).
2. **Every lesson must tie back to the end goal and the signature theme** — on-board consistency and "train your own model" are the two themes most likely to quietly disappear during integration, so this plan explicitly adds an on-board convergence lesson (L14b), forces a re-trained confirmation classifier in L13, and folds the whole "progressively squeeze the simulator's currently-idle capabilities (the full depth map, optical flow, domain randomization, distillation) into self-trained small models" into Track B, so the signature theme is not just "shown once more" but becomes a complete deepening main line.
3. **Be honest about the sim-to-real gap** — lessons that use ground-truth throughout must say plainly that "real hardware has no ground-truth." Track E makes this principle concrete: first polish the telemetry / replay / safety infrastructure in the $0 sim, then bring up a cheap Tello to measure the real gap, honestly labelling the hardware cost and "the Tello's AI is off-board, not offline on-board — not the end goal."
4. **Hold the teaching ground rules** — five-part structure, $0 sim-first, bilingual docs, every script's `--selftest` printing `XXX OK` + assert behaviour.
5. **Capabilities first self-produce data in sim, stay $0, and converge under `--selftest`; hardware and the sim-to-real gap are always labelled honestly, no faked reuse** — the new depth / optical-flow / DR / distillation lessons all reuse the existing `gen_dataset` / `gen_person_dataset` pattern of "the simulator hands you ground truth as a privileged label" and the npz format, reinventing no wheels; the real-hardware lessons (Tello / Crazyflie) always state "the protocol doesn't change, only the controller does," and spell out the essential difference between AI off-board (Tello) and offline on-board (Crazyflie / GAP8).

## 2. Tracks

The follow-on lessons consolidate into five tracks:

- **Track A — Orchestration (main line)**: L11 state-machine skeleton → L12 voice-driven transitions → L13 multimodal mini-capstone → L16 graduation project. This is the required path for everyone on the main line.
- **Track B — On-device / perception depth**: L14a mapping & patrol → L14b on-board convergence; then deeper with L17 monocular depth → L18 optical flow / VO → L19 multi-obstacle RL (fed by perception) → L20 domain randomization → L21 distillation + compression → L22 distill multiple capabilities into a single on-board policy. This track progressively squeezes the simulator's currently-idle capabilities into self-trained int8 small models — it is the deepening backbone of the signature theme, and the key to keeping the course **close to real hardware** rather than drifting away from it. L29 caps the track by extending this line from *reactive* to *anticipatory* — now closed-loop: a nano V-JEPA world model predicts warn/crit collision rings (never pixels) at four horizons, and a 12 Hz vision-only latent MPC flies it — at 1.4–1.6 m/s the reactive baseline crashes 40–60 % of single-pillar courses while the anticipating hand MPC holds 0–10 %; the crown result goes further: a *learned* policy over the same world model (L29 step 6) flies the entire 0.8–1.6 m/s sweep — 150 courses — without a single crash, all on a 137 KB on-board budget.
- **Track C — DroneVoice Apple App (parallel elective, needs Apple hardware)**: L27 protocol extraction (up-front technical debt) → L28 parser-evaluation arena (the quantitative foundation for the counter-example control group) → Phase 2 voice entry → Phase 3 on-device LLM parsing (counter-example control group) → Phase 4 SwiftUI + bidirectional telemetry + app failsafe → Phase 5 sim→real (5a Tello first, 5b Crazyflie to close). Anyone without an iPhone has a 100%-equivalent Python checkpoint.
- **Track D — advanced going-further (docs only, not lessons)**: signpost docs such as swarm, tracking robustness (Kalman), segmentation labelling, etc., pointing the way for those who "want to go further" without blocking graduation. (Sensor noise / domain randomization have been promoted to a formal lesson, L20, and removed from this track.)
- **Track E — sim-to-real bring-up (real-hardware landing infrastructure)**: L23 flight black box (telemetry + replay) → L24 Tello cheap-real-hardware stepping stone → L25 sim-to-real gap measurement → L26 field-test SOP + Taiwan regulations. This track turns "can fly" into "flies legally, safely, reviewably, and verifiably on real hardware" — the last mile before the models trained on the main line / Track B truly land.

Relationships between tracks: the models Track B trains (L17 depth / L8 person) are inputs to Track E (L25 gap measurement) and Track C (L22 on-board narrative); Track E's `nanodrone/safety.py` (extracted in L24) is shared by Track C Phase 4/5 and the L26 SOP; Track C's `nanodrone.protocol` (L27) is the single source of truth shared across the Tello / Crazyflie / Apple ends.

## 3. Recommended build order

**Do Track A's L11 first, no exceptions.** Why: L11 is the highest-value, lowest-risk lesson in the whole roadmap — it needs zero hardware and purely factors the duplicated while loop from 11+ scripts into `nanodrone.mission`, which both pays down real technical debt (confirmed by grep) and plants the state-machine mental model common to ROS / PX4, and **every later lesson depends on it**. Once L11 starts, three things must be done right in one pass: (a) the `mission runner` **must not hard-code `num_drones=1`** (reserve a clean interface for the future); (b) build in a **Failsafe/Return state**; (c) formally add `nanodrone/mission.py` to `setup/requirements` and `.github` CI (including the cross-lesson integration CI).

After that, the order splits into two layers: "core required" and "advanced / elective branches."

### Core required main line (recommended in order)

1. **L11** (foundation, must be first in sequence)
2. **L12** (the simplest "command→state" integration, medium) — depends on L11
3. **L13** (the first multimodal mini-capstone, advanced, includes re-training a confirmation classifier) — depends on L11, L12, L8
4. **L14a** (mapping & patrol, advanced) — depends on L11; **can run in parallel with L12/L13** (depends only on L11, not on the voice line)
5. **L14b** (on-board convergence, advanced, the required lesson that closes the on-board crack — not skippable) — depends on L14a, L4, L13
6. **L16** (graduation project) — scheduled last; it grades all the capabilities above

### Track B perception-depth branch (advanced elective, but core for anyone who "really wants to get on-board")

7. **L17 monocular depth** (medium) — depends on L2/L3/L4. **The entry to this branch**: pure supervision, directly reusing the `gen_dataset` pattern, lowest risk; doing it first immediately verifies "we really can train a dense model."
8. **L18 optical flow / VO** (medium) — depends on L1/L3/L8/L4. Independent of L17, can run in parallel.
9. **L19 multi-obstacle RL** (advanced) — depends on L3, L17 (depth as observation). Can only generalize once the perception modalities are in place.
10. **L20 domain randomization** (medium) — depends on L17, L2. Needs an already-running depth model as the subject under test.
11. **L21 distillation + compression** (advanced) — depends on L4, L17+L20, L3. Needs a larger model raised earlier as the teacher for "compression" to mean anything.
12. **L22 distill multiple capabilities into a single policy** (advanced, the capstone of the on-board deepening line) — depends on L8, L19, L21, L4. Can only proceed once both the avoidance (L19) and following (L8) teachers exist.

> Track B ordering principle: first unlock new perception modalities (depth, optical flow) → feed them into harder decisions (multi-obstacle RL) → close the sim-to-real gap (domain randomization) → slim down for on-board (distillation / compression) → unify capabilities (distillation capstone) → **anticipate the future (L29 nano world model: latent prediction flown closed-loop by a vision-only latent MPC, distilled on-board)** — the predictive frontier that caps Track B.

### Track E real-hardware landing branch ($0 sim first, hardware labelled after)

13. **L23 flight black box** (beginner, pure $0 sim) — depends on L1, bridge phase 1. The entry to Track E; first nail down the log format / replay tools in sim.
14. **L24 Tello stepping stone** (advanced, needs a ~US$100 Tello; FakeTello means $0 in CI) — depends on L23, L11 Failsafe (the extracted `nanodrone/safety.py`), bridge phase 1.
15. **L25 sim-to-real gap measurement** (advanced, $0 to run the samples; shooting your own real-hardware gap needs the L24 Tello) — depends on the L8 (or L3) model, L18 (understanding imperfect sensing), L24 (capturing real-hardware imagery, optional). **Echoes and circles back to the motivation for L20 domain randomization.**
16. **L26 field-test SOP + Taiwan regulations** (medium, $0 against sim / no hardware) — depends on L23 (log), L11/L24 (safety module), L24 (real-hardware target, optional).

### Track C Apple product-line branch (parallel elective, needs Apple hardware; anyone without an iPhone has a 100%-equivalent Python checkpoint)

17. **L27 protocol extraction `nanodrone.protocol`** (beginner, $0) — depends on bridge phase 1. **The single source of truth for the whole Apple product line and the real-hardware line**, and must be done first, or Phase 2–5 and Tello / Crazyflie will each reparse JSON and the protocol will inevitably drift. **Strongly recommended to pay down this protocol debt at the same time as L11.**
18. **L28 parser-evaluation arena** (medium, $0, runnable in CI) — depends on L27, L12, L10. Turns Phase 3's "counter-example control group" into a quantifiable offline harness.
19. **DroneVoice Phase 2** (medium, needs iPhone/Xcode; $0 without an iPhone) — depends on L27, L9
20. **DroneVoice Phase 3** (advanced, needs iOS 26 + Apple Intelligence) — depends on Phase 2, L27, L28
21. **DroneVoice Phase 4** (advanced, SwiftUI + telemetry + failsafe UI) — depends on L27, Phase 3, L23 (telemetry format), L4/L24 (failsafe concept)
22. **DroneVoice Phase 5a (Tello) / 5b (Crazyflie)** (advanced, hardware labelled) — depends on L27, Phase 4, L24 (Tello backend) / L4 (cflib)

**Can run in parallel**: Track B, Track E, and Track C are decoupled from one another and can be advanced separately. L14a and L12/L13 are mutually independent, so a team can split up. **The fastest path to a real-hardware demo**: L23→L24 (Tello over Wi-Fi) has a far lower bar than the GAP8 / Crazyflie route. **The path that best reinforces the signature theme**: L17→L20→L21 (train your own dense model → make it sim-to-real robust → compress it into 512KB).

---

## 4. Per-lesson / Phase outlines (five-part)

Lesson order: L11 → L12 → L13 → L14a → L14b → L16 → L17 → L18 → L19 → L20 → L21 → L22 → L23 → L24 → L25 → L26 → L27 → L28 → DroneVoice Phase 2 → Phase 3 → Phase 4 → Phase 5a → Phase 5b. **(Frontier addendum: L29 nano world model — a Track B lesson, buildable right after L22; placed last here as the newest addition.)**

### [Lesson 11] Mission orchestration skeleton: turn the flight loop into a state machine + built-in Failsafe (Track A)

- **Cost** $0 (pure sim, pure refactor) | **Difficulty** medium | **Prereqs** L5 (flight loop), bridge phase 1 (`apply_command` semantics, gentle land)

**Why**: up to L10, every flight script (L5/L6/L7/L8/L9/L10/bridge) copied an almost word-for-word identical while loop: build `CtrlAviary+DSLPIDControl`, compute target/target_yaw each frame, feed `computeControlFromState`, then `sync()` on the GUI path / count steps on the headless path. To string together "take off → find a person → follow → land," you first need something that can manage "which phase am I in now, and when do I switch to the next." In this lesson the beginner learns for the first time: an autonomous robot is not one giant if-else, but a **state machine** — the mental model common to ROS / PX4 / real drones, and the sooner it's established the better. **This is also the turning point of the core theme**: the first 10 lessons were "building capabilities" (training models, writing perception); from this lesson on we move into "composing capabilities" (orchestrating existing building blocks). The README must state this turning point in one paragraph, so the signature theme doesn't seem to silently disappear.

**Concept**: formally encapsulate the existing "two-layer architecture + update target/target_yaw setpoint each frame" pattern into a `nanodrone.mission` module: a `State` base class (`on_enter()` / `step(state_vector)->(target, target_yaw)` / `is_done()`) + a `Mission` runner, where the runner's internal while loop is exactly the shared skeleton from L5/bridge. Built-in states: `Takeoff` (target[2]→1.0, reusing bridge `apply_command`'s takeoff semantics), `Hover`, `GoTo(xyz)`, `Land` (gentle descent of `z-=0.4*dt` per frame, copying bridge's landing logic word-for-word), and **`Failsafe`** (any state detecting a geofence breach / N consecutive frames of perception loss / an external lost-link flag immediately transitions in: first `Hover` to stabilize, then `Land` on timeout). `Failsafe` is the safety net for the "real-hardware autonomy required" of every later lesson; build it into the foundation and run it through the whole course, rather than only verbally requiring it in the L16 rubric. The runner **does not hard-code `num_drones`** (index with `obs[i]` rather than `obs[0]`), reserving a clean interface for any multi-drone extension.

**Hands-on (deliverables)**:
- Add `nanodrone/mission.py`: `State` base class + `Mission` runner + built-in `Takeoff`/`Hover`/`GoTo`/`Land`/`Failsafe` states.
- Add `lessons/11_mission/mission_demo.py`: runs the scripted mission "take off → GoTo(1,0,1.2) → Hover 2s → Land," plus a test case that deliberately triggers a geofence breach to verify `Failsafe`.
- `--selftest` (headless) prints two lines: `MISSION OK: ran 4 states [Takeoff>GoTo>Hover>Land], moved 1.0m, landed at z=0.30` and `FAILSAFE OK: geofence breach -> Hover -> Land, ended safe`. Asserts: the state-transition sequence is correct, the final altitude ≈ ground, horizontal displacement > 0.2m, and after a breach it really enters Failsafe and lands safely.

**Checkpoint ✅**: `MISSION OK` + `FAILSAFE OK` two green lines, CI passing; in GUI mode use `chase_cam` to watch it execute in order.

**Going further**: compare the runner's while loop to a ROS 2 behaviour tree / PX4 commander, explaining how this state machine migrates to a real flight controller.

**Reuse**: reuse word-for-word the `run()` while-loop skeleton and gentle land from `bridge/sim_server.py`; `GoTo`'s setpoint clip reuses the `BOX_XY`/`BOX_Z` geofence; `nanodrone.view`'s `setup_view`/`chase_cam`; the "scripted + print OK + assert" CI template behind `SelftestInput`; `Takeoff`/`Land` semantics aligned with bridge `apply_command`.

---

### [Lesson 12] Voice-driven state transitions: switch mission phases by speaking (with a source→event adapter) (Track A)

- **Cost** $0 (CI needs no microphone at all; for real voice, reuse L9/L10's free Vosk / self-trained model) | **Difficulty** medium | **Prereqs** L11 (state machine), L9 (`parse_command`), L10 (`KwsListener`)

**Why**: L9/L10 taught "voice → command → continuous velocity," which is "hold-the-stick" style continuous control. In a real mission you say things like "take off," "follow me," "land" — high-level commands that **switch the whole behaviour**. This lesson shows the beginner: route the same spoken sentence to a state machine, and it upgrades from "keep drifting forward" to "trigger a one-time phase transition." It also demonstrates "the command front-end is swappable" — keyboard, voice, KWS, and the later app JSON are all just different sources producing the same kind of transition event.

**Concept (an explicit adapter layer)**: `parse_command` (returns a `(fwd,strafe,up,yaw)` velocity tuple or `'land'`/`None`), `KwsListener` (returns a label string), and `apply_command` (directly mutates target) have fundamentally different output types, so an adapter layer is needed in between. This lesson explicitly adds `nanodrone/mission_events.py`, defining a **source→event adapter** layer:

| Source | Raw output | Adapter rule | Mission event produced |
|---|---|---|---|
| L9 `parse_command` | `(fwd,strafe,up,yaw)` tuple / `'land'` / `None` | `'land'`→land; sustained positive fwd and context=follow→follow; `None`/all-zero→(emit no event) | `takeoff`/`follow`/`land`/`stop` |
| L10 `KwsListener.poll()` | label string + conf | only trust if conf>0.6; look up the label directly; `background`→emit no event | same as above (discrete label→event) |
| bridge `apply_command` | mutates target/yaw + mode | mode=`'land'`→land, `'emergency'`→stop; displacement actions→(continuous control, no phase switch) | `land`/`stop` |

The runner adds an `event->transition` lookup table (reusing L9 `_CMDS`' "longest-match first" ordering and L10's `background` reject-class idea, so noise doesn't accidentally trigger a phase switch). The voice thread uses `KwsListener.poll()` in non-blocking mode, and the flight loop still runs every frame.

**Hands-on (deliverables)**:
- Add `nanodrone/mission_events.py` (three adapters + the `event->transition` table).
- `lessons/12_voice_mission/voice_mission.py`: voice (or `--selftest` scripted events) drives "Idle→(takeoff)→Takeoff→Hover→(land)→Land."
- `--selftest` injects a timestamped event sequence (reusing L9's `ScriptedVoice` approach, no microphone needed), printing `VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed, 1 noise-event rejected`. Asserts the transition count, the final state, and that the deliberately injected `background` / low-conf noise events are indeed rejected (no transition triggered).

**Checkpoint ✅**: `VOICE-MISSION OK` green; the noise-rejection assert passes.

**Going further**: treat the adapter as an "event-source family," foreshadowing that DroneVoice's JSON is just a new member of the same family.

**Reuse**: L11 `mission` runner and `Takeoff`/`Hover`/`Land`; L9 `voice.py`'s `parse_command` and `ScriptedVoice` timestamp injection; L10 `kws_fly.py`'s `KwsListener.poll()` non-blocking polling and its `conf>0.6` reject threshold, the `background` quiet-class "if unsure, do nothing" design.

---

### [Lesson 13] Multimodal full mission (mini-capstone): take off → find a person → follow → land on hearing "land" (with re-training a classifier) (Track A)

- **Cost** $0 (reuse L8's sim-self-produced data to train PersonCNN; the new lightweight intruder / background classifier is likewise self-produced in sim) | **Difficulty** advanced | **Prereqs** L11, L12, L8 (PersonCNN and the follow loop)

**Why**: this is the first time the whole course is sewn into a full mission you can describe in one plain sentence, and the direct implementation of the topic's original phrasing. Vision (L8's learned person-finding) handles perception, voice (L12) handles the high-level command, the state machine (L11) handles orchestration, and the two-layer controller handles stable flight. In this lesson the beginner gets the first finished product they can describe to the camera: "this drone finds me on its own, follows me, and lands when I shout 'land.'" It also honestly exposes the problems that only appear during integration: what should the state machine do when perception is lost, and how do voice and vision events avoid fighting each other. **And it requires students to use sim-self-produced data to re-train a lightweight "target person vs background" binary confirmation classifier**, hung in front of the Search→Follow transition as a "confirmation gate" (to avoid mistaking a background colour blob for a person and transitioning to Follow). This makes the signature theme "generic detection isn't robust enough → train your own small classifier" appear once more before the capstone, organically combined with the integration task rather than bolted on.

**Concept (event-priority table + loss-and-recapture state diagram)**: wrap the whole L8 "follow a real person" into a composite state slotted into the L11 state machine:

```
Takeoff
  └→ Search (slow yaw scan in place, run detection every PERCEPTION_EVERY frames)
        ├─ cnn_bearing hit AND distance<MAX_RANGE AND [newly-trained classifier confirms=person] → Follow
        └─ scanned a full circle with no hit → keep scanning (timeout T_search → Failsafe)
  Follow (port L8 world_point→target_yaw=theta, reach=dist-DESIRED_DIST convergence)
        └─ lose target for N=8 consecutive frames → fall back to Search
  Land (voice land event, highest priority)
```

**Event-priority table (hard rule)**: `land`(emergency/voice) > `Failsafe`(lost-link/breach) > visual state transitions (Search↔Follow) > continuous control. The `land` event can fire immediately in any state at the highest priority; visual events never override land. The only new pieces are the state-transition conditions, the loss-and-recapture strategy, and the new classifier confirmation gate; the perception and follow math fully reuse L8.

**Hands-on (deliverables)**:
- `lessons/13_find_follow_land/train_confirm.py`: sim-self-produce "person vs background" data + train a tiny CNN confirmer. `--selftest` prints `CONFIRM-CNN OK: trained on N samples, val acc>0.9`.
- `lessons/13_find_follow_land/mission.py`: the full mission. `--headless` uses L8 `scripted_person_xy` to walk a circle + an L12 timestamped land event (injected at ~12 s), printing `CAPSTONE-MINI OK: Search→Follow in Ns (confirm-cnn gated), tracked K frames mean bearing err X deg, land event→landed at z=0.30`. Asserts: (a) successful Search→Follow through the classifier confirmation gate (b) mean true bearing error < 18° during Follow (measured independently via `true_bearing_deg`, reusing the L8 threshold) (c) on receiving land it really lands (d) inject a fake background target, and the classifier confirmation gate blocks it without erroneously transitioning to Follow.

**Checkpoint ✅**: `CONFIRM-CNN OK` + `CAPSTONE-MINI OK` two green lines, including the false-trigger rejection assert.

**Going further**: an honest discussion — sim uses `scripted_person` and ground-truth bearing for the checkpoint, but real hardware has no ground-truth and people get occluded; point to Track D's Kalman-filter recapture.

**Reuse**: L11 mission runner + `Takeoff`/`Land`/`Failsafe`; L8 `follow_real.py`'s `cnn_bearing`/`depth_at_bearing`/`world_point` follow math, PersonCNN, and `person.py`'s `build_person`/`move_person`/`true_bearing_deg`/`scripted_person_xy`; the L8 self-produced-data training flow (the `gen_person_dataset`/`train_person_cnn` pattern) reused for the new confirmer; L12's voice events→transitions and priority.

---

### [Lesson 14a] Simple mapping & autonomous patrol: sweep the space and mark the obstacles (Track B)

- **Cost** $0 (pure sim, matplotlib is already a dependency) | **Difficulty** advanced | **Prereqs** L11 (`GoTo` waypoint chaining), L2 (image capture / ranging)

**Why**: earlier missions all revolved around "one target / one person," but real autonomy (PULP-Dronet, inspection drones) also needs the ability to "cover a region of space." This lesson gives the beginner their first concept of **spatial memory**: the drone records the obstacles it has seen onto a 2D occupancy grid and patrols along preset waypoints. It fills the biggest perception gap — depth has so far only been used for single-point ranging (`dep[cy,cx]`), never the whole depth map.

**Concept (honestly labelled as new capability)**: **both the occupancy-grid projection and the multi-obstacle scene builder are new code, not "reusing the L3 scene"** (L3 has only one pillar and is bound to the RL-specific `AvoidAviary`, not reusable). Turn each column of the (downsampled) full depth map into a bundle of range readings, and use the same geometry as `world_point` to project obstacle points onto a numpy 2D occupancy grid (grid the geofence range, increment hit cells by +1). The patrol itself is the L11 state machine chaining a loop of `GoTo` waypoints (`GoTo→…→Land`), scanning and updating the map at each waypoint. Factor the occupancy-grid logic into a new module **`nanodrone/map.py`** (shared by L14b and L16). The decision is still a high-level setpoint, the PID handles stable flight — the two-layer architecture holds.

**Hands-on (deliverables)**:
- Add `nanodrone/map.py` (occupancy grid + depth-column→world projection).
- Add `lessons/14a_map_patrol/scene.py` (a multi-pillar obstacle scene builder, **self-contained, not reusing L3**).
- `lessons/14a_map_patrol/patrol.py`: patrol 4 corner waypoints, build the map while flying, and save `output/map.png` at the end (matplotlib, following the L2 save-image convention). `--headless` prints `PATROL OK: visited 4/4 waypoints, mapped C occupied cells, obstacles at [(x,y),...]`. Asserts: (a) all four waypoints reached (b) occupied cells really exist near the true coordinates of the two known pillars.

**Checkpoint ✅**: `PATROL OK` green, `map.png` produced.

**Going further**: occupancy-grid resolution × range = memory footprint, leading into L14b's "will this fit on GAP8."

**Reuse**: L11 mission runner + `GoTo`/`Land` waypoint chaining; `nanodrone.detect`'s `linearize_depth` and `world_point` geometry; L2 `perception_demo`'s image capture and save-image; `env._getDroneImages` depth channel.

---

### [Lesson 14b] Perception scheduling & quantization under the on-board budget: sew the mission capabilities back onto GAP8 (Track B)

- **Cost** $0 (pure-sim measurement + quantization; real-hardware verification optional, reusing L4's ~US$545 Crazyflie AI bundle) | **Difficulty** advanced | **Prereqs** L14a, L4 (`quantize_cnn.py` int8/ONNX/<512KB), L13 (the perception model being quantized)

**Why (closing the "consistency with the end goal" crack — this is the roadmap's strategic patch)**: L11–L14a are all host-side, sim-only orchestration Python, and never went back to ask "how does this capability get on-board." The course's end point is int8 on GAP8, <512KB, offline self-flight. This lesson sews the new capabilities together with L4's deployment reality, honestly answering three questions: (1) `PERCEPTION_EVERY=6` is a hand-tuned expedient — what is the real on-board inference latency? (2) After quantizing L13's confirmation CNN / L8's PersonCNN to int8, how much accuracy drops, and does it fit under <512KB? (3) Will the occupancy grid's memory fit on the 256KB L2, and how do we lower the resolution? This lesson formally couples "spatial memory + learned perception" with "the on-board compute budget" — the key lesson that keeps the course **close to real hardware** rather than drifting away.

**Concept**: reuse L4 `quantize_cnn.py` to convert the L13 confirmation CNN to int8 ONNX, and measure (a) the accuracy difference before vs after quantization (b) model size vs the <512KB budget (c) under a host-simulated "on-board inference latency," the effect of perception frequency on state-machine control stability — inject latency via a tunable `INFER_LATENCY_MS` parameter, plot the "latency↑ → follow bearing error↑" curve, and explain why `PERCEPTION_EVERY` can't be naively lowered. An honest discussion of the **sim-to-real gap**: sim is perfect ground-truth state, but real hardware has IMU / position noise and noisy perception — pointing to L20's domain randomization.

**Hands-on (deliverables)**:
- `lessons/14b_onboard_budget/quantize_confirm.py`: quantize the L13 confirmation CNN to int8 ONNX. `--selftest` prints `QUANT OK: int8 model 312KB < 512KB budget, val acc 0.93->0.91 (drop 0.02)`. Asserts the model is <512KB and the accuracy drop is < threshold.
- `lessons/14b_onboard_budget/latency_sim.py`: inject `INFER_LATENCY_MS` to run the L13 mission and measure bearing error. `--selftest` prints `LATENCY OK: at 80ms infer, mean bearing err 16.2deg < 18 (stable); grid fits 64x64 int8 = 4KB`. Asserts control is still stable at reasonable latency and the occupancy-grid memory is < the on-board budget.

**Checkpoint ✅**: `QUANT OK` + `LATENCY OK` green.

**Going further**: real-hardware optional — actually flash the quantized model into the AI-deck/GAP8 (following the L4 flow), and measure the real latency against the sim prediction.

**Reuse**: L4 `quantize_cnn.py`'s int8/ONNX quantization flow and <512KB budget check; L13's confirmation CNN and mission; L14a `nanodrone/map.py`'s occupancy grid (measuring its memory); L8 `cnn_bearing`/`depth_at_bearing`.

---

### [Lesson 16] Graduation project & rubric: design your own mission (Track A)

- **Cost** $0 (sim-first graduation; real-hardware demo optional, reusing L4's ~US$545 Crazyflie or DroneVoice's ~US$100 Tello) | **Difficulty** advanced | **Prereqs** L11, L12, L13, L14a, L14b

**Why**: the whole course converges here into a capstone where the student "sets their own task, integrates it themselves, and can show it off." Every earlier lesson gave a fixed task; the graduation project has students assemble a new task out of the `nanodrone.mission` building blocks (e.g. "patrol → spot an intruder → follow and report by voice → land on 'land'"), self-assessed against a clear rubric. It is also the terminal stop of the all-$0 sim-first journey, and gives the bridge to real hardware (L4 Crazyflie / DroneVoice Phase 5 Tello).

**Concept (explicitly account for the theme's turning point + tie back to the counter-example)**: teaches no new algorithm; provides a capstone template and rubric: use the L11 state machine to compose ≥3 chosen capabilities out of L12 (voice) + L13 (find/follow person / re-trained classifier) + L14a (mapping & patrol) + L14b (on-board budget) into a custom task graph. The README must, in one paragraph, **formally account for the core theme's arc**: from "the generic model isn't good enough → train your own small model" (L3/L8/L10/L13 confirmer) to "orchestrate with existing capability building blocks" (L11–L16), and tie it back, in a paragraph of contrast, to DroneVoice Phase 3's counter-example that "a generic large model + structured constraints is enough" (when to train vs when not to), so the signature theme doesn't silently disappear. Provide a mission validator, upgrading the ground rule "`--selftest` + print OK + assert" into "the student's own task must also `--selftest`." Rubric dimensions: integration breadth, `--selftest` green (hard gate), safety (geofence / failsafe / loss-recapture, must actually use the L11 `Failsafe` state), whether it includes on-board considerations (L14b), bilingual docs, and a demo video.

**Hands-on (deliverables)**:
- `lessons/16_capstone/`: (a) a `template_mission.py` template + bilingual README explanation + a `RUBRIC.md` grading sheet (percentage scale, `XXX OK` green as a hard gate); (b) `validate_mission.py` mission validator, printing `CAPSTONE OK: graph valid (S states, T transitions), has Takeoff+Land+Failsafe, all transitions guarded, selftest green`. Asserts the graph is valid, includes Failsafe, and all transitions have trigger conditions. The template task itself ships a `--selftest` as a demonstration.

**Checkpoint ✅**: `CAPSTONE OK` green; the student's custom task must also be `--selftest` green on its own.

**Going further**: point to the real-hardware route via L4 and DroneVoice Phase 5, moving the graduation work onto a Tello / Crazyflie.

**Reuse**: the full L11 `nanodrone.mission` (including Failsafe); L12/L13/L14a/L14b as assemblable capability building blocks; the whole course's "`--selftest` + OK + assert + bilingual docs" ground rules as hard rubric metrics.

---

### [Lesson 17] Monocular depth-estimation CNN: training a dense model for the first time (Track B)

- **Cost** $0 (pure sim, self-produced privileged labels) | **Difficulty** medium | **Prereqs** L2 (`detect.linearize_depth`), L3 (`TinyDronet` / training skeleton), L4 (footprint/ONNX arithmetic)

**Why**: depth is currently only used for single-point ranging (`detect_blob`'s `dep[cy,cx]`, `follow_real`'s `depth_at_bearing` taking a small patch); the whole HxW depth map has never been learned. The pain point points straight at the end goal: the real AI-deck has only a grayscale camera and no depth sensor, so to avoid obstacles / measure range you must "guess depth from a single image" — exactly a re-appearance of the classic "generic rules aren't enough → train your own small model" reason (L3/L8), turning the simulator's idle depth channel into free dense privileged labels. This lesson is the entry to the Track B perception-depth branch.

**Concept**: supervised dense regression: image → per-pixel depth (log-depth + scale-invariant loss); the difference between an encoder-decoder and L3's pure encoder; why a dense depth map can feed downstream avoidance (L19). GAP8 limits: squeeze resolution to 64×64, downsample the output, and the int8 footprint must be <512KB (reusing the L4 arithmetic).

**Hands-on (deliverables)**:
- `lessons/17_depth/gen_depth_dataset.py`: sim-self-produce, with `env._getDroneImages` grabbing rgb and the whole dep at once, `linearize_depth` converting each pixel to meters as the label, saving `output/depth_dataset.npz` (X/y format same as L3/L8).
- `lessons/17_depth/train_depth_cnn.py`: `TinyDepthNet`, encoder directly copying `TinyDronet.features`' three conv layers, plus a lightweight upsampling head.
- `lessons/17_depth/depth_demo.py`: fly a circle and save a predicted-vs-truth heatmap PNG.
- `--selftest` (headless) prints `DEPTH OK: trained N samples, val AbsRel=0.XX, int8 footprint=YYY KB (<512 fits)`. Asserts `AbsRel<0.25` and `footprint<512`.

**Checkpoint ✅**: `DEPTH OK` green, heatmap PNG produced, CI passing.

**Going further**: dense depth feeds L19 multi-obstacle RL as observation; points to L20 "clean sim depth will collapse on real hardware."

**Reuse**: `gen_dataset.py`'s `CtrlAviary+DSLPIDControl` sampling loop and box-reset logic; `nanodrone.linearize_depth` (`detect.py`) applied per pixel; `train_cnn.py`'s `TinyDronet.features` three conv layers as the encoder, the `device='mps'` and npz training skeleton; L4 `quantize_cnn`'s `n_params/1024` footprint and ONNX export to compute the int8 size. Honestly labelled: the encoder-decoder upsampling head is new (L3 has only an encoder), and the scale-invariant loss is new.

---

### [Lesson 18] Optical flow / visual odometry: self-estimate state without GPS (Track B)

- **Cost** $0 (pure sim, privileged displacement labels) | **Difficulty** medium | **Prereqs** L1 (hover), L3 (training skeleton / trajectory plot), L8 (sampling template), L4 (footprint)

**Why**: currently every flight loop eats the "simulator privileged position" from `env._getDroneStateVector` / `obs[0]` (e.g. `follow_real`'s `drone_pos=state[0:3]`); real hardware has no such external localization. The pain point: to fly autonomously offline you must "estimate how much you've moved from the on-board camera alone." This is a new perception modality (motion across two consecutive frames), and a small CNN can be trained to regress pixel displacement → body velocity, continuing the signature main line while filling in the state estimation that autonomy requires.

**Concept**: optical flow = the pixel displacement field across two consecutive frames; use the known simulator displacement difference as a privileged label to learn "flow → body velocity"; integrate to get odometry and the concept of drift; why downstream setpoint control (two-layer architecture) needs it. Honestly labelled real-hardware gap: real indoor localization needs a downward camera (Crazyflie Flow deck v2, ~US$45, not required for this lesson), and integration accumulates drift — position is an estimate, not ground truth. GAP8: two stacked 64×64 grayscale frames as input, 2–3 velocity numbers as output, int8 <512KB.

**Hands-on (deliverables)**:
- `lessons/18_flow/gen_flow_dataset.py`: in sim, randomly translate / yaw the hovering drone, saving the two adjacent frames + the true displacement difference `(dx,dy,dyaw)` as the label.
- `lessons/18_flow/train_flow_net.py`: `FlowNet` (two-frame stack → small conv → 3-number regression).
- `lessons/18_flow/odom_demo.py`: fly a preset path and plot "integrated estimated trajectory vs true trajectory" as a top-down PNG.
- `--selftest` prints `FLOW OK: N pairs, vel MAE=0.0X m/s, drift over 5s=0.XX m, int8=YYY KB`. Asserts `vel MAE<0.1` and `footprint<512`, and reports the drift so the student sees the sim-to-real concern.

**Checkpoint ✅**: `FLOW OK` green, trajectory PNG produced.

**Going further**: feed the odometry back into the L11 state machine as a "fallback localization when there is no privileged position"; point to L25's real-hardware optical-flow degradation.

**Reuse**: `gen_person_dataset.py`'s hover-then-capture sampling template; `train_person_cnn.py`'s training loop and the `BEARING_SCALE`-style label-scaling convention (changed to velocity scaling); `train_rl.py`'s `_save_trajectory_plot` for plotting trajectory; the L4 footprint arithmetic; `detect.py`'s `fov_deg` geometry concept for scale conversion. Honestly labelled: computing over the whole image (cv2 optical flow or a two-frame CNN) is the first time sim uses this — earlier it only point-sampled. This lesson merges two angles — classical optical-flow principles (cv2) and "train your own small CNN (privileged labels) to regress velocity" — into one lesson, rather than opening two separate optical-flow lessons.

---

### [Lesson 19] Harder multi-obstacle RL course: fed by perception, generalizes (Track B)

- **Cost** $0 (pure sim) | **Difficulty** advanced | **Prereqs** L3 (`AvoidAviary`/PPO full set), L17 (depth as observation)

**Why**: the existing RL has only one fixed pillar and is hard-bound to `AvoidAviary` (the code comment admits it: only a fixed layout lets it learn to weave around using KIN observation alone; randomize and you must feed obstacle info into the observation). The pain point: real avoidance has multiple obstacles, each time different. To generalize you must put the depth (or obstacle bearing) learned in L17 into the observation — this truly connects the perception lessons' results into decision-making, the high-point prelude of Track B.

**Concept**: fold a perception summary (the depth CNN's output of several range rays / nearest-obstacle bearing+distance) into the RL observation → the policy generalizes to random layouts; a curriculum increasing from 1 pillar to 3 pillars; reward shaping reuses the existing progress+crash+goal structure. GAP8: the policy MLP is already tiny, so the point is to demonstrate the "perception front-end int8 + control back-end" split deployment.

**Hands-on (deliverables)**:
- `lessons/19_multi_avoid/multi_avoid_aviary.py`: an `AvoidAviary` subclass that, on reset, randomly spawns 1–3 pillars and folds each pillar's nearest distance / bearing into the observation.
- `lessons/19_multi_avoid/train_multi_rl.py`: reusing PPO + curriculum timesteps.
- eval plots a multi-pillar weaving trajectory PNG.
- `--selftest` (few-step smoke) prints `MULTI-AVOID OK: trained Ns, success X/10 on random layouts, 0 crash in selftest ep`. Asserts at least one crash-free trajectory completed + the observation dimension includes obstacle info.

**Checkpoint ✅**: `MULTI-AVOID OK` green.

**Going further**: this avoidance policy is L22's avoidance teacher for multi-capability distillation; points to L20 randomizing the training arena.

**Reuse**: `avoid_aviary.py` almost wholesale as the base (`_spawn_obstacle` changed to a loop spawning multiple pillars, `_computeReward`/`_Terminated`/`_Truncated` reusing progress+crash+goal); `train_rl.py`'s PPO settings (`ent_coef=0.01`), `make_vec_env`, evaluate, and `_save_trajectory_plot`; the L17 depth CNN inference as the observation front-end; **directly reuse L14a's multi-pillar `scene.py` builder** (don't rebuild the scene). Honestly labelled: "folding perception into the observation + curriculum" is new, the real gap the `avoid_aviary` comment explicitly names.

---

### [Lesson 20] Domain randomization: shrink the sim-to-real gap (Track B)

- **Cost** $0 (pure sim) | **Difficulty** medium | **Prereqs** L17 (depth model and data pipeline), L2 (visual scene construction)

**Why**: the L17–L19 models are all trained on clean, noiseless sim imagery (sensor noise, segmentation, domain randomization have never been used so far), and collapse the moment they hit real hardware. The pain point: sim is too perfect → the model overfits to the sim's appearance. The fix is to randomize appearance / lighting / noise during training, forcing the model to learn robust features — this is the key lesson that lets "the small model you trained yourself" really get on-board, still $0 and entirely in sim. It directly answers "how to shrink" the sim-to-real gap measured by L25.

**Concept**: domain randomization: randomize wall / floor colours, lighting direction, camera noise / blur, obstacle size and colour; why this is more cost-effective than "making the sim more photorealistic"; use a randomization-retrained L17 depth CNN compared against the baseline to prove improved robustness.

**Hands-on (deliverables)**:
- `lessons/20_domain_rand/randomize.py`: a set of reusable randomizers (`changeVisualShape` to change PyBullet colours, add Gaussian image noise, jitter lighting).
- `lessons/20_domain_rand/retrain_depth_dr.py`: call randomize then re-run the L17 training.
- a comparison script compares baseline vs DR model on a "deliberately recoloured test scene."
- `--selftest` prints `DR OK: baseline AbsRel=0.4X on shifted scene, DR model=0.2X (robustness up YY%)`. Asserts the DR model's error on the shifted scene is significantly lower than the baseline.

**Checkpoint ✅**: `DR OK` green.

**Going further**: apply the same randomizer set to L18 optical flow and L19 RL scenes; point to L25 using real-hardware imagery to verify whether DR really works.

**Reuse**: the full L17 `gen_depth_dataset.py` / `train_depth_cnn.py` (randomize inserted before the image capture in the sampling loop); `perception_demo.py` / `gen_dataset.py`'s `createVisualShape rgbaColor` pattern changed to use `changeVisualShape` for dynamic recolouring; `person.py`'s multi-colour modelling idea as a "hard sample" reference. Honestly labelled: noise / lighting / randomization are the first time the simulator uses them.

---

### [Lesson 21] Knowledge distillation + model compression: extending L4's quantize-and-get-on-board (Track B)

- **Cost** $0 to train; hardware still reuses L4's already-labelled ~US$545 AI bundle, **no double billing** | **Difficulty** advanced | **Prereqs** L4 (quantize/ONNX/footprint), L17+L20 (teacher model), L3 (training skeleton)

**Why**: L4 only did the footprint check and ONNX export, never actually "compressed." The pain point: for accuracy, L17/L20 may raise a depth model larger than `TinyDronet`, which won't necessarily fit under 512KB. The fix: use the large model as a teacher to distill a smaller student model, then quantize — pushing L4's int8/<512KB ground rule forward into "actively compress until it fits on-board." This complements L14b (on-board convergence, measuring the quantization drop): L14b measures "will it fit," L21 teaches "how to actively compress when it won't fit."

**Concept**: knowledge distillation: the teacher's soft outputs guide the student (for dense depth, the teacher's prediction map serves as extra supervision); the accuracy difference between distillation vs directly training a small model; the accuracy drop from post-training int8 quantization; use the L4 formula to verify the student really is <512KB.

**Hands-on (deliverables)**:
- `lessons/21_distill/distill_depth.py`: load L20's large DR depth model as the teacher, train a smaller student (conv channels halved).
- `lessons/21_distill/compress_report.py`: extend L4 `quantize_cnn` to print a three-column teacher-vs-student comparison of parameter count / footprint / accuracy + export the student ONNX.
- `--selftest` prints `DISTILL OK: teacher YYY KB / student ZZZ KB (<512), AbsRel teacher=0.2X student=0.2Y (kept WW%)`. Asserts the student `footprint<512` and the accuracy-retention rate > threshold.

**Checkpoint ✅**: `DISTILL OK` green.

**Going further**: the distillation flow is the prerequisite for L22's multi-teacher unification; against L14b's latency curve, discuss "a small student infers faster."

**Reuse**: L4 `quantize_cnn.py`'s footprint computation, ONNX export, and accuracy sanity — almost the whole three parts reused; `train_cnn.py`'s training skeleton; L17/L20's depth model and dataset as teacher and evaluation set; `TinyDronet`/`PersonCNN`'s `features` architecture shrunk into the student.

---

### [Lesson 22] Distill multiple capabilities into a single on-board policy (Track B capstone)

- **Cost** $0 (pure sim) | **Difficulty** advanced | **Prereqs** L8 (follow teacher), L19 (avoidance teacher), L21 (distillation flow), L4 (footprint)

**Why**: currently avoidance (L19) and following (L8) are two independent models / loops, and the real GAP8 can neither run multiple networks nor switch between them. The pain point: the on-board compute only fits one policy. The fix: distill the behaviour of multiple teachers (the avoidance policy + the follow CNN) into "one" small policy network — this is the finale of the whole on-board AI deepening main line, integrating all the earlier self-trained small models into a single on-board brain. The difference from the L16 graduation project: L16 is a host-side capstone of "orchestrate with mission building blocks," and L22 is an on-board capstone of "compress multiple capabilities into a single int8 network" — each closes a different main line.

**Concept**: policy/behaviour distillation: in mixed scenarios (must follow a person while weaving around obstacles), use the teachers to generate (observation→action) demonstration data, then train a student policy to imitate; mode-switching vs a unified policy; the footprint and latency advantages of a single int8 network.

**Hands-on (deliverables)**:
- `lessons/22_unified/gen_policy_dataset.py`: in a scene with both a person + multiple pillars, run the L19 avoidance and L8 follow teachers, take the safer action per scenario, and save `(obs,action)` npz.
- `lessons/22_unified/distill_policy.py`: a small MLP/CNN student imitates.
- `lessons/22_unified/unified_fly.py`: fly a segment that follows a person while avoiding obstacles.
- `--selftest` prints `UNIFIED OK: distilled from 2 teachers, follow err=XX deg & min obstacle dist=0.XX m (no crash), single int8=YYY KB`. Asserts the follow error < threshold AND no crash throughout AND `footprint<512`.

**Checkpoint ✅**: `UNIFIED OK` green.

**Going further**: use the unified policy as the "on-board reflex" for the L16 graduation project or DroneVoice Phase 5b; real-hardware optional flashing into GAP8 (following L4).

**Reuse**: `follow_real.py`'s follow loop / `cnn_bearing`/`depth_at_bearing`/`world_point` as the follow teacher and evaluator; the L19 multi_avoid policy as the avoidance teacher; `train_rl.py` evaluate's success / crash statistics and `_save_trajectory_plot`; the L21 distillation skeleton and L4 footprint verification; the unified flight shell connects the L11 `mission` runner and the L27 `protocol.step_target` (no longer copying `sim_server.py`).

---

### [Lesson 23] Flight black box: telemetry logging and offline replay (Track E entry)

- **Cost** $0 (pure sim, pure software) | **Difficulty** beginner | **Prereqs** L1 (flight loop), bridge phase 1 (the newline-JSON protocol and selftest-injection template)

**Why**: the first thing real-hardware landing needs is not smarter AI, but the ability to "look back at what happened after the flight." Incidents, jitter, and false triggers all have to be reconstructed from the log. First nail down the log format and replay tools in the $0 sim; later Tello (L24) / Crazyflie only need to emit data in the same format to use the same tools for replay, avoiding rewriting analysis scripts every time the platform changes. This is also the best demonstration of the sim-first ground rule.

**Concept**: structured telemetry (each frame writes `timestamp/pos/target/yaw/battery` as newline-JSON, sharing a source with the bridge's existing protocol), a fixed-rate sampled time series, offline replay (feed the recorded targets back into the flight controller to re-enact), headless checkpoint. Explains why newline-JSON rather than binary: human-readable, greppable, and injectable in the L9/L10 `ScriptedVoice` style.

**Hands-on (deliverables)**:
- `lessons/23_telemetry/record_flight.py`: at the end of the shared flight loop, append one JSON record per frame to `logs/*.jsonl`.
- `lessons/23_telemetry/replay_flight.py`: read the jsonl, feed each frame's target back into `CtrlAviary+DSLPIDControl` (or the L11 mission runner) to re-enact, viewable in the GUI.
- `nanodrone/telemetry.py`: factor `FlightLogger.log(state,target,yaw)` / `load_log()` into a reusable module.
- `--selftest`: record prints `RECORD OK: logged N frames, M fields/frame, file=…` (asserts N>0 and a consistent field count per frame); replay prints `REPLAY OK: replayed N frames, end-pos within 0.15 m of logged end` (asserts the replay endpoint is within 0.15 m of the recorded endpoint, proving the replay is faithful).

**Checkpoint ✅**: `RECORD OK` + `REPLAY OK` two green lines.

**Going further**: the log is the prerequisite for L26 SOP's "logging must be on during flight"; points to wiring the log into a visualization dashboard (DroneVoice Phase 4 telemetry UI).

**Reuse**: directly reuse the L11 mission runner's (or `bridge/sim_server.py`'s) `CtrlAviary+DSLPIDControl` + per-frame target loop and `chase_cam`/`sync`; the log line is inserted right after `ctrl.computeControlFromState`. The JSON-line format follows the bridge `serve()` newline-JSON convention. The selftest's scripted injection follows `sim_server.py`'s `(t_s, cmd)` timestamp-list template and `kws_fly.py`'s scripted_label template. Honestly labelled: the log/replay format and tools are genuinely new content (the codebase has no log/replay whatsoever).

---

### [Lesson 24] The first real drone that flies: a cheap Tello over Wi-Fi (Track E)

- **Cost** **needs hardware: a DJI/Ryze Tello, ~US$100**; the software `pip install djitellopy` is free; `--selftest` uses FakeTello so it is $0 and runs in CI | **Difficulty** advanced | **Prereqs** L23 (real hardware must log first), L11 (`Failsafe`, and extract it into `nanodrone/safety.py`), bridge phase 1 (the command protocol and `apply_command` interface), L5/L9 flight semantics

**Why**: the GAP8/AI-deck route (L4, ~US$545, requires soldering and flashing, offline on-board) has a high bar for beginners. A Tello costs only ~US$100, connects over Wi-Fi, and flies with one pip; the AI runs on the laptop and sends commands over Wi-Fi — this is exactly the real-hardware version of the bridge's existing TCP JSON protocol: the same structured command, with the backend swapped from sim to Tello. First get "the command really makes the thing fly" working on the cheapest real hardware that you won't mind crashing, building confidence and sim-to-real intuition, then advance to the Crazyflie's offline on-board. **Honestly labelled**: the Tello's AI is off-board, not offline, and is not the course's final goal; it is proof of "protocol portability" and a safe first step onto real hardware. The codebase currently has no Tello code at all — this is genuinely new content.

**Concept**: connect to real hardware over Wi-Fi, map the bridge/protocol's high-level actions (takeoff/forward/turn_left/land/emergency) to DJITelloPy's `takeoff()`/`move_forward(cm)`/`rotate_ccw(deg)`/`land()`/`emergency()`, unit conversion (the protocol uses meters, the Tello uses centimeters / degrees), the real-hardware two-layer architecture mapping (your AI sends high-level commands, the Tello's built-in flight controller stabilizes, the AI never touches the motors — the same role as the sim's DSLPIDControl), and real-hardware failsafe landing. **This lesson systematizes the scattered failsafe**: add `nanodrone/safety.py` (pure functions: `battery_gate(vbat/pct)`, `geofence_clip(target)` (extracted from bridge), `link_watchdog(last_cmd_t, now)`, `decide_failsafe(...)` returning `'ok'/'low_batt'/'lost_link'/'out_of_bounds'/'estop'`), shared by Tello, Crazyflie, Apple Phase 4, and the L26 SOP, and able to inject synthetic-fault tests in sim (on real hardware you wouldn't dare drop the battery to 3.5V, but sim can). This factors the `Failsafe` semantics built into L11 into a unit-testable, fault-injectable shared module, rather than opening another state-machine lesson.

**Hands-on (deliverables)**:
- `nanodrone/safety.py` (a pure-function safety layer + `--inject low_batt|lost_link|out_of_bounds` to inject faults in sim for testing).
- `lessons/24_tello/tello_backend.py`: `class TelloBackend: apply_command(cmd)` translates the 13 actions into DJITelloPy calls, the same interface as `sim_server.py`'s `apply_command`.
- `lessons/24_tello/fly_tello.py`: connect to the bridge TCP server or read a command list to drive a real Tello, with `nanodrone/safety.py` attached.
- `--selftest` (no hardware connection, uses FakeTello to record received calls) prints `TELLO OK: mapped 13/13 actions to Tello calls (1.0 m forward -> move_forward(100cm), 90 deg -> rotate_ccw(90)), unit conversion verified; safety 4/4 faults triggered correct response`. Asserts each action maps to the correct DJITelloPy call and unit, doesn't actually take off when unconnected, and the four injected faults trigger the expected states.

**Checkpoint ✅**: `TELLO OK` green (including the safety injection test).

**Going further**: swap the Crazyflie controller under the same protocol (DroneVoice Phase 5b); point to L25 using the Tello camera to record video and measure the sim-to-real gap.

**Reuse**: `TelloBackend.apply_command` and L27 `protocol.step_target` share the same action names, distance/degrees defaults (0.5m/30°), and body-frame semantics; `geofence_clip` directly takes the `np.clip(±BOX_XY, BOX_Z)` at the end of `sim_server.py`; `battery_gate` generalizes `fly_crazyflie.py`'s `MIN_TAKEOFF_VOLTAGE` gate; emergency/freeze and the gentle land follow `sim_server.py`'s `mode=='emergency'`/`landing(z-=0.4*dt)`; the FakeTello stub follows `input.py`'s `SelftestInput` "scripted fake backend for CI" template.

---

### [Lesson 25] Move sim-trained models onto real hardware and honestly measure the sim-to-real gap (Track E)

- **Cost** $0 to run (using the bundled sample video + sim); shooting your own real-hardware gap needs the L24 Tello (~US$100) | **Difficulty** advanced | **Prereqs** the L8 (or L3) trained model, L18 (understanding imperfect real-hardware sensing), L24 (obtaining real-hardware imagery, optional)

**Why**: the recurring theme of the whole course is "train a small model on your own data" (L3/L8/L10), but these models were only ever verified in sim. The key step to landing is: put a sim-trained detection / avoidance model onto real-hardware imagery, measure how many points it loses, and understand why (lighting, materials, camera noise, motion blur — sim has none of these). This lesson turns the "sim is perfect vs real hardware is dirty" gap into a measurable number rather than empty talk, and directly leads into why L20 domain randomization matters and whether real-hardware data fine-tuning is worth it.

**Concept**: the sources of the sim-to-real gap (domain shift); run the same model on sim imagery and on real-hardware imagery and compare detection accuracy / bearing error; add synthetic degradation to sim imagery (Gaussian noise, brightness jitter, blur) to approximate real hardware, as lightweight domain randomization; decide "whether to fine-tune with real-hardware data." Be honest: a pure-sim model usually loses points on real hardware.

**Hands-on (deliverables)**:
- `lessons/25_sim2real/measure_gap.py`: the same L8 (or L3) CNN / detector, fed sim imagery and real-hardware / recorded imagery respectively, outputting a comparison table of bearing error and detection rate.
- `nanodrone/degrade.py`: `add_noise`/`jitter_brightness`/`blur` pure functions, to add a real-hardware flavour to sim imagery.
- the L24 Tello-recorded video can be used as real-hardware input; without a Tello, use the bundled sample video.
- `--selftest` prints `SIM2REAL OK: sim bearing-err=… deg, degraded bearing-err=… deg, gap=… deg measured over N frames`. Asserts a non-zero gap can be measured and the pipeline runs through; **does not assert the model must be accurate**, honestly presenting the gap.

**Checkpoint ✅**: `SIM2REAL OK` green (a non-zero gap measured).

**Going further**: use the measured gap as the effectiveness baseline for L20 DR training (the DR model's gap should be smaller); discuss the cost / benefit of real-hardware-data fine-tuning. L20 "randomizes during training for robustness" on the sim side, while L25 "measures how many points are actually lost on real-hardware imagery" — the two push and verify, complementing each other; `degrade.py` and L20 `randomize.py` share the noise / blur primitives.

**Reuse**: the detector directly loads the model from L8 `train_person_cnn.py` and `follow_real.py`'s `cnn_bearing`/`depth_at_bearing`/`true_bearing_deg` measurement approach (already an "estimate vs truth" comparison); or the L3 `train_cnn.py` avoidance CNN. The sim-side imagery follows `_getDroneImages`, and the real-hardware side follows the L24 Tello frames. `degrade.py` and L20 `randomize.py` share the noise / blur primitives (avoiding reinvention).

---

### [Lesson 26] Field-test SOP and Taiwan regulations: turn "can fly" into "flies legally and safely" (Track E close)

- **Cost** $0 (pre-flight checks can run against sim or with no hardware; running against real hardware needs the L24 Tello) | **Difficulty** medium | **Prereqs** L23 (log), L11/L24 (`nanodrone/safety.py`), L24 (real-hardware target, optional)

**Why**: the last mile of real-hardware landing is not code, but process and compliance. Beginners most easily overlook: the pre-takeoff check, who the safety officer is, what to do when something goes wrong, and Taiwan's CAA (Civil Aeronautics Administration) rules for remote-controlled drones on registration / labelling / no-fly zones / weight classes. Light as the Tello/Crazyflie are, you still want to build the SOP habit, so you don't get into trouble the moment you graduate to a big drone. This lesson strings together the L11/L24 failsafe and the L23 log into an executable pre-/in-/post-flight checklist, and automates the "auto-checkable items."

**Concept**: the pre-/in-/post-flight SOP (battery, propellers, airspace, safety officer, RC override, logging on), the key points of Taiwan CAA remote-controlled-drone rules (registration and operation rules by weight class, no-fly / restricted zones — **the course provides a checklist, not legal advice, and reminds you to check the latest official notices yourself**), and automating the programmable pre-flight checks. Explains why even a toy drone needs an SOP: habit formation decides whether you get into trouble when you fly a big drone.

**Hands-on (deliverables)**:
- `lessons/26_field_test/preflight_check.py`: read the real-hardware / sim state, run the automatable pre-flight gate (battery > threshold, `logs/` writable, geofence and takeoff height reasonable, `nanodrone/safety.py` loadable), and only return GO if all pass.
- docs include en + zh-TW "field-test SOP checklist" and "Taiwan CAA checklist (with official source links, reminding you to confirm the latest version yourself)."
- `--selftest` prints `PREFLIGHT OK: 5/5 automated checks pass (battery/log-writable/geofence/takeoff-height/failsafe-importable), GO`. Asserts only GO when all items pass; any failure returns NO-GO and lists the reasons.

**Checkpoint ✅**: `PREFLIGHT OK` green (or NO-GO with clear reasons).

**Going further**: wire the SOP into DroneVoice Phase 4's app-side "pre-takeoff confirmation page"; point to the advanced regulations for flying big drones (out of scope for this lesson).

**Reuse**: `battery_gate` reuses L24 `nanodrone/safety.py` (sourced from `fly_crazyflie.py`); the geofence-reasonableness check reuses safety.py parameters; the log-writable check reuses L23 `nanodrone/telemetry.py`'s `FlightLogger`; the lost-link / e-stop SOP maps to the L11/L24 state machine; the bilingual docs follow the existing `tools/gen_docs.py` en-source + zh-TW flow.

---

### [Lesson 27] Extract the flight protocol into `nanodrone.protocol`: one schema, reused everywhere (Track C up-front technical debt)

- **Cost** $0 (pure sim/CPU, no new packages) | **Difficulty** beginner | **Prereqs** bridge phase 1 (already done)

**Why**: `bridge/sim_server.py`'s `apply_command` binds "the protocol definition (which actions, the distance/degrees defaults, the body-frame math, the geofence)" and "the PyBullet flight loop" into the same file. DroneVoice Phase 2/3/4, Tello (L24), and Crazyflie each have to parse the same JSON — without first extracting a single testable schema, each end will hard-code its own action list and defaults, and the protocol will inevitably drift. This is the biggest technical debt of the whole Apple product line and real-hardware line, and must be paid down first. It also echoes design principle 1 (pay down technical debt first), and demonstrates what it means to "free the contract from the implementation." **Recommended to pay it down at the same time as L11** (L11 extracts the mission while loop, L27 extracts the protocol; the two are orthogonal and don't interfere).

**Concept**: contract-first: define the 13 actions' legal values, fields (`distance` default 0.5m / `degrees` default 30°), body-frame→world rotation, and geofence (±3m, 0.3–2.5m) into a simulator-independent module of pure data + pure functions, and emit a machine-readable JSON Schema for future Apple guided generation to consume directly.

**Hands-on (deliverables)**:
- `nanodrone/protocol.py`: (a) the `ACTIONS` constant table + `DEFAULT_DIST=0.5` / `DEFAULT_DEG=30`; (b) `validate(cmd)->(ok, reason)` pure function (rejects unknown actions, negative distance, NaN); (c) move `sim_server.py`'s existing `apply_command(cmd, target, yaw)` over verbatim as `step_target(cmd, target, yaw)->(yaw, mode)`; (d) `schema()->dict` emits the JSON Schema.
- rewrite `bridge/sim_server.py` to import this module (behaviour unchanged); change `send.py`'s `TURNS` set to import protocol.
- `--selftest` prints `PROTOCOL OK: 13 actions, validate rejects 4 bad cmds, schema valid, sim_server behaviour unchanged`. Asserts the legal / illegal decisions are correct and the schema is self-consistent.

**Checkpoint ✅**: `PROTOCOL OK` green, the `sim_server` behaviour regression test passing.

**Going further**: the JSON Schema directly generates the Swift-side contract document for DroneVoice (Phase 2/3).

**Reuse**: directly move over `sim_server.py`'s `apply_command` (including the `c,s=cos/sin yaw` body→world math, the `np.clip` `BOX_XY=3.0`/`BOX_Z=(0.3,2.5)` geofence, the land/emergency mode return); the constants `START`/`DEFAULT_DIST`/`DEFAULT_DEG`/`BOX_XY`/`BOX_Z` moved out of `sim_server.py`. Honestly labelled: there was no independent testable schema module for the protocol before, so this is a genuinely new module.

---

### [Lesson 28] A quantitative arena for the signature counter-example control group: self-trained small model vs generic large model + structured constraints (Track C)

- **Cost** $0 to complete (the A/B backends are pure CPU); the optional local-instruct-model backend C needs an extra download (labelled optional, not required to complete) | **Difficulty** medium | **Prereqs** L27, L12 (the adapter concept), L10 (the KWS fixed vocabulary)

**Why**: DroneVoice Phase 3 is positioned as the signature theme's "counter-example control group." **This lesson turns it into a quantifiable, offline, $0, CI-runnable arena**, letting the data speak rather than just talking. Earlier, L3/L8/L10/L13/L17 all argued "generic isn't good enough → self-train a small model"; this lesson asks the opposite: when the task is "turn flexible natural-language sentences into structured commands," a self-trained fixed-vocabulary KWS (L10) is the wrong tool, while a generic large model + guided generation (forced to emit a legal schema) is the right one. The Apple Foundation Model is just one of this arena's backends; anyone without an iPhone can complete the whole lesson with the Python backend. This also precedes and supports Phase 3.

**Concept**: use a comparison table along four axes — "intent-parsing accuracy + schema-legality rate + coverage + hardware / offline cost." The backend interface is unified to `parse(text)->cmd|None`: backend A = rule-based parsing (bilingual keywords + quantity-word extraction, reusing the L9 `_CMDS` idea; "forward two meters" → `{action:forward,distance:2.0}`), backend B = an L10 KWS-style fixed-vocabulary classifier, backend C = guided-generation (on the Python side, a local small instruct model or stub with constrained decoding demonstrates the concept of "forced to emit legal JSON"; the Apple side corresponds to `@Generable`). Key teaching point: why guided generation can guarantee the schema is always legal (only grammar-allowed tokens are permitted at decoding). This lesson also brings the "rule-based parser" in as backend A, placed in the "vs generic large model" comparison context rather than as a standalone lesson.

**Hands-on (deliverables)**:
- `bridge/parse_text.py`: `parse_text(s)->cmd|None` (bilingual, extracts numbers + units 公尺/米/度/degree) as backend A.
- `bridge/send_text.py`: parse a sentence into JSON and send it through the existing socket (the "voice stand-in" for those without an iPhone, and also the no-iPhone equivalent checkpoint tool for Phase 2).
- `bridge/golden_intents.jsonl`: ~40 mixed Chinese-English golden test sentences (including compound / synonym / quantity-word cases).
- `bridge/eval_parsers.py`: compute the four-axis scores for each backend and print the comparison table.
- `--selftest` uses the two offline backends A and B (C auto-SKIPs when there is no model), printing `EVAL OK: ruleA acc=0.78 schema=1.00 | kwsB acc=0.55 | covered 40 phrases`. Asserts "B's fixed vocabulary has clearly lower acc than A on flexible sentences" and "all outputs pass `protocol.validate`."

**Checkpoint ✅**: `EVAL OK` green (the B<A acc-gap assert passing).

**Going further**: swap backend C for the Apple Foundation Model and you get Phase 3; the comparison table directly serves as the counter-example evidence for the Phase 3 docs.

**Reuse**: L27 `protocol.validate` as the legality judge for all backends; L9 `voice.py`'s `_CMDS` bilingual keyword table and the "longer/turn/land match first" ordering as the base of backend A (plus quantity-word extraction); L10 `kws.py`'s `make_net` + `LABELS/COMMANDS` "fixed-vocabulary classifier" concept as backend B (using text tokens rather than MFCC, following the "fixed classes + argmax + confidence threshold" idea); `bridge/send.py`'s `socket.create_connection` send logic.

---

### [DroneVoice Phase 2] (parallel-elective side-track) iPhone voice entry: App Intents + on-device dictation sending JSON (Track C)

- **Cost** software $0 | **needs hardware / environment**: an iPhone supporting Apple Intelligence (A17 Pro or later) or an iOS 26 simulator + Xcode on a Mac; no drone needs buying (still hits sim); anyone without an iPhone uses L28 `send_text.py` for the equivalent checkpoint | **Prereqs** L27 (protocol), L9 (bilingual keyword parsing)

**Why**: phase 1 already shipped the sim server, but currently you can only use `send.py` to pretend to be the app. The next step in the product story is to actually speak from an iPhone. This lesson corresponds to "the Apple version of L9": microphone → text → minimal keyword parsing → send the existing JSON protocol, letting the user, for the first time, "speak to the iPhone and watch the drone in sim obey." The JSON protocol is a stable contract, and the server doesn't change at all.

**Concept**: on the iOS side, use `SpeechAnalyzer`/`DictationTranscriber` (iOS 26 on-device, best suited to short commands, Chinese and English; older devices fall back to `SFSpeechRecognizer`) for speech-to-text, then use a lookup table (porting L9 `parse_command`'s bilingual-keyword idea and the `background` reject class to prevent false triggers) to map text to one of the 13 actions, serialize it into the bridge's newline JSON, and send over TCP. The action enum and fields use L27 `protocol.schema()` as the single source of truth (rather than hard-copying `sim_server.py`). Define App Intents (`TakeoffIntent`, etc.) so Siri / Shortcuts can also trigger.

**Hands-on (deliverables)**: a `DroneVoice/` iOS project: microphone → text → JSON sent to `sim_server`. The checkpoint uses L27 `protocol.validate` / `protocol.schema()` as the single source of truth: the bytes the app sends must match, field by field, the JSON that `send.py` (or L28 `send_text.py`) produces for the same command. Add `bridge/validate_protocol.py --selftest` to feed the app-recorded command sequence into `protocol.validate`, printing `PROTOCOL OK: 12/12 app commands parsed, schema valid, matched send.py`. Asserts all are legal.

**Checkpoint ✅**: `PROTOCOL OK` green; the app output matches `send.py` field by field. Anyone without an iPhone uses `send_text.py` for the equivalent checkpoint.

**Going further**: foreshadow Phase 3's natural-language-sentence parsing.

**Reuse**: `bridge/sim_server.py`'s `serve()` wire protocol (unchanged) and the L27 `protocol` module; `bridge/send.py` as the protocol control group and regression baseline; L9 `parse_command`'s bilingual keyword table as the app-side vocabulary and fallback; L10's `background` reject-class idea to prevent voice false triggers.

---

### [DroneVoice Phase 3] (parallel-elective side-track) on-device LLM parsing of natural-language sentences: Foundation Models guided generation (the signature theme's counter-example control group) (Track C)

- **Cost** software $0 | **needs hardware / environment**: same as Phase 2; Foundation Models needs iOS 26 and a device that supports Apple Intelligence | **Prereqs** DroneVoice Phase 2, L27, L28

**Why**: Phase 2's keyword parsing can only understand fixed words; what the product really wants is natural-language sentences like "fly forward two meters then turn left ninety degrees." **In the docs, this lesson is explicitly positioned as the course signature theme's "counter-example control group"**: contrasted side by side with L8/L10/L13's "train your own small model" — this time you don't self-train; instead you use Apple's on-device ~3B Foundation Model + guided generation, relying on constrained decoding to guarantee it directly emits schema-correct structured commands. The teaching point is judgment: **when should you train your own small model (data-specific, edge deployment, must fit on GAP8), and when is a generic large model + structured constraints enough (natural-language parsing, an off-the-shelf on-device framework exists)**. If it's not framed as a control group, it would be read as "you actually don't need to train models," diluting the whole course's argument, so the README must spell out this contrast.

**Concept**: use the Foundation Models framework to define `@Generable struct DroneCommand { action: enum(13, aligned with bridge); distance: Double?; degrees: Double? }`, and have `LanguageModelSession` guided-generate a natural-language sentence into an object guaranteed to land within the enum with the correct types, serialized into bridge JSON. The `@Generable` enum and fields are generated from L27 `protocol.schema()` rather than hand-copied. Keep Phase 2's L9 keyword table as a fallback when the LLM is unavailable / parsing fails (echoing the L9/L10 reject-class spirit: if unsure, don't fly recklessly).

**Hands-on (deliverables)**: a DroneVoice app upgrade: natural-language sentence → `@Generable DroneCommand` → JSON. The checkpoint takes the bridge as truth: feed the JSON produced by a set of natural-language test cases (including multi-step, Chinese and English) into the extended `bridge/validate_protocol.py --selftest`, printing `NL-PARSE OK: N/N phrases -> valid commands, all actions in 13-enum, distances within geofence`. Asserts all are schema-legal and land within the geofence. This Phase's quantitative evidence directly cites the L28 `eval_parsers.py` comparison table (backend C = Foundation Model).

**Checkpoint ✅**: `NL-PARSE OK` green. **Note**: CI can only verify JSON schema correctness, not the on-device LLM's behaviour quality — the latter needs manual spot-checking on a real device.

**Going further**: Phase 4 (SwiftUI + bidirectional telemetry + app-side failsafe / dangerous-command confirmation / geofence UI preview), Phase 5 (sim→real, Tello DJITelloPy first, Crazyflie cflib to close).

**Reuse**: Phase 2's app and JSON-sending pipeline; L27 `protocol.schema()`'s 13-action schema as the `@Generable` enum source and validation standard; L9 `parse_command` as the LLM fallback; the `bridge/validate_protocol.py` checkpoint (built in Phase 2); the L28 `eval_parsers.py` comparison table as counter-example evidence.

---

### [DroneVoice Phase 4] (parallel-elective side-track) SwiftUI app: connection settings, command log, emergency stop, bidirectional telemetry, app-side failsafe (Track C)

- **Cost** software $0 (the no-iPhone route verifies the server-side telemetry / e-stop / confirmation protocol) | **needs hardware / environment**: iPhone + Mac + Xcode (the iPhone route) | **Difficulty** advanced | **Prereqs** L27 (protocol), Phase 3, L23 (telemetry format), L4/L24 (failsafe concept and `nanodrone/safety.py`)

**Why**: package the voice entry into an app that's actually usable: the person needs to see where the drone is (telemetry), needs a one-touch e-stop, needs to be stopped for confirmation before a dangerous command, and needs to see the geofence. This lesson moves the three-part failsafe philosophy from L4's real-hardware bring-up (battery threshold, geofence, exception means land) and the L24-extracted `nanodrone/safety.py` up to the app UI layer, and makes sim_server return telemetry. Anyone without an iPhone verifies "the server-side new telemetry + dangerous-command confirmation protocol," which can be poked with `send.py`. Teaching point: **the UI is not decoration, it is part of the failsafe.**

**Concept**: the human-machine safety interface: (a) a bidirectional protocol — the server returns one line of telemetry JSON after each command (x/y/z/yaw / whether the geofence edge was hit), the format following L23 `nanodrone/telemetry.py`; (b) app-side failsafe — the `emergency_stop` button sends `{action:emergency_stop}` directly, and dangerous commands like land/down pop a confirmation first; (c) geofence visualization. The server returns a rejection response for unsafe sequences like "forward without takeoff" (using L27 `protocol.validate` as the judge).

**Hands-on (deliverables)**:
- extend `bridge/sim_server.py`: after handling each command, return telemetry JSON (following `env._getDroneStateVector(0)`, and wiring up the L23 `FlightLogger` format), adding a rejection response for unsafe sequences.
- add a SwiftUI app: a connection-settings page / command log (wiring up the L23 jsonl concept) / a red EMERGENCY STOP button / telemetry readout / geofence box.
- `--selftest` (in sim_server), once extended, prints `BRIDGE OK: telemetry sent N frames, refused 1 unsafe cmd, emergency froze drone`. Asserts the position no longer changes after e-stop, the telemetry frame count > 0, and the unsafe command is rejected.

**Checkpoint ✅**: `BRIDGE OK` (including the three asserts: telemetry frame count, rejection, e-stop freeze) green. Anyone without an iPhone uses this as the equivalent checkpoint.

**Going further**: wire the app-side pre-flight confirmation page into L26 `preflight_check.py`; wire the telemetry readout into L23 replay for a "post-flight review."

**Reuse**: `sim_server.py`'s `env._getDroneStateVector(0)[0:3]` for state as the telemetry source, and the gentle-land logic; L4 `fly_crazyflie.py`'s three-part failsafe idea (battery gate → dangerous-command confirmation, geofence → already in L27, exception → emergency) mapped to the app; L24 `nanodrone/safety.py`'s `decide_failsafe` as the server-side safety judge; L27 `protocol.validate` as the judge that rejects unsafe commands; L23 `telemetry.py`'s JSON format as the telemetry wire format.

---

### [DroneVoice Phase 5a] (parallel-elective side-track) Tello over Wi-Fi: AI off-board, not offline (Track C)

> Phase 5 runs in two legs: **5a Tello (first, lowest risk) → 5b Crazyflie (closing, back to the course's end point)**. The protocol (L27), voice (Phase 2/3), and app (Phase 4) don't change by a single word; only the controller backend swaps.

- **Cost** **hardware: a DJI Tello, ~US$100** + a computer that can connect to the Tello Wi-Fi (no Apple Intelligence/A17 requirement); $0 without hardware (the FakeTello selftest runs throughout) | **Difficulty** advanced | **Prereqs** L27, Phase 4, **L24 (directly reuse `TelloBackend`)** | new package `djitellopy`

**Why**: the first leg of phase 5. The Tello is the cheapest, Wi-Fi, with a mature DJITelloPy, making it the lowest-risk real-hardware demonstration of "the same JSON protocol, only the controller backend swaps." Key teaching point: none of your earlier lessons (L27 protocol, Phase 2 voice, Phase 4 app) change by a single word; you just swap the sim_server's "PyBullet backend" for a "Tello backend." **Honestly labelled**: the Tello's AI is off-board, not offline, and is not the final goal — it is proof of "protocol portability" and a safe first step onto real hardware.

**Concept**: a backend swap: map L27 `step_target`'s semantics to DJITelloPy's `takeoff`/`move_forward`/`rotate_clockwise`/`land`; the body-frame and geofence rules follow L27; the Tello-specific failsafe (battery-% threshold, refuse to fly when low, auto-land on connection loss) goes through L24 `nanodrone/safety.py`. **The division of labour between this Phase and L24**: L24 already built `TelloBackend` and safety; Phase 5a connects it to the port-9000 TCP server, letting the Apple app (Phase 4) drive a real Tello directly — that is, "app → real hardware" end-to-end.

**Hands-on (deliverables)**:
- `hardware/tello_server.py`: listen on the same port 9000, receive the same newline-JSON, and fly the real drone with the L24 `TelloBackend` + `djitellopy`; `distance(m)→cm`, `degrees→rotate`.
- `--selftest` (uses a FakeTello stub when there's no Tello) prints `TELLO-SERVER OK: served N protocol cmds -> [takeoff, forward 100cm, cw 90, up 50cm, land], battery-gate enforced, app-equivalent`. Asserts each protocol command maps to a legal Tello call, doesn't actually take off when unconnected, and matches the bytes the Phase 4 app sends.

**Checkpoint ✅**: `TELLO-SERVER OK` green; the end-to-end (app→tello_server→FakeTello) consistency assert passing.

**Going further**: swap the controller and you get Phase 5b Crazyflie.

**Reuse**: the whole `serve()` socket/newline parsing loop from `bridge/sim_server.py` (the protocol-receiving layer doesn't move at all); L24 `TelloBackend` and `nanodrone/safety.py`; L27 `protocol.validate` + `ACTIONS` + body-frame math to decide what to send the Tello; the FakeTello stub follows the `SelftestInput` template.

---

### [DroneVoice Phase 5b] (parallel-elective side-track) Crazyflie offline self-flight: back to the course's end point (Track C)

- **Cost** **hardware: a Crazyflie 2.x + Crazyradio (+ optional AI-deck) ≈ within the course's existing ~US$545 bundle**; needs a clear indoor flight area; $0 without hardware (the FakeCrazyflie selftest) | **Difficulty** advanced (the hardest in the whole line) | **Prereqs** L27, Phase 4, L4 (cflib/MotionCommander/three-part failsafe), L22 (the on-board reflex narrative, optional) | new package `cflib`

**Why**: the close of phase 5, and the end-point echo of the whole nanodrone-ai: an offline, on-board, <512KB int8 real Crazyflie. It connects the DroneVoice product line back to the course main line (L3 self-trained CNN → L4 GAP8 quantization → L17–L22 on-board deepening) — voice / app is the "high-level command entry," but the true offline autonomy (avoidance) is still a small model running on the drone. The Crazyflie goes through cflib, and the protocol is likewise unchanged. **Honestly labelled**: this is the highest difficulty in the whole line, needing the most complete hardware and flight area.

**Concept**: the final form of the two-layer architecture: the app / voice sends a high-level setpoint (the L27 protocol) → the host-side cflib feeds the setpoint to the Crazyflie's on-board PID (motor mixing); meanwhile the on-board GAP8 runs the quantized avoidance CNN (L4 quantization / L22 unified policy) as an offline reflex. Teaching point: how the two control paths (the human's high-level intent vs the on-board real-time reflex) coexist safely and their priority (the reflex always takes priority over high-level intent, echoing the L13 event-priority table).

**Hands-on (deliverables)**:
- `hardware/crazyflie_server.py`: the same port 9000, the same JSON, flying the real drone with cflib `SyncCrazyflie` + `MotionCommander`, the safety following L4 + `nanodrone/safety.py`.
- `--selftest` (uses a FakeCrazyflie stub without hardware) prints `CF-SERVER OK: mapped protocol cmds -> motion_commander calls, battery-gate + commander-always-lands enforced`. Asserts the exception path always triggers land, and it doesn't take off when unconnected.
- a README paragraph explaining how to run alongside the L4 GAP8 on-board avoidance model (or the L22 unified policy): high-level setpoint vs on-board reflex priority.

**Checkpoint ✅**: `CF-SERVER OK` green; the exception-always-lands, no-takeoff-when-unconnected asserts passing.

**Going further**: flash the L22 unified int8 policy into the AI-deck as the on-board reflex, achieving the final demo of "app high-level intent + on-board offline autonomy" — the whole course converges here.

**Reuse**: the whole L4 `fly_crazyflie.py`'s cflib connection / `read_battery`/MotionCommander "enter and take off, exit / exception always land" three-part failsafe as the controller base; the `sim_server.py` `serve()` receiving layer; the L27 protocol mapping JSON to `MotionCommander.forward/turn/up/land`; the <512KB ONNX produced by L4 `quantize_cnn.py` (or L22) as the "on-board reflex" narrative (no re-quantizing, just wiring it back); `nanodrone/safety.py`; the FakeCrazyflie stub follows `SelftestInput`.

---

### [Lesson 29] Nano world model: latent-space prediction for proactive avoidance (V-JEPA, distilled on-board) (Track B predictive frontier)

- **Cost** $0 (pure sim, self-produced sequences) | **Difficulty** advanced | **Prereqs** L17 (`TinyDronet`/`TinyDepthNet` conv encoder), L18 (two-frame temporal idea), L19 (avoidance to make proactive), L21 (distillation), L4 (int8 footprint arithmetic)

*Note — this section is the pre-implementation blueprint, kept for the design rationale. The shipped lesson grew well past it: four nets (a bearing-aware encoder, a multi-horizon predictor, dual warn/crit collision heads, a danger-now head), four horizons k∈{4,8,16,32}, eight scripts, and closed-loop / learned-policy scoreboards. The lesson README is the source of truth.*

**Why**: every model so far is *reactive* — L17 depth and L19 RL both answer "what about the obstacle that is close *now*." At speed that is too late: a 27 g drone with bounded acceleration cannot swerve once a pillar fills the frame. A **world model** adds *anticipation*: it learns how the scene will change and lets the drone act on what is *about to* happen — the frontier Track D only signposted. The naive build predicts the next *image* (diffusion / pixel generation): slow, and it hallucinates detail a controller cannot use. This lesson takes the **V-JEPA** route — predict the next *latent embedding*, never pixels — and the signature theme returns at the frontier: the real V-JEPA is an Orin-class billion-parameter model that will never fit GAP8, so you train and distil your own *nano* one under 512KB.

**Concept**: three tiny nets, all reusing the course's conv stack, all int8-able: an **Encoder** `f_θ` (image→64-d latent, L3 `TinyDronet.features`), an action-conditioned **Predictor** `g_φ` (`(z_t,a_t)→ẑ_{t+k}`, a small MLP predicting the *residual* so "nothing changes" is the free baseline), and a linear **collision head** (`ẑ→P(too close within k steps)` — the anticipation signal). Latent prediction works without a pixel loss (and without collapse) via an **EMA target encoder** with stop-gradient (V-JEPA/BYOL) plus a VICReg-style variance guard; the loss is `‖g_φ(f_θ(x_t),a_t) − sg(f_EMA(x_{t+k}))‖² + var-guard + BCE(collision)`. **V-JEPA vs 4D-GS (honest contrast)**: 4D-GS is the explicit-geometry world model — the heavyweight 3D+time cousin of L14a's 2D occupancy grid; metric-precise and photorealistic, but its latency scales with the number of Gaussians → Orin-class, and it produces geometric "floaters" when extrapolating (the geometry analogue of pixel hallucination). V-JEPA trades metric grounding for a fixed, distillable, hallucination-free latent forecast — which is why it is the on-board backbone here, with 4D-GS kept as *offline* supervision in the going-further.

**Hands-on (deliverables)**:
- `lessons/29_world_model/gen_wm_dataset.py`: really fly forward through randomized multi-pillar layouts, streaming the camera each control step, and slice into (x_t, a_t=velocity, x_{t+k}) triples + a *free* future-collision flag (planar distance < DANGER_R within k steps). `--selftest` prints `WM-DATA OK: N seqs, horizon k=8 steps, collide-rate=0.XX, ...`; asserts both classes are present.
- `lessons/29_world_model/train_world_model.py`: the nano V-JEPA (`Encoder` + EMA `target` + `Predictor` + `CollisionHead`), latent loss, footprint via the L4 `n_params/1024` formula. `--selftest` prints `WORLD-MODEL OK: latent MSE=0.XX (no-op baseline Y.YY), collision AUC=0.XX, int8 footprint=ZZ KB (<512 fits)`; asserts the predictor beats the "future==present" no-op baseline, AUC>0.70, and footprint<512.
- `lessons/29_world_model/proactive_avoid.py`: fly the same course reactive (veer when a pillar is close *now*) vs proactive (veer when the *predicted* k-step distance is close), under bounded acceleration so reacting late genuinely costs clearance; save a top-down PNG. `--selftest` prints `PROACTIVE OK: reactive min-clear=A m (avoid@R), proactive min-clear=B m (avoid@P), lead=+X steps (~Wms earlier), crashes r/p = 0/0`; asserts proactive triggers earlier and keeps ≥ the clearance without crashing.

**Checkpoint ✅**: `WM-DATA OK` + `WORLD-MODEL OK` + `PROACTIVE OK` green (locally, since the trainer loads torch — like L3/L8/L13); the two torch-free scripts (`gen_wm_dataset`, `proactive_avoid`) also run in CI.

**Going further**: (1) **geometry-grounded latent prediction** — use 4D-GS *offline* (sim / Orin) to produce metric occupancy and add a grounding loss so `ẑ_{t+k}` decodes to a collision-checkable distance, buying V-JEPA's latency with 4D-GS's grounding (an ICRA/CVPR-flavoured contribution). Items (2) and (3) of the original plan have since **shipped as the lesson itself**: the closed-loop MPC flies from the trained collision heads with no privileged look-ahead (step 4, `wm_closed_loop.py`), and a PPO policy learned over the world model's outputs replaced the hand-written cost (step 6, `learn_policy.py`) — the open edges that remain (the LSTM's speed-extreme gap, longer memory) live in the lesson's own going-further. Honest gap: full V-JEPA 2 / 4D-GS are Orin-class — this teaches the principle under the GAP8 budget.

**Reuse**: L3 `train_cnn.py`'s `TinyDronet.features` as the encoder backbone (imported, the L4 pattern); the L3/L17 `gen_dataset` `CtrlAviary+DSLPIDControl` sampling loop and `env._getDroneImages` capture; L14a/L19's multi-pillar scene idea; L4 `quantize_cnn.py`'s `n_params/1024` int8 footprint check; `train_rl.py`'s `_save_trajectory_plot` top-down plot. Honestly labelled **new to the course**: the EMA target encoder, the latent (no-pixel) JEPA loss, the action-conditioned residual predictor, the variance anti-collapse guard, the future-collision head, and the proactive (anticipatory) avoidance metric — the course has done supervised / RL / distillation before, but never self-supervised latent prediction.

---

## 5. Master table

> **Required / elective markers**: ★ = core required main line; ◆ = advanced branch (core for anyone who "really wants to get on-board / land," elective for those who only want to finish the sim main line); ○ = parallel elective (needs specific hardware / platform).

| No. | Title | Track | Category | Cost | Difficulty | Depends on |
|---|---|---|---|---|---|---|
| L11 | Mission orchestration skeleton: flight loop → state machine + Failsafe | A Orchestration | ★ | $0 | medium | L5, bridge phase 1 |
| L12 | Voice-driven state transitions (source→event adapter) | A Orchestration | ★ | $0 | medium | L11, L9, L10 |
| L13 | Multimodal mini-capstone: find person → follow → land (with re-training a confirmation classifier) | A Orchestration | ★ | $0 | advanced | L11, L12, L8 |
| L14a | Simple mapping & autonomous patrol (`nanodrone.map`) | B On-device / perception | ★ | $0 | advanced | L11, L2 |
| L14b | Perception scheduling & quantization under the on-board budget (sew back onto GAP8) | B On-device / perception | ★ | $0 (real-hardware optional ~US$545) | advanced | L14a, L4, L13 |
| L16 | Graduation project & rubric (host-side capstone) | A Orchestration | ★ | $0 (real-hardware optional) | advanced | L11, L12, L13, L14a, L14b |
| L17 | Monocular depth-estimation CNN (training a dense model for the first time) | B On-device / perception | ◆ | $0 | medium | L2, L3, L4 |
| L18 | Optical flow / visual odometry: self-estimate state without GPS | B On-device / perception | ◆ | $0 (real-hardware optional Flow deck ~US$45) | medium | L1, L3, L8, L4 |
| L19 | Multi-obstacle RL course (fed by perception, generalizes) | B On-device / perception | ◆ | $0 | advanced | L3, L17 |
| L20 | Domain randomization: shrink the sim-to-real gap | B On-device / perception | ◆ | $0 | medium | L17, L2 |
| L21 | Knowledge distillation + model compression (extending L4 quantization) | B On-device / perception | ◆ | $0 (hardware reuses L4, no double billing) | advanced | L4, L17, L20, L3 |
| L22 | Distill multiple capabilities into a single on-board policy (on-board capstone) | B On-device / perception | ◆ | $0 | advanced | L8, L19, L21, L4 |
| L23 | Flight black box: telemetry logging and offline replay | E Real-hardware landing | ◆ | $0 | beginner | L1, bridge phase 1 |
| L24 | Cheap Tello real-hardware stepping stone (extract `nanodrone/safety.py`) | E Real-hardware landing | ◆ | needs Tello ~US$100 (FakeTello CI $0) | advanced | L23, L11, bridge phase 1 |
| L25 | Sim-to-real gap measurement | E Real-hardware landing | ◆ | $0 (shooting real hardware needs L24 Tello) | advanced | L8/L3, L18, L24 |
| L26 | Field-test SOP + Taiwan regulations | E Real-hardware landing | ◆ | $0 (real-hardware optional) | medium | L23, L11/L24, L24 |
| L27 | Protocol extraction `nanodrone.protocol` (pay down the protocol debt) | C Apple | ◆ | $0 | beginner | bridge phase 1 |
| L28 | Parser-evaluation arena (the quantitative foundation for the counter-example control group) | C Apple | ◆ | $0 (backend C optional) | medium | L27, L12, L10 |
| DroneVoice Phase 2 | iPhone voice entry (App Intents + dictation→JSON) | C Apple | ○ | software $0 (needs iPhone/Xcode) | medium | L27, L9 |
| DroneVoice Phase 3 | on-device LLM parsing (counter-example control group) | C Apple | ○ | software $0 (needs iOS 26 + Apple Intelligence) | advanced | Phase 2, L27, L28 |
| DroneVoice Phase 4 | SwiftUI app + bidirectional telemetry + app failsafe | C Apple | ○ | software $0 (needs iPhone/Xcode) | advanced | L27, Phase 3, L23, L4/L24 |
| DroneVoice Phase 5a | Tello over Wi-Fi (AI off-board, protocol unchanged, swap controller) | C Apple | ○ | hardware ~US$100 (FakeTello CI $0) | advanced | L27, Phase 4, L24 |
| DroneVoice Phase 5b | Crazyflie offline self-flight (back to the course's end point) | C Apple | ○ | hardware ≈ L4 ~US$545 (FakeCrazyflie CI $0) | advanced | L27, Phase 4, L4, L22 |
| L29 | Nano world model: latent-space prediction for proactive avoidance (V-JEPA, distilled on-board) | B On-device / perception | ◆ | $0 | advanced | L17, L18, L19, L21, L4 |

### Numbering rationale

- The L11–L16 backbone keeps its original ordering and dependency graph; **L15 is deliberately left blank** (swarm has been demoted to a Track D docs-only going-further, does not occupy a lesson number, and the number is not reused so as not to be confused with the "cut swarm"). L14 is split into L14a (mapping) / L14b (on-board convergence) to accommodate the added on-board gap. L16 keeps the graduation project's "last lesson" symbolic number.
- The three deepening lines — perception depth, real-hardware landing, and the Apple product line — all use a **continuous new number range starting at L17**, not inserting numbers into L11–L16 (avoiding disturbing the already-stable dependency graph).
- Phase 4/5 keep the "Phase" naming (consistent with phase 1–3, marking them as a bridge side-track rather than a main-line Lesson).
- **L29** takes the next free lesson number as Track B's *predictive frontier*: new capabilities always take the next number rather than being inserted into the stable L11–L28 graph, so L29 is filed under Track B even though it is numbered after Track C's L27–L28. The generated DroneVoice docs page is renumbered `31-dronevoice.md` so the numbered lessons (L29's world model and L30's course summary) sort before it.

## 6. Design trade-offs: which ideas got merged, and why swarm was cut

1. **Failsafe doesn't get its own lesson; it's extracted into `nanodrone/safety.py`**. L11 already builds in the `Failsafe` state (first Hover, then Land on timeout), runs it through the whole course, and the L16 rubric lists it as a hard gate. The approach is to, **at L24 (the first time you touch real hardware, the first time failsafe truly matters for safety), extract L11's Failsafe into the unit-testable, fault-injectable `nanodrone/safety.py`**, shared by L26, Phase 4, and Phase 5 — satisfying both the demand that "failsafe must be verifiable by fault injection in sim" and not duplicating a state-machine lesson alongside L11.

2. **The rule-based parser doesn't get its own lesson; it's folded into the L28 evaluation arena as backend A**. L12 already builds the source→event adapter (keyboard / voice / KWS → events). Placing the "rule-based parser" into **L28's "vs generic large model" comparison context** has more teaching tension than a standalone lesson; the no-iPhone equivalent checkpoint tool `send_text.py` ships in the L28 deliverables.

3. **The two optical-flow proposals are merged into a single L18**. Classical optical flow (cv2, teaching the principles + real hardware needs a Flow deck) and "train a small CNN to regress velocity" are merged into one: with "train your own small CNN (privileged labels)" as the main line (matching the signature theme), while including the classical-optical-flow principles for contrast and the honest labelling of "real hardware needs a Flow deck v2 ~US$45, will drift." No two optical-flow lessons.

4. **Multi-obstacle RL (L19) doesn't rebuild the scene**. L14a already brings its own multi-pillar scene builder for mapping & patrol (and honestly labels it as new, not reusing L3). L19 **directly reuses L14a's multi-pillar `scene.py`**, only adding the layer of "fold perception (L17 depth) into the RL observation + curriculum" — the real gap that L14a didn't do, and that the `avoid_aviary` comment explicitly names.

5. **The three capstones have clear, non-overlapping division of labour**: **L16** is the host-side graduation project of "orchestrate with mission building blocks"; **L22** is the on-board technical capstone of "compress multiple capabilities into a single int8 network"; **Phase 5b** is the product-line close of "app high-level intent + on-board offline reflex." Each is the end point of its own main line, extensions of one another rather than duplicates.

6. **Cut swarm (the original L15 proposal)**. A two-drone swarm has the weakest connection to the ultimate "single-drone on-board autonomy," the largest refactoring surface, the highest maintenance cost, and zero contribution to the signature theme, so it is **demoted to a docs-only going-further (Track D), not a lesson, occupying no number**. If it were to come back and crack open the L11 foundation or drag down the graduation pace, the price isn't worth it. To preserve extension flexibility, the L11 `mission runner` still **does not hard-code `num_drones`**, but no lesson is opened for it.

7. **Correct the inflated reuse**. The mapping & patrol (L14a) occupancy grid and multi-obstacle scene builder are honestly labelled as **new capability** (L3 has only one pillar and is bound to the RL-specific `AvoidAviary`, not reusable), and extracted into `nanodrone.map` for later sharing. Everything in the new depth / optical-flow / DR lessons — the "upsampling head, scale-invariant loss, whole-image computation, noise / randomization" — is labelled one by one as the first time sim uses it, with no pretend reuse.

8. **The world model is a *nano latent* predictor (V-JEPA), not pixel generation and not full 4D-GS**. A world model tempts two dead ends on a 27 g drone: predicting pixels (diffusion — slow, and it hallucinates detail the controller cannot act on) and explicit 4D geometry (4D-GS — metric but Orin-class, its latency scaling with the scene). L29 takes neither: it predicts the next *latent* with an EMA-target joint-embedding loss (no pixels), a fixed compute cost that distils under 512KB int8. 4D-GS is kept as the honest contrast (the heavyweight cousin of L14a's occupancy grid) and, in the going-further, as an *offline* geometric-grounding teacher — never the on-board engine. The signature theme reappears at the frontier: the Orin-class world model won't deploy, so you train your own nano one.

## 7. Risk notes

**Technologies with a risk of changing after Jan 2026 (all concentrated in Track C Apple)**:

- **Apple Foundation Models framework** (Phase 3): needs iOS 26 + Apple Intelligence + A17 Pro/M series. The API is still evolving, and `@Generable`'s parsing stability for "a large enum + multilingual natural-language sentences" needs real-device testing; the GA status, the hardware-requirement list, and the breadth of Traditional-Chinese on-device model support may all update with new device models / new OS. **Before starting, be sure to re-verify against the Apple Developer docs.**
- **SpeechAnalyzer / DictationTranscriber** (Phase 2): new iOS 26 APIs; the offline-download status of the Traditional-Chinese on-device model needs verifying; the dual path of falling back to `SFSpeechRecognizer` on older devices needs testing.
- **iOS 27 / 2026 WWDC** may again adjust these API names or add streaming/tool-use capabilities.
- **Risk isolation**: once L27 extracts the protocol into a single source of truth, the Apple API risk is further isolated to the "swap the language and re-run the same schema / golden test data" layer — L28's Python backend and `send_text.py` let anyone without an iPhone complete the course 100%-equivalently, and any Apple-side API change does not affect "whether the course can be completed."

**Hardware cost (all honestly labelled, all CI runnable at $0)**:

- The sim parts of the core main-line Track A and Track B (including L17–L22) are **$0 throughout, pure sim, with CI needing no hardware** (including a microphone — L12/L13 and all real-hardware lessons inject via scripted events / FakeXxx stubs).
- **L24 / Phase 5a: a DJI Tello, ~US$100** (DJITelloPy/Wi-Fi, AI off-board, not offline — the fastest path to a real-hardware demo, but **stated plainly to not be the course's end point**). The FakeTello stub keeps CI $0.
- **L18 real-hardware optical flow: a Crazyflie Flow deck v2, ~US$45** (not required for this lesson, pure sim to learn the principles).
- **L14b / L21: reuse L4's already-labelled ~US$545 AI bundle, no double billing.**
- **Phase 5b: a Crazyflie ≈ within the L4 ~US$545 bundle** (the highest hardware + flight-area bar in the whole line). The FakeCrazyflie stub keeps CI $0.
- L25 shooting your own real-hardware gap needs the L24 Tello; without a Tello, you can still complete the course with the bundled sample video.
- Track C additionally needs an iPhone supporting Apple Intelligence (A17 Pro or later) or an iOS 26 simulator + Mac/Xcode.

**Maintenance cost**:

- Track C has the highest overall maintenance cost — it depends on Apple platform versions, and CI can't truly verify on-device LLM behaviour (only the JSON schema). **It is therefore marked as a parallel elective, fully decoupled from the main line**: the JSON protocol is a stable contract, and Track A/B are unaffected by Apple API changes. The L27 protocol extraction + the L28 evaluation arena push the risk down another layer.
- **Once L11 `nanodrone/mission.py` and L27 `nanodrone/protocol.py` become the foundation, any API change could silently break downstream** (mission affects L12–L16/L23; protocol affects L24/Phase 2–5). **A cross-lesson integration CI must be built in `.github`** (not just each lesson's own `--selftest`), covering the four shared modules `mission`/`protocol`/`safety`/`telemetry`, to catch regressions in real time when the API changes.
- Track B's new lessons all self-produce data in sim and converge under `--selftest`, so the maintenance cost is low; only L19 RL and L21/L22 distillation have longer training times, so CI uses a few-step smoke test (not running the full training in CI).
- **L29 (world model)** is the only lesson doing self-supervised latent prediction, whose failure mode is *representation collapse*; it is guarded by the EMA target + a VICReg-style variance term, and its `--selftest` gates on "beats the no-op baseline" *and* on the veer-ranking check (can it rank which evasion is truly safer — the planner's question), so a collapsed or side-blind encoder fails. Like L3/L8/L13 its trainer loads torch and is verified locally; the torch-free smoke job runs its data-gen (`gen_wm_dataset`) and the torch-free `proactive_avoid`. It is a *principle* demo, not production V-JEPA.

**The most critical strategic trade-off**: pulling the course back from "smarter desktop-simulation orchestration" to the "on-board / offline / real-hardware autonomy" signature, accomplished by these main lines: (1) **L14b** sews the orchestration capabilities back onto GAP8/int8/<512KB; (2) **L13** forces re-training a confirmation classifier, making "train your own model" re-appear before the capstone; (3) **L11's built-in Failsafe**, **L16 listing on-board considerations and failsafe as a hard rubric gate**, and explicitly accounting for the theme's turning-point arc and the Phase 3 counter-example in the docs; (4) **Track B's L17→L18→L20→L21→L22** walks the whole line of "the simulator's idle capabilities → self-trained dense / optical-flow small models → sim-to-real robustness → compress into 512KB → unify multiple capabilities on-board," upgrading the "train your own small model" theme from "shown once more" to "running all the way through"; (5) **adding Track E (L23–L26)** makes "sim-first infrastructure → cheap real-hardware stepping stone → measure the gap → fly legally and safely" concrete, directly answering the "be honest about sim-to-real" principle. **The cut swarm stays demoted**, its number not reused, and it does not come back to crack open the foundation.

---

Related existing code paths: `bridge/sim_server.py`, `bridge/send.py`, `nanodrone/{detect,input,view}.py`, `lessons/0[1-9]_*` and `lessons/10_*`. Track A's new modules land in `nanodrone/{mission,mission_events,map}.py`. The remaining new modules are recommended to land in `nanodrone/{protocol,telemetry,safety,degrade}.py`, `lessons/{17_depth,18_flow,19_multi_avoid,20_domain_rand,21_distill,22_unified,23_telemetry,24_tello,25_sim2real,26_field_test}/`, `bridge/{parse_text,send_text,eval_parsers,golden_intents.jsonl}`, `hardware/{tello_server,crazyflie_server}.py`, and `apple/DroneVoice/`.

---

## Appendix A — Track A build spec (aligned with the shipped `nanodrone.mission`)

> L11 is **already implemented and passing its checkpoint** (`lessons/11_mission/mission_demo.py --selftest` prints
> `MISSION OK …` and `FAILSAFE OK …`, already wired into CI). This appendix takes the outlines of Track A's
> follow-on lessons **down to the depth of "building against a real API,"** with all signatures based on the version
> actually landed in `nanodrone/mission.py` (where this differs from the outline descriptions above, this prevails).

### A.0 The shipped `nanodrone.mission` API (the foundation for L12–L16)

```python
from nanodrone.mission import (
    State, Mission, Takeoff, Hover, GoTo, Land, Failsafe,
    in_fence, clip_to_fence,            # geofence pure functions
    FENCE_XY, FENCE_Z, HOVER_HEIGHT, LAND_HEIGHT,   # constants
)
```

- **`State`** (subclass to extend): `on_enter(m)` is called once on entry (usually sets `m.target`);
  `step(m) -> (target_pos, yaw)` returns the desired high-level setpoint each frame; `is_done(m) -> bool` decides when to move to the next phase.
  The state reads live state from `m`, and **never touches the motors**.
- **`Mission(states, *, start=(0,0,0.1), gui=False, fence_xy=FENCE_XY, fence_z=FENCE_Z, failsafe=None)`**:
  - `.run(max_seconds=20.0) -> dict`, with dict fields: `history` (list of the names of the states entered), `steps`,
    `moved` (horizontal displacement from start to end), `final_z`, `in_failsafe`, `failsafe_reason`, `landed`.
  - `.request_failsafe(reason: str)`: drop into Failsafe at any time (lost-link / breach / perception timeout).
  - the loop automatically runs a geofence watchdog each frame: any state trying to leave the safety box → auto `request_failsafe("geofence")`.
  - live attributes for states to read: `m.pos` (np3), `m.yaw_now`, `m.target`, `m.yaw`, `m.dt`. The runner indexes `obs[0]` but does not hard-code `num_drones` into the loop body.
- Built-in states: `Takeoff(height=1.0)`, `Hover(seconds=1.0)`, `GoTo(xyz, face=False, tol=0.12, safe=True)`,
  `Land()`, `Failsafe(hover_seconds=0.5)`. `GoTo(..., safe=False)` can deliberately request an out-of-bounds point to demonstrate the watchdog.

> **Small foundation extension for L12–L16 (recommended to add in one pass)**: add a public method
> `Mission.go(state)` (immediately enter any State, for event-driven jumps, internally `_enter`),
> and have `run()` accept an optional `event_source` (each frame `poll() -> event|None`).
> These two let L12's "event→transition" and L13's "perception loss→recapture" no longer copy the loop.

### A.1 [Lesson 12] Voice-driven state transitions — build spec

- **New file `nanodrone/mission_events.py`**: a source→event adapter layer (the three sources have different output types and must be adapted):

  | Source | Raw output | Adapter | Mission event |
  |---|---|---|---|
  | L9 `voice.parse_command` | `(fwd,strafe,up,yaw)` / `'land'` / `None` | `'land'`→land; all-zero/None→(emit nothing) | `takeoff`/`land`/`stop`… |
  | L10 `kws_fly.KwsListener.poll()` | `(label, conf)` | only trust if `conf>0.6`; `background`→emit nothing | discrete label→event |
  | bridge `protocol.step_target` (after L27) | mode | `'land'`→land, `'emergency'`→stop | `land`/`stop` |

  Plus an `EVENT_TO_STATE = {"takeoff": Takeoff, "hover": Hover, "land": Land, ...}` table
  (reusing L9 `_CMDS`' "longest-match first" and L10's `background` reject idea).
- **New file `lessons/12_voice_mission/voice_mission.py`**: use `Mission` + `event_source`, and when an event arrives `m.go(EVENT_TO_STATE[ev]())`; `emergency`/`land` take the highest priority. The voice thread uses `KwsListener.poll()` non-blocking.
- **`--selftest`** (no microphone, injects a timestamped event sequence, reusing L9's `ScriptedVoice` approach) prints:
  `VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed, 1 noise-event rejected`.
  Asserts: the transition count is correct, the final state is Land, `landed`, and the injected `background`/low-conf noise events do **not** trigger a transition.
- **Reuse**: L11 `Mission`/`Takeoff`/`Hover`/`Land`/`go()`; L9 `parse_command`/`ScriptedVoice`; L10 `KwsListener.poll()` + the `conf>0.6` threshold + the `background` reject class.

### A.2 [Lesson 13] Multimodal mini-capstone (find person → follow → land) — build spec

- **New file `lessons/13_find_follow_land/train_confirm.py`**: sim-self-produce "target person vs background" data + train a tiny CNN confirmer (reusing the L8 `gen_person_dataset`/`train_person_cnn` pattern). `--selftest` prints `CONFIRM-CNN OK: trained N samples, val acc>0.9`.
- **Two new `State` subclasses** (in the lesson or in `nanodrone/mission.py`):
  - `Search(State)`: `step` slowly increments `m.yaw`, holds altitude; runs L8 `cnn_bearing` every `PERCEPTION_EVERY` frames;
    `is_done` = detection hit **and** distance `<MAX_RANGE` **and** the confirmation CNN decides=person. On timeout `T_search`, `m.request_failsafe("search_timeout")`.
  - `Follow(State)`: `step` uses L8 `world_point`/`depth_at_bearing` to compute `target` and `m.yaw` (converging to `DESIRED_DIST`);
    lose target for `N=8` consecutive frames → `m.go(Search())` to recapture.
- **Event priority (hard rule)**: `land`(voice/emergency) > `Failsafe`(lost-link/breach) > visual transitions (Search↔Follow) > continuous control.
- **New file `lessons/13_find_follow_land/mission.py`**: `Takeoff → Search → Follow`, with the voice `land` event interrupting at the highest priority.
  `--headless` uses L8 `scripted_person_xy` to walk a circle + injects a land event at ~12 s. `--selftest` prints
  `CAPSTONE-MINI OK: Search→Follow in Ns (confirm-cnn gated), tracked K frames mean bearing err X deg, land→landed z=0.40`.
  Asserts: (a) completed Search→Follow through the confirmation gate (b) mean `true_bearing_deg` error < 18° during Follow (c) `landed` after land (d) the injected fake background target is blocked by the confirmation gate without erroneously transitioning to Follow.
- **Reuse**: L11 runner + `Takeoff`/`Land`/`Failsafe`/`go()`; L8 `follow_real.cnn_bearing`/`depth_at_bearing`/`world_point`/`true_bearing_deg`/`scripted_person_xy` + PersonCNN; L12's events and priority.

### A.3 L14a / L14b / L16 — build essentials (against the A.0 API)

- **L14a mapping & patrol**: new `nanodrone/map.py` (occupancy grid + depth-column→world projection) + a self-contained multi-pillar `scene.py` (**not reusing L3**). The patrol = `Mission([Takeoff, GoTo(corner1), …, GoTo(corner4), Land])`, scanning and updating the map at each waypoint. `PATROL OK: visited 4/4 waypoints, mapped C cells`.
- **L14b on-board convergence**: reuse L4 `quantize_cnn` to convert the L13 confirmation CNN to int8, measure footprint (<512KB) / accuracy drop; inject `INFER_LATENCY_MS` to run the L13 mission and measure "latency↑ → bearing err↑". `QUANT OK …` + `LATENCY OK …`.
- **L16 graduation project**: `lessons/16_capstone/` provides `template_mission.py` (use the `Mission` building blocks to assemble your own task) + `RUBRIC.md` + `validate_mission.py` (checks the task graph includes `Takeoff`+`Land`+`Failsafe`, and all transitions have trigger conditions). `CAPSTONE OK: graph valid …`. The student's custom task must also be `--selftest` green on its own.
