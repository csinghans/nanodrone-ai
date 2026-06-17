"""
Lesson 5 (bonus) — Fly it yourself with an Xbox controller
==========================================================
Lessons 1-4 made the drone fly *itself*. This one hands you the sticks. It's a
fun way to build flight intuition -- and to appreciate how hard the autonomy
was -- by teleoperating the simulated drone with a gamepad.

How it works (same two-layer idea as Lesson 1): the controller doesn't drive the
motors. Each frame we read the sticks, turn them into a desired **velocity**,
integrate that into a moving **target position**, and let the PID flight
controller chase the target. Release the sticks -> the target stops -> the drone
hovers in place.

Controls (body-frame, like an FPV pilot: "forward" follows the nose):
  * Right stick  -> move forward/back + strafe left/right (relative to heading)
  * Left stick   -> up/down (vertical) + yaw (rotate the heading)
  * Keyboard fallback: arrows = move, W/S = up/down, Q/E = yaw left/right

Run:
  python lessons/05_teleop/teleop_xbox.py            # Xbox pad (else keyboard)
  python lessons/05_teleop/teleop_xbox.py --input keyboard
  python lessons/05_teleop/teleop_xbox.py --list     # show pads + live axes
"""

import argparse
import sys
import time

import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

START = np.array([0.0, 0.0, 1.0])
SPEED = 1.0  # metres/second at full stick deflection
YAW_RATE = 1.5  # radians/second at full yaw-stick deflection
DEADZONE = 0.12  # ignore tiny stick noise around centre
# Soft geofence: the target can never leave this box.
BOX_XY = 2.0
BOX_Z = (0.2, 2.5)


def _deadzone(v: float) -> float:
    return 0.0 if abs(v) < DEADZONE else v


class XboxInput:
    """Read an Xbox/SDL gamepad via pygame. Returns world-frame (vx, vy, vz)."""

    def __init__(self, lx=0, ly=1, rx=2, ry=3):
        import pygame  # imported lazily so the sim lessons don't need pygame

        self.pygame = pygame
        pygame.init()
        pygame.joystick.init()
        if pygame.joystick.get_count() == 0:
            raise RuntimeError("no gamepad detected")
        self.js = pygame.joystick.Joystick(0)
        self.js.init()
        self.lx, self.ly, self.rx, self.ry = lx, ly, rx, ry
        print(f"Gamepad: {self.js.get_name()} ({self.js.get_numaxes()} axes)")

    def read(self):
        self.pygame.event.pump()
        rx = _deadzone(self.js.get_axis(self.rx))
        ry = _deadzone(self.js.get_axis(self.ry))
        lx = _deadzone(self.js.get_axis(self.lx))
        ly = _deadzone(self.js.get_axis(self.ly))
        # Sticks read +down / +right; flip so forward/up/CCW are positive.
        # Returns (forward, strafe-left, up, yaw-left).
        return (-ry, -rx, -ly, -lx)

    def close(self):
        self.pygame.quit()


class KeyboardInput:
    """Read the PyBullet GUI keyboard. Arrows = move, W/S = up/down, Q/E = yaw."""

    def read(self):
        keys = p.getKeyboardEvents()

        def down(k):
            return k in keys and keys[k] & p.KEY_IS_DOWN

        fwd = (1.0 if down(p.B3G_UP_ARROW) else 0) - (
            1.0 if down(p.B3G_DOWN_ARROW) else 0
        )
        strafe = (1.0 if down(p.B3G_LEFT_ARROW) else 0) - (
            1.0 if down(p.B3G_RIGHT_ARROW) else 0
        )
        up = (1.0 if down(ord("w")) else 0) - (1.0 if down(ord("s")) else 0)
        yaw = (1.0 if down(ord("q")) else 0) - (1.0 if down(ord("e")) else 0)
        return (fwd, strafe, up, yaw)

    def close(self):
        pass


