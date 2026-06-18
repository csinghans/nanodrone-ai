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
# Keywords list BOTH traditional and simplified Chinese, because the Vosk CN
# model outputs simplified (前进 / 后退 / 左转 / 右转 / 起飞 / 悬停).
_CMDS = [
    ("land", ["land", "降落", "著陸", "着陆"]),
    ((0, 0, 0, 1), ["turn left", "左轉", "左转", "向左轉", "向左转"]),
    ((0, 0, 0, -1), ["turn right", "右轉", "右转", "向右轉", "向右转"]),
    (
        (0, 0, 0, 0),
        ["stop", "hover", "takeoff", "停止", "停", "懸停", "悬停", "起飛", "起飞"],
    ),
    ((1, 0, 0, 0), ["forward", "前進", "前进", "向前"]),
    ((-1, 0, 0, 0), ["backward", "back", "後退", "后退"]),
    ((0, 1, 0, 0), ["left", "向左", "左"]),
    ((0, -1, 0, 0), ["right", "向右", "右"]),
    ((0, 0, 1, 0), ["up", "上升", "向上"]),
    ((0, 0, -1, 0), ["down", "下降", "向下"]),
]

# Restrict the recognizer to just the command words (a Vosk "grammar"). This
# hugely improves accuracy for command-and-control with a small model. Words
# must match the model's vocabulary (simplified for the CN model).
GRAMMAR = {
    "en": [
        "takeoff",
        "forward",
        "back",
        "left",
        "right",
        "up",
        "down",
        "turn left",
        "turn right",
        "stop",
        "hover",
        "land",
    ],
    "zh": [
        "起飞",
        "前进",
        "后退",
        "向左",
        "向右",
        "上升",
        "下降",
        "左转",
        "右转",
        "停止",
        "悬停",
        "降落",
    ],
}


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


class VoiceListener:  # pragma: no cover - needs a mic + model, user runs this
    """Listen to the mic with Vosk (offline) on a background thread. poll()
    returns the latest recognized phrase (or None) WITHOUT blocking, so the
    flight loop keeps running at full rate. `lang` is 'en' or 'zh' and selects
    the model in lessons/09_voice/model-<lang>/."""

    def __init__(self, lang: str):
        import json
        import queue
        import threading

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
        self._sd, self._json = sd, json
        model = Model(model_dir)
        grammar = json.dumps(GRAMMAR.get(lang, []) + ["[unk]"])
        try:  # restrict to command words for much better accuracy
            self._rec = KaldiRecognizer(model, 16000, grammar)
        except Exception:  # model without grammar support -> open vocabulary
            self._rec = KaldiRecognizer(model, 16000)
        self._audio = queue.Queue()
        self._phrases = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        print("Listening — say: takeoff / forward / turn left / up / stop / land")
        self._thread.start()

    def _run(self):
        def cb(indata, frames, t, status):
            self._audio.put(bytes(indata))

        with self._sd.RawInputStream(
            samplerate=16000, blocksize=4000, dtype="int16", channels=1, callback=cb
        ):
            while not self._stop.is_set():
                try:
                    data = self._audio.get(timeout=0.2)
                except Exception:
                    continue
                if self._rec.AcceptWaveform(data):
                    text = self._json.loads(self._rec.Result()).get("text", "")
                    if text.strip():
                        self._phrases.put(text)

    def poll(self):
        """Return the most recent recognized phrase since the last poll, or None."""
        latest = None
        while not self._phrases.empty():
            latest = self._phrases.get_nowait()
        return latest

    def stop(self):
        self._stop.set()


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

    script = ScriptedVoice() if selftest else None
    listener = None
    if not selftest:
        listener = VoiceListener(lang)
        listener.start()

    i = 0
    try:
        while True:
            t = i * dt
            # --- get the latest command (non-blocking; sim runs every frame) ---
            if selftest:
                c = script.command_at(t)
            else:
                phrase = listener.poll()
                c = parse_command(phrase) if phrase else None
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

    if listener is not None:
        listener.stop()
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
