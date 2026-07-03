"""nanodrone — shared core for the course lessons.

Capabilities first written in a lesson, factored out here so later lessons build
on them instead of copying:
  * detect  — colour-blob detection + pixel-to-world geometry (Lesson 2)
  * input   — gamepad / keyboard / selftest backends (Lesson 5)
  * view    — GUI camera + look (the chase cam from Lesson 7)
"""

__version__ = "1.0.0"

from .detect import (
    GREEN,
    ORANGE,
    RED,
    Blob,
    detect_blob,
    linearize_depth,
    world_point,
)
from .input import (
    KeyboardInput,
    SelftestInput,
    XboxInput,
    list_pads,
    make_input,
)
from .view import chase_cam, setup_view

__all__ = [
    "Blob",
    "detect_blob",
    "linearize_depth",
    "world_point",
    "RED",
    "GREEN",
    "ORANGE",
    "make_input",
    "list_pads",
    "XboxInput",
    "KeyboardInput",
    "SelftestInput",
    "setup_view",
    "chase_cam",
]
