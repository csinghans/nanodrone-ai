"""
Lesson 9 — Voice-controlled flight
==================================
Talk to the drone. An **offline speech model** (Vosk — a trained neural net that
runs on your machine, no cloud) turns what you say into words; we map those
words to flight commands and fly. It's another "needs a trained model" capability
(like Lesson 8), and it stays true to the course's on-device, offline theme.

Two layers, as always:
  * speech -> text          (Vosk, the trained model)
  * text   -> command       (parse_command, a tiny rule table)
  * command -> flight        (the PID controller, body-frame like Lesson 5)

Commands: "takeoff", "forward", "back", "left", "right", "up", "down",
          "turn left", "turn right", "stop"/"hover", "land".

Run:
  python lessons/09_voice/voice.py            # listen to your mic (needs Vosk)
  python lessons/09_voice/voice.py --selftest # scripted commands, no mic (CI)
"""

import math
import os
import sys
import time

import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

from nanodrone import chase_cam, setup_view

START = np.array([0.0, 0.0, 1.0])
SPEED = 0.8  # m/s while a movement command is active
YAW_RATE = 1.2  # rad/s while turning
BOX_XY, BOX_Z = 2.5, (0.3, 2.5)

# Bilingual command table: each command maps to a persistent
# (forward, strafe, up, yaw) setpoint and a list of English + 中文 keywords.
# "stop" zeroes the setpoint; "land" ends the flight. Order matters — longer /
# turn / land phrases are checked before the single-word movement ones (so
# "左轉" is a turn, not a "左" strafe).
_CMDS = [
    ("land", ["land", "降落", "著陸"]),
    ((0, 0, 0, 1), ["turn left", "左轉", "向左轉"]),
    ((0, 0, 0, -1), ["turn right", "右轉", "向右轉"]),
    ((0, 0, 0, 0), ["stop", "hover", "takeoff", "停止", "停", "懸停", "起飛"]),
    ((1, 0, 0, 0), ["forward", "前進", "向前"]),
    ((-1, 0, 0, 0), ["backward", "back", "後退"]),
    ((0, 1, 0, 0), ["left", "向左", "左"]),
    ((0, -1, 0, 0), ["right", "向右", "右"]),
    ((0, 0, 1, 0), ["up", "上升", "向上"]),
    ((0, 0, -1, 0), ["down", "下降", "向下"]),
]


def parse_command(text: str):
    """Map recognized speech (English or 中文) to a command. Returns a
    (fwd, strafe, up, yaw) tuple, the string 'land', or None if nothing matched."""
    text = text.lower().strip()
    for command, keywords in _CMDS:
        if any(k in text for k in keywords):
            return command
    return None


class ScriptedVoice:
    """A scripted sequence of spoken phrases (no mic) for CI / --selftest."""

    def __init__(self):
        # (start_second, phrase) — mixed English + 中文 to prove bilingual parsing.
        self._cues = [
            (0.0, "takeoff"),
            (1.0, "前進"),  # forward
            (3.0, "turn left"),
            (4.0, "上升"),  # up
            (5.0, "stop"),
            (6.0, "降落"),  # land
        ]

    def command_at(self, t: float):
        phrase = ""
        for start, ph in self._cues:
            if t >= start:
                phrase = ph
        return parse_command(phrase)


def listen_vosk(lang: str):  # pragma: no cover - needs a mic + model, user runs
    """Yield recognized phrases from the mic using Vosk (offline). `lang` is
    'en' or 'zh' and selects the model in lessons/09_voice/model-<lang>/."""
    import json
    import queue

    import sounddevice as sd
    from vosk import KaldiRecognizer, Model

    model_dir = os.path.join(os.path.dirname(__file__), f"model-{lang}")
    if not os.path.isdir(model_dir):
        examples = {"en": "vosk-model-small-en-us", "zh": "vosk-model-small-cn"}
        print(
            f"No Vosk model for '{lang}'. Download one and unzip it to\n"
            f"  {model_dir}\n"
            f"e.g. {examples.get(lang, '')} from https://alphacephei.com/vosk/models"
        )
        sys.exit(1)
    q = queue.Queue()

    def cb(indata, frames, t, status):
        q.put(bytes(indata))

    rec = KaldiRecognizer(Model(model_dir), 16000)
    with sd.RawInputStream(
        samplerate=16000, blocksize=8000, dtype="int16", channels=1, callback=cb
    ):
        print("Listening — say: takeoff / forward / turn left / up / stop / land")
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                yield json.loads(rec.Result()).get("text", "")
            else:
                yield json.loads(rec.PartialResult()).get("partial", "")


def fly(selftest: bool, lang: str = "en") -> None:
    gui = not selftest
    env = CtrlAviary(
        drone_model=DroneModel.CF2X,
        num_drones=1,
        initial_xyzs=np.array([START]),
        physics=Physics.PYB,
        pyb_freq=240,
        ctrl_freq=48,
        gui=gui,
        user_debug_gui=False,
    )
    ctrl = DSLPIDControl(drone_model=DroneModel.CF2X)
    if gui:
        setup_view(env.CLIENT)

    target = START.copy()
    target_yaw = 0.0
    cmd = (0, 0, 0, 0)  # current persistent command
    landing = False
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()

    voice = None
    script = None
    if selftest:
        script = ScriptedVoice()
    else:
        voice = listen_vosk(lang)

    i = 0
    try:
        while True:
            t = i * dt
            # --- get the latest command ---
            if selftest:
                c = script.command_at(t)
            else:
                c = parse_command(next(voice))
            if c == "land":
                landing = True
            elif c is not None:
                cmd = c

            fwd, strafe, up, yaw_in = cmd
            if landing:
                fwd = strafe = up = yaw_in = 0
                target[2] = max(BOX_Z[0], target[2] - 0.4 * dt)  # ease down

            # --- command -> motion (body-frame, like Lesson 5) ---
            target_yaw += yaw_in * YAW_RATE * dt
            c_, s_ = math.cos(target_yaw), math.sin(target_yaw)
            target[0] = float(
                np.clip(
                    target[0] + (fwd * c_ - strafe * s_) * SPEED * dt, -BOX_XY, BOX_XY
                )
            )
            target[1] = float(
                np.clip(
                    target[1] + (fwd * s_ + strafe * c_) * SPEED * dt, -BOX_XY, BOX_XY
                )
            )
            if not landing:
                target[2] = float(np.clip(target[2] + up * SPEED * dt, *BOX_Z))

            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=obs[0],
                target_pos=target,
                target_rpy=np.array([0.0, 0.0, target_yaw]),
            )
            if gui:
                chase_cam(env.CLIENT, obs[0][0:3])
                env.render()
                sync(i, start_t, dt)
            i += 1
            if selftest and landing and target[2] <= BOX_Z[0] + 0.05:
                break
    except KeyboardInterrupt:
        print("\nStopping (you quit).")
    except p.error:
        print("\nSimulator window closed — stopping.")

    try:
        env.close()
    except p.error:
        pass

    if selftest:
        moved = float(np.linalg.norm(target[0:2] - START[0:2]))
        print(
            f"VOICE OK: ran {i} steps, moved {moved:.2f} m, "
            f"yaw {math.degrees(target_yaw):.0f} deg, landed."
        )
        assert moved > 0.2, f"commands didn't move the drone ({moved:.2f} m)"
        assert abs(target_yaw) > 0.05, "turn command had no effect"


if __name__ == "__main__":
    lang = "zh" if "--lang" in sys.argv and "zh" in sys.argv else "en"
    fly(selftest="--selftest" in sys.argv, lang=lang)
    sys.exit(0)
