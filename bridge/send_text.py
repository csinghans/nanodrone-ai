"""
Lesson 28 — speak (by typing) to the bridge without an iPhone
=============================================================
The "voice stand-in" for anyone without the DroneVoice app: type a natural
sentence, the rule parser turns it into a command, and it's sent to the bridge
over the same JSON protocol the app uses. (The app's job in Phase 3 is exactly
this parse step, done by an on-device LLM instead.)

  python bridge/sim_server.py            # in one terminal
  python bridge/send_text.py "go forward 2 metres"
  python bridge/send_text.py "左轉 90 度"
  python bridge/send_text.py --selftest "turn left 90 degrees"   # parse only, no socket
"""

import argparse
import json
import os
import socket
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_text import parse_text  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--selftest", action="store_true", help="parse only, no socket")
    ap.add_argument("sentence", help="a natural-language flight instruction")
    args = ap.parse_args()

    cmd = parse_text(args.sentence)
    if cmd is None:
        print(f"Sorry, couldn't turn that into a command: {args.sentence!r}")
        sys.exit(1)

    if args.selftest:
        print(f"SEND-TEXT OK: {args.sentence!r} -> {json.dumps(cmd)}")
        return

    with socket.create_connection((args.host, args.port), timeout=5) as s:
        s.sendall((json.dumps(cmd) + "\n").encode())
    print(f"sent {cmd} to {args.host}:{args.port}")


if __name__ == "__main__":
    main()
    sys.exit(0)
