"""nanodrone.safety — the failsafe layer as pure, testable functions.

Lesson 11 built a Failsafe *state*; the first time it actually matters is real
hardware (Lesson 24's Tello, a Crazyflie). So the rules are factored out here as
pure functions: battery gate, link watchdog, geofence, and a single
`decide_failsafe` that returns what to do. Pure functions mean you can inject the
faults you'd never dare create on a real battery and unit-test the response.

Reused by Lesson 24 (Tello), Lesson 26 (pre-flight SOP) and DroneVoice Phase 4/5.
"""

import numpy as np

from . import protocol

MIN_BATTERY_PCT = 25.0  # below this, don't take off / land now
LINK_TIMEOUT_S = 2.0  # no command in this long -> lost link


def battery_gate(pct: float, min_pct: float = MIN_BATTERY_PCT) -> bool:
    """True if there's enough battery to fly."""
    return float(pct) >= min_pct


def link_watchdog(
    last_cmd_t: float, now: float, timeout: float = LINK_TIMEOUT_S
) -> bool:
    """True if the control link is alive (a command arrived recently enough)."""
    return (now - last_cmd_t) <= timeout


def geofence_clip(target, xy: float = protocol.BOX_XY, z=protocol.BOX_Z) -> np.ndarray:
    """Clamp a target into the safe box (shared with the sim/protocol)."""
    t = np.asarray(target, dtype=float).copy()
    t[0] = float(np.clip(t[0], -xy, xy))
    t[1] = float(np.clip(t[1], -xy, xy))
    t[2] = float(np.clip(t[2], *z))
    return t


def in_bounds(pos, xy: float = protocol.BOX_XY, z=protocol.BOX_Z) -> bool:
    """Is the drone inside the geofence right now?"""
    return (
        abs(pos[0]) <= xy + 1e-6
        and abs(pos[1]) <= xy + 1e-6
        and z[0] - 1e-6 <= pos[2] <= z[1] + 1e-6
    )


def decide_failsafe(
    battery_pct: float,
    last_cmd_t: float,
    now: float,
    pos,
    *,
    min_pct: float = MIN_BATTERY_PCT,
    timeout: float = LINK_TIMEOUT_S,
) -> str:
    """One decision for the whole safety layer. Returns the first tripped reason:
    'low_batt', 'lost_link', 'out_of_bounds', or 'ok'. The caller maps a non-'ok'
    result to land / hold (Lesson 11's Failsafe state, the Tello's land, ...)."""
    if not battery_gate(battery_pct, min_pct):
        return "low_batt"
    if not link_watchdog(last_cmd_t, now, timeout):
        return "lost_link"
    if not in_bounds(pos):
        return "out_of_bounds"
    return "ok"
