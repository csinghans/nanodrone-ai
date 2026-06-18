"""
Lesson 10 (step 3) — fly with YOUR voice model
==============================================
Listen on the mic, classify each ~1 s window with the model you trained on your
own voice, and fly. World-frame commands (forward/back/left/right/up/down/stop/
land), same flight controller as before.

  python lessons/10_voice_train/kws_fly.py            # your model + mic
  python lessons/10_voice_train/kws_fly.py --selftest # scripted, no mic/model (CI)
"""

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kws import COMMANDS, DURATION, LABELS, SAMPLE_RATE  # noqa: E402

START = np.array([0.0, 0.0, 1.0])
SPEED = 0.8
BOX_XY, BOX_Z = 2.5, (0.3, 2.5)
MODEL = os.path.join(os.path.dirname(__file__), "output", "kws_model.pth")


class KwsListener:  # pragma: no cover - needs a mic + model, user runs this
    """Background thread: record 1 s windows, classify with your model, expose
    the latest confident command via poll()."""

    def __init__(self):
        import queue
        import threading

        import torch
        from kws import make_net, wav_to_feat

        self._torch, self._wav_to_feat = torch, wav_to_feat
        net = make_net()
        net.load_state_dict(torch.load(MODEL, map_location="cpu"))
        net.eval()
        self._net = net
        self._out = queue.Queue()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        print(f"Listening — say: {', '.join(LABELS)}")
        self._thread.start()

    def _run(self):
        import sounddevice as sd

        while not self._stop.is_set():
            audio = sd.rec(
                int(DURATION * SAMPLE_RATE),
                samplerate=SAMPLE_RATE,
                channels=1,
                dtype="int16",
            )
            sd.wait()
            feat = self._wav_to_feat(audio[:, 0])
            x = self._torch.tensor(feat).unsqueeze(0).unsqueeze(0)
            with self._torch.no_grad():
                probs = self._net(x).softmax(1)[0]
            conf, idx = float(probs.max()), int(probs.argmax())
            if conf > 0.6:  # ignore unsure windows (noise / silence)
                self._out.put(LABELS[idx])

    def poll(self):
        latest = None
        while not self._out.empty():
            latest = self._out.get_nowait()
        return latest

    def stop(self):
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.5)


def scripted_label(t: float):
    cues = [(0.5, "forward"), (2.5, "up"), (3.5, "left"), (4.5, "stop"), (5.5, "land")]
    label = None
    for start, lab in cues:
        if t >= start:
            label = lab
    return label


def main(selftest: bool) -> None:
    gui = not selftest
    if not selftest and not os.path.exists(MODEL):
        print(f"No model at {MODEL}. Run record_commands.py then train_kws.py first.")
        return

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

    listener = None
    if not selftest:
        listener = KwsListener()
        listener.start()

    target = START.copy()
    vel = (0, 0, 0)
    landing = False
    action = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    i = 0
    try:
        while True:
            t = i * dt
            label = scripted_label(t) if selftest else (listener.poll())
            if label == "land":
                landing = True
            elif label is not None:
                vel = COMMANDS[label]

            vx, vy, vz = (0, 0, 0) if landing else vel
            target[0] = float(np.clip(target[0] + vx * SPEED * dt, -BOX_XY, BOX_XY))
            target[1] = float(np.clip(target[1] + vy * SPEED * dt, -BOX_XY, BOX_XY))
            if landing:
                target[2] = max(BOX_Z[0], target[2] - 0.4 * dt)
            else:
                target[2] = float(np.clip(target[2] + vz * SPEED * dt, *BOX_Z))

            obs, _, _, _, _ = env.step(action)
            action[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt, state=obs[0], target_pos=target
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
        print(f"KWS-FLY OK: ran {i} steps, moved {moved:.2f} m, landed.")
        assert moved > 0.2, f"scripted commands didn't move the drone ({moved:.2f})"


if __name__ == "__main__":
    main(selftest="--selftest" in sys.argv)
    sys.exit(0)
