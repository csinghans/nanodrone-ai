"""
Tiny CLI to send a command to the DroneVoice bridge (stands in for the app).

  python bridge/send.py takeoff
  python bridge/send.py forward 1.5      # distance in metres
  python bridge/send.py turn_left 90     # degrees
  python bridge/send.py land
  python bridge/send.py --host 192.168.1.20 forward 1
"""

import argparse
import json
import socket
import sys

from nanodrone.protocol import normalize_action

TURNS = {"turn_left", "turn_right"}  # which actions take 'degrees' not 'distance'


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("action")
    ap.add_argument(
        "amount", nargs="?", type=float, help="metres, or degrees for turns"
    )
    args = ap.parse_args()

    cmd = {"action": args.action}
    if args.amount is not None:
        is_turn = normalize_action(args.action) in TURNS
        cmd["degrees" if is_turn else "distance"] = args.amount

    with socket.create_connection((args.host, args.port), timeout=5) as s:
        s.sendall((json.dumps(cmd) + "\n").encode())
    print(f"sent {cmd} to {args.host}:{args.port}")


if __name__ == "__main__":
    main()
    sys.exit(0)
