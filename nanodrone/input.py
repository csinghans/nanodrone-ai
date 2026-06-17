"""Shared input backends: read a gamepad or keyboard as (forward, strafe, up,
yaw) in [-1, 1]. First written in Lesson 5, factored out so Lesson 7 (and any
future lesson) can drive something with the same code.
"""

import time

import pybullet as p

DEADZONE = 0.12  # ignore tiny stick noise around centre


def _deadzone(v: float) -> float:
    return 0.0 if abs(v) < DEADZONE else v


class XboxInput:
    """Read an Xbox/SDL gamepad via pygame. Returns (fwd, strafe, up, yaw)."""

    def __init__(self, lx=0, ly=1, rx=2, ry=3):
        import pygame  # imported lazily so non-gamepad lessons don't need pygame

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
    """Scripted input (no pad, no GUI) so CI can verify a control loop."""

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
    """Print detected gamepads and live axis values (for calibration)."""
    import pygame

    pygame.init()
    pygame.joystick.init()
    n = pygame.joystick.get_count()
    print(f"Detected {n} gamepad(s).")
    if n == 0:
        print("Pair your controller (Bluetooth/USB) and try again.")
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
    """Pick an input backend; 'xbox' transparently falls back to keyboard.
    Returns (backend, needs_gui)."""
    if kind == "selftest":
        return SelftestInput(), False
    if kind == "keyboard":
        return KeyboardInput(), True
    try:
        return XboxInput(), True
    except Exception as exc:
        print(f"Xbox pad unavailable ({exc}); falling back to keyboard.")
        return KeyboardInput(), True
