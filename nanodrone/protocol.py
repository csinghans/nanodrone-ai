"""nanodrone.protocol — the drone command contract, separate from any drone.

`bridge/sim_server.py` once owned both the protocol (which actions exist, their
defaults, the body-frame math, the geofence) *and* the PyBullet loop. But the
DroneVoice app, a Tello and a Crazyflie all parse the same JSON — if each hard-
codes the action list and defaults, they drift. This module is the single source
of truth: pure data + pure functions, no simulator import, plus a machine-
readable JSON Schema (for Apple's guided generation / any client).

One JSON object per command:
  {"action": "forward", "distance": 1.0}     # metres (default 0.5)
  {"action": "turn_left", "degrees": 45}      # degrees (default 30)
  {"action": "takeoff" | "land" | "stop" | "emergency_stop" | ...}
"""

import math

import numpy as np

# The 13 actions every backend (sim / Tello / Crazyflie / app) agrees on.
ACTIONS = (
    "takeoff",
    "land",
    "forward",
    "back",
    "left",
    "right",
    "up",
    "down",
    "turn_left",
    "turn_right",
    "stop",
    "hover",
    "emergency_stop",
)
DEFAULT_DIST = 0.5  # metres per move command if none given
DEFAULT_DEG = 30.0  # degrees per turn command if none given
START = (0.0, 0.0, 1.0)
BOX_XY = 3.0  # indoor geofence: 6x6 m
BOX_Z = (0.3, 2.5)  # 0.3-2.5 m high
TURNS = {"turn_left", "turn_right"}

# accept a few spellings, normalize to the canonical action name
_ALIASES = {
    "turnleft": "turn_left",
    "turnright": "turn_right",
    "estop": "emergency_stop",
    "emergency": "emergency_stop",
}


def normalize_action(action: str) -> str:
    """Canonical action name: lowercase, spaces/dashes -> underscore, aliases."""
    a = str(action).lower().strip().replace(" ", "_").replace("-", "_")
    return _ALIASES.get(a, a)


def validate(cmd: dict):
    """Check one command. Returns (ok: bool, reason: str)."""
    if not isinstance(cmd, dict) or "action" not in cmd:
        return False, "missing 'action'"
    action = normalize_action(cmd["action"])
    if action not in ACTIONS:
        return False, f"unknown action '{cmd['action']}'"
    for key in ("distance", "degrees"):
        if key in cmd:
            try:
                v = float(cmd[key])
            except (TypeError, ValueError):
                return False, f"{key} is not a number"
            if not math.isfinite(v):
                return False, f"{key} is not finite"
            if key == "distance" and v < 0:
                return False, "distance must be >= 0"
    return True, "ok"


def step_target(cmd: dict, target: np.ndarray, yaw: float):
    """Apply one command to a flight target/heading (body-frame, geofenced).
    Mutates `target` in place; returns (yaw, mode) where mode is '', 'land' or
    'emergency' for the caller's loop to handle. Identical to the bridge's
    original apply_command — that logic now lives here."""
    action = normalize_action(cmd.get("action", ""))
    dist = float(cmd.get("distance", DEFAULT_DIST))
    deg = float(cmd.get("degrees", DEFAULT_DEG))
    c, s = math.cos(yaw), math.sin(yaw)  # body -> world rotation

    if action == "takeoff":
        target[2] = max(target[2], 1.0)
    elif action == "forward":
        target[0] += dist * c
        target[1] += dist * s
    elif action == "back":
        target[0] -= dist * c
        target[1] -= dist * s
    elif action == "left":  # body +y is left
        target[0] -= dist * s
        target[1] += dist * c
    elif action == "right":
        target[0] += dist * s
        target[1] -= dist * c
    elif action == "up":
        target[2] += dist
    elif action == "down":
        target[2] -= dist
    elif action == "turn_left":
        yaw += math.radians(deg)
    elif action == "turn_right":
        yaw -= math.radians(deg)
    elif action in ("stop", "hover"):
        pass
    elif action == "land":
        return yaw, "land"
    elif action == "emergency_stop":
        return yaw, "emergency"

    target[0] = float(np.clip(target[0], -BOX_XY, BOX_XY))
    target[1] = float(np.clip(target[1], -BOX_XY, BOX_XY))
    target[2] = float(np.clip(target[2], *BOX_Z))
    return yaw, ""


def schema() -> dict:
    """A JSON Schema for one command — hand this to Apple guided generation or
    any client so the action enum and defaults have a single source."""
    return {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": list(ACTIONS)},
            "distance": {
                "type": "number",
                "minimum": 0,
                "description": f"metres (default {DEFAULT_DIST})",
            },
            "degrees": {
                "type": "number",
                "description": f"degrees (default {DEFAULT_DEG})",
            },
        },
        "required": ["action"],
        "additionalProperties": False,
    }
