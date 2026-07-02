# Glossary — the course's terms, in plain words

Terms in the order you'll meet them. Each entry: what it is, and why this
course cares.

## Flying

- **Simulator (PyBullet)** — a physics engine that pretends to be the real
  world. Crashes cost nothing, and the sim can tell you things a real drone
  can't (exact positions), which is where free training labels come from.
- **Flight controller** — the always-on firmware that keeps a drone upright
  hundreds of times per second. In this course your AI *never* replaces it.
- **Two-layer split** — the course's first rule: AI sends simple commands
  ("forward at 0.8 m/s"), the flight controller turns them into motor speeds.
- **PID controller** — the classic feedback recipe (Proportional-Integral-
  Derivative): steer harder the further you are from the target. It's the
  flight controller's core, and Lesson 1's hover.
- **Setpoint** — the "please be here / fly this fast" command the AI layer
  sends down to the flight controller.
- **Waypoint** — a point in space the drone flies to; a route is just a list
  of them. Lesson 1's square challenge is four waypoints.
- **Yaw** — rotation about the vertical axis: which way the nose points,
  without going anywhere. (Its siblings: pitch = nose up/down, roll = lean
  left/right.)
- **Body-frame vs world-frame** — "forward" as the *drone* sees it vs "east"
  as the *map* sees it. Gamepad and voice commands arrive body-frame and are
  converted before the flight controller sees them.
- **State machine** — a mission written as named phases (Takeoff → Search →
  Land) with explicit rules for moving between them. Predictable, debuggable.
- **Failsafe** — the phase every mission can jump to when something's wrong
  (low battery, lost link, out of bounds): land, safely, now.
- **Geofence** — a software box the drone must stay inside.
- **Odometry** — the drone's own estimate of where it is, from its sensors.
  "Using odometry" = using self-knowledge, not world-knowledge.

## Learning

- **Neural network / CNN** — a function with millions of adjustable knobs; a
  CNN (convolutional NN) is the kind that reads images. "Training" = turning
  the knobs until outputs match labelled examples.
- **Label** — the answer attached to a training example. The course's
  signature move: in a simulator, labels are *free* (the sim knows the truth).
- **Dataset** — many (input, label) pairs. You'll generate your own, by
  flying.
- **Policy** — any rule that maps what the drone senses to what it does next.
  Can be hand-written (if-then, cost functions) or learned (a network).
- **Imitation learning** — learning a policy by copying recorded examples of
  behaviour (state → action) instead of trial and error — Lesson 3's other
  route to the same skill.
- **Reinforcement learning (RL) / PPO** — learning a policy by trial and
  error against a *reward* instead of labels. PPO is the workhorse algorithm
  used here (Lessons 3, 19, 29).
- **Reward** — the score RL climbs: progress is good, crashing is very bad.
  Designing it is half the craft.
- **Observation** — everything the policy is allowed to see at each step.
  What you put in it decides what can be learned.
- **Keyword spotting (KWS)** — recognizing a small fixed set of spoken words
  ("takeoff", "left") on-device — far smaller than full speech-to-text.
  Lessons 9–10.
- **MFCC** — the compact "fingerprint of a sound" fed to the voice model: a
  tiny image of which frequencies were loud, when. What makes a nano KWS net
  possible.
- **AUC** — a 0.5-to-1 score for "does this detector rank dangers above
  non-dangers?" 0.5 = coin flip, 1.0 = perfect ranking.

## Fitting on the chip

- **GAP8 / AI-deck** — the target hardware: an ultra-low-power 8-core chip
  (on the Crazyflie's AI-deck) with ~512 KB of fast memory. The course's
  budget ceiling.
- **int8 / quantization** — storing network weights as 1-byte integers
  instead of 4-byte floats: 4× smaller, nearly as accurate. How nano models
  fit.
- **Footprint / activations** — a model's true memory bill: weights *plus*
  the intermediate tensors (activations) and working buffers. Weights alone
  understate it — the course budgets all three.
- **Distillation** — training a small "student" network to imitate a big
  "teacher", keeping most of the skill at a fraction of the size.

## Seeing and predicting

- **HSV mask** — picking out pixels by colour in hue/saturation/value space
  (steadier under lighting changes than raw RGB). Lesson 2 finds the target
  this way.
- **Contour / centroid** — the outline drawn around the mask's blob, and that
  blob's centre pixel — the image-side answer to "where is it?".
- **Bearing** — the left/right angle from the camera's centreline to the
  target: the one number that turns "I see it" into "steer this way".
- **Visual servoing** — steering straight off what the camera sees (keep the
  target centred), no map in between — Lessons 6–8.
- **Depth map** — an image where each pixel says "how far away". Lesson 17
  squeezes one out of a single ordinary camera.
- **Optical flow** — how each pixel *moves* between frames; motion betrays
  distance and speed.
- **Occupancy grid** — a top-down map of "where I've seen stuff", built as
  the drone flies.
- **Latent / embedding** — a short list of numbers a network uses as its
  internal summary of an image. Lesson 29 predicts *these* instead of pixels.
- **World model** — a model that predicts what happens *next* (given what you
  see and what you do) — the ingredient that turns reacting into
  anticipating.
- **V-JEPA** — a research approach ("joint-embedding predictive
  architecture"): predict the future in latent space, never generate pixels.
  Lesson 29 is a nano-scale distillation of the idea.
- **Horizon** — how far ahead a prediction looks (e.g. 667 ms). Multiple
  horizons = anticipation at several time scales.
- **MPC (model-predictive control)** — a planner that "imagines" each
  candidate action with a model and picks the cheapest future.
- **FOV (field of view)** — the wedge of the world the camera can see (60°
  here). What's outside it does not exist to a memoryless model — measured
  honestly in Lesson 29.

## Getting real

- **Sim-to-real gap** — everything the simulator gets wrong about reality
  (optics, textures, airflow). It's measured, priced, and narrowed — never
  assumed away.
- **Domain randomization** — training across randomized appearances and
  physics so the model stops memorizing one clean simulator (Lesson 20, 29).
- **Selftest / checkpoint** — every script's `--selftest` prints an `XXX OK`
  line and *asserts* it. If the line prints, the claim held on your machine
  too.
