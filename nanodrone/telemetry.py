"""nanodrone.telemetry — a flight black box: log every frame, replay it later.

The first thing real-hardware bring-up needs isn't smarter AI — it's being able
to *see what happened* after a flight (a jitter, a misfire, a near-miss). This
logs each frame as newline-JSON (human-readable, greppable, same wire format as
the DroneVoice bridge) so any platform — sim now, Tello/Crazyflie later — that
emits the same rows can be replayed with one tool.
"""

import json
import os

FIELDS = ("t", "x", "y", "z", "tx", "ty", "tz", "yaw")  # one row per frame


class FlightLogger:
    """Append a structured telemetry row per frame; save/load as JSONL."""

    def __init__(self):
        self.rows: list[dict] = []

    def log(self, t: float, pos, target, yaw: float) -> None:
        self.rows.append(
            {
                "t": round(float(t), 4),
                "x": round(float(pos[0]), 4),
                "y": round(float(pos[1]), 4),
                "z": round(float(pos[2]), 4),
                "tx": round(float(target[0]), 4),
                "ty": round(float(target[1]), 4),
                "tz": round(float(target[2]), 4),
                "yaw": round(float(yaw), 4),
            }
        )

    def save(self, path: str) -> int:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for r in self.rows:
                f.write(json.dumps(r) + "\n")
        return len(self.rows)


def load_log(path: str):
    """Read a telemetry JSONL file back into a list of row dicts."""
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
