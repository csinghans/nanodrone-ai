"""
DroneVoice bridge — drive the nanodrone sim from JSON flight commands over TCP.

The Apple app (Siri / App Intents / in-app mic -> Apple Foundation Model parses
natural language into structured commands) connects here and sends newline-
delimited JSON; this server flies the PyBullet sim so you SEE the drone obey
your phone. Swapping the sim for a real Tello/Crazyflie later keeps this same
JSON protocol.

Commands (one JSON object per line):
  {"action": "takeoff"}
  {"action": "forward", "distance": 1.0}     # metres (default 0.5)
  {"action": "turn_left", "degrees": 45}      # degrees (default 30)
  {"action": "up"|"down"|"left"|"right"|"back"|"stop"|"hover"}
  {"action": "land"}            # descend and settle
  {"action": "emergency_stop"}  # freeze in place immediately

Run:
  python bridge/sim_server.py                 # GUI + listen on 0.0.0.0:9000
  python bridge/sim_server.py --selftest      # scripted, headless (CI)
"""

import argparse
import json
import math
import queue
import socket
import sys
import threading
import time

import numpy as np
import pybullet as p
from gym_pybullet_drones.control.DSLPIDControl import DSLPIDControl
from gym_pybullet_drones.envs.CtrlAviary import CtrlAviary
from gym_pybullet_drones.utils.enums import DroneModel, Physics
from gym_pybullet_drones.utils.utils import sync

from nanodrone import chase_cam, setup_view

START = np.array([0.0, 0.0, 1.0])
DEFAULT_DIST = 0.5  # metres per move command if none given
DEFAULT_DEG = 30.0  # degrees per turn command if none given
BOX_XY, BOX_Z = 3.0, (0.3, 2.5)  # indoor geofence: 6x6 m, 0.3-2.5 m high


def apply_command(cmd: dict, target: np.ndarray, yaw: float):
    """Nudge the flight target/heading from one command. Returns (yaw, mode)
    where mode is '', 'land' or 'emergency' for the loop to handle."""
    action = str(cmd.get("action", "")).lower().replace(" ", "_").replace("-", "_")
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
    elif action in ("turn_left", "turnleft"):
        yaw += math.radians(deg)
    elif action in ("turn_right", "turnright"):
        yaw -= math.radians(deg)
    elif action in ("stop", "hover"):
        pass
    elif action == "land":
        return yaw, "land"
    elif action in ("emergency_stop", "emergency", "estop"):
        return yaw, "emergency"

    target[0] = float(np.clip(target[0], -BOX_XY, BOX_XY))
    target[1] = float(np.clip(target[1], -BOX_XY, BOX_XY))
    target[2] = float(np.clip(target[2], *BOX_Z))
    return yaw, ""


def serve(cmd_queue: "queue.Queue", host: str, port: int) -> None:
    """Accept clients and push each newline-JSON command into cmd_queue."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(1)
    print(f"[bridge] listening on {host}:{port}")
    while True:
        conn, addr = srv.accept()
        print(f"[bridge] client connected: {addr}")
        buf = b""
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break
                buf += data
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        cmd_queue.put(json.loads(line))
                        print(f"[bridge] recv {line.decode(errors='replace')}")
                    except json.JSONDecodeError:
                        print(f"[bridge] bad JSON: {line!r}")
        print("[bridge] client disconnected")


def run(gui: bool, host: str, port: int, selftest: bool) -> None:
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

    cmd_queue: queue.Queue = queue.Queue()
    if selftest:  # scripted commands at given seconds (no socket)
        for t_s, cmd in [
            (0.5, {"action": "takeoff"}),
            (1.5, {"action": "forward", "distance": 1.0}),
            (3.0, {"action": "turn_left", "degrees": 90}),
            (4.0, {"action": "up", "distance": 0.5}),
            (5.0, {"action": "land"}),
        ]:
            cmd_queue.put((t_s, cmd))
    else:
        threading.Thread(
            target=serve, args=(cmd_queue, host, port), daemon=True
        ).start()

    target = START.copy()
    yaw = 0.0
    landing = False
    scripted = []
    if selftest:
        while not cmd_queue.empty():
            scripted.append(cmd_queue.get())

    action_in = np.zeros((1, 4))
    dt = env.CTRL_TIMESTEP
    start_t = time.time()
    duration = 7 * env.CTRL_FREQ if selftest else 10**9
    i = 0
    try:
        while i < duration:
            t = i * dt
            # gather commands due now
            if selftest:
                due = [c for (ts, c) in scripted if abs(ts - t) < dt / 2]
                cmds = due
            else:
                cmds = []
                while not cmd_queue.empty():
                    cmds.append(cmd_queue.get_nowait())
            for cmd in cmds:
                yaw, mode = apply_command(cmd, target, yaw)
                if mode == "land":
                    landing = True
                elif mode == "emergency":
                    target[:] = env._getDroneStateVector(0)[0:3]
                    landing = False
            if cmds:
                print(
                    f"[bridge] target -> x={target[0]:+.2f} y={target[1]:+.2f} "
                    f"z={target[2]:+.2f} yaw={math.degrees(yaw):+.0f} deg",
                    flush=True,
                )

            if landing:
                target[2] = max(BOX_Z[0], target[2] - 0.4 * dt)

            obs, _, _, _, _ = env.step(action_in)
            action_in[0, :], _, _ = ctrl.computeControlFromState(
                control_timestep=dt,
                state=obs[0],
                target_pos=target,
                target_rpy=np.array([0.0, 0.0, yaw]),
            )
            if gui:
                chase_cam(env.CLIENT, obs[0][0:3])
                sync(i, start_t, dt)
            i += 1
    except KeyboardInterrupt:
        print("\n[bridge] stopping.")
    except p.error:
        print("\n[bridge] simulator window closed — stopping.")

    try:
        env.close()
    except p.error:
        pass

    if selftest:
        moved = float(np.linalg.norm(target[0:2] - START[0:2]))
        print(
            f"BRIDGE OK: ran {i} steps, target moved {moved:.2f} m, "
            f"yaw {math.degrees(yaw):.0f} deg, landed."
        )
        assert moved > 0.2, f"commands didn't move the drone ({moved:.2f} m)"
        assert abs(yaw) > 0.05, "turn command had no effect"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--no-gui", action="store_true", help="run without a window")
    ap.add_argument("--selftest", action="store_true", help="scripted, headless (CI)")
    args = ap.parse_args()
    run(
        gui=not (args.no_gui or args.selftest),
        host=args.host,
        port=args.port,
        selftest=args.selftest,
    )


if __name__ == "__main__":
    main()
    sys.exit(0)