class SelftestInput:
    """Scripted input (no pad, no GUI) so CI and `--input selftest` can verify
    the flight loop end to end."""

    def __init__(self, steps_per_phase=24):
        # (forward, strafe, up, yaw) per phase: up, forward, yaw, hover.
        self._script = [(0, 0, 1, 0), (1, 0, 0, 0), (0, 0, 0, 1), (0, 0, 0, 0)]
        self._spp = steps_per_phase
        self._i = 0
        self.done = False

    def read(self):
        phase = self._i // self._spp
        self._i += 1
        if phase >= len(self._script):
            self.done = True
            return (0.0, 0.0, 0.0, 0.0)
        return self._script[phase]

    def close(self):
        pass


def list_pads() -> None:
    import pygame

    pygame.init()
    pygame.joystick.init()
    n = pygame.joystick.get_count()
    print(f"Detected {n} gamepad(s).")
    if n == 0:
        print("Pair your Xbox controller (Bluetooth/USB) and try again.")
        return
    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Using: {js.get_name()} with {js.get_numaxes()} axes.")
    print("Move the sticks; Ctrl-C to stop. Note which axis index moves.")
    try:
        for _ in range(200):
            pygame.event.pump()
            axes = [round(js.get_axis(i), 2) for i in range(js.get_numaxes())]
            print("  axes:", axes, end="\r")
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    print()
    pygame.quit()


def make_input(kind: str):
    """Pick an input backend; xbox transparently falls back to keyboard."""
    if kind == "selftest":
        return SelftestInput(), False  # (backend, needs_gui)
    if kind == "keyboard":
        return KeyboardInput(), True
    try:
        return XboxInput(), True
    except Exception as exc:
        print(f"Xbox pad unavailable ({exc}); falling back to keyboard.")
        return KeyboardInput(), True


def fly(kind: str) -> None:
    backend, needs_gui = make_input(kind)
    gui = needs_gui
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
        # No manual RPM sliders: we steer with the gamepad, and the slider reads
        # crash with "Failed to read parameter" the moment the window is closed.
        user_debug_gui=False,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    target = START.copy()
    target_yaw = 0.0
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()

    if gui:
        print("Flying. Right stick = move, left stick = up/down + yaw. Ctrl-C to quit.")
    i = 0
    try:
        while True:
            fwd, strafe, up, yaw_in = backend.read()
            # Turn the heading, then move relative to it (body frame -> world).
            target_yaw += yaw_in * YAW_RATE * dt
            c, s = np.cos(target_yaw), np.sin(target_yaw)
            vx = fwd * c - strafe * s
            vy = fwd * s + strafe * c
            target[0] = float(np.clip(target[0] + vx * SPEED * dt, -BOX_XY, BOX_XY))
            target[1] = float(np.clip(target[1] + vy * SPEED * dt, -BOX_XY, BOX_XY))
            target[2] = float(np.clip(target[2] + up * SPEED * dt, BOX_Z[0], BOX_Z[1]))

            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=obs[0],
                target_pos=target,
                target_rpy=np.array([0.0, 0.0, target_yaw]),
            )
            if gui:
                env.render()
                sync(i, start_t, dt)
            i += 1
            if getattr(backend, "done", False):
                break  # selftest script finished
    except KeyboardInterrupt:
        print("\nLanding (you quit).")
    except p.error:
        print("\nSimulator window closed — stopping.")

    backend.close()
    try:
        env.close()
    except p.error:
        pass  # physics server already gone (window was closed)

    if kind == "selftest":
        moved = np.linalg.norm(target - START)
        assert moved > 0.1, f"target barely moved ({moved:.3f} m) -- loop broken"
        assert abs(target_yaw) > 0.05, f"yaw barely changed ({target_yaw:.3f} rad)"
        print(
            f"SELFTEST OK: ran {i} steps, target moved {moved:.2f} m, "
            f"yaw {np.degrees(target_yaw):.0f} deg."
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", choices=["xbox", "keyboard", "selftest"], default="xbox"
    )
    parser.add_argument("--list", action="store_true", help="list pads + live axes")
    args = parser.parse_args()
    if args.list:
        list_pads()
        return
    fly(args.input)


if __name__ == "__main__":
    main()
    sys.exit(0)
