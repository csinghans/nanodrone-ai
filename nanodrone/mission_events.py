"""nanodrone.mission_events — turn command sources into MISSION EVENTS.

A *mission event* switches the whole behaviour — ``"takeoff"``, ``"hover"``,
``"land"`` — unlike the continuous nudges (forward / left / up) that Lessons 5,
9 and 10 used. Each source speaks differently, so each gets a tiny adapter; they
all emit the same small event vocabulary, so the Lesson 11 state machine only
has to learn one mapping (`default_event_map`).

Why adapt at the keyword level instead of reusing Lesson 9's `parse_command`?
Because `parse_command` collapses *takeoff*, *stop* and *hover* into the same
zero-velocity nudge `(0, 0, 0, 0)` — fine for "hold the stick" control, useless
for a phase machine that must tell "take off" apart from "hover" apart from a
movement word. So we map phrases straight to events here.

Sources adapted:
  * typed / spoken phrases (e.g. Lesson 9's mic) -> `phrase_to_event`
  * Lesson 10 KWS labels (forward/stop/land/...) -> `kws_to_event`
"""

from .mission import Hover, Land, Takeoff

EVENTS = ("takeoff", "hover", "land")  # phase-switching events the machine knows

# Bilingual keyword -> event. Keeps takeoff / hover / land DISTINCT (unlike
# parse_command). Chinese lists traditional + simplified, like Lesson 9.
_PHRASE_KEYWORDS = [
    ("takeoff", ["takeoff", "take off", "起飛", "起飞"]),
    ("land", ["land", "降落", "著陸", "着陆"]),
    ("hover", ["hover", "stop", "停止", "停", "懸停", "悬停"]),
]

# Lesson 10 KWS labels -> events. KWS has no "takeoff", and its movement labels
# (forward/back/left/right/up/down) are *continuous* control, not phase
# switches, so they map to no event here.
_KWS_TO_EVENT = {"land": "land", "stop": "hover"}


def phrase_to_event(text):
    """A typed or spoken phrase (English or 中文) -> a mission event, or None."""
    if not text:
        return None
    t = str(text).lower().strip()
    for event, keywords in _PHRASE_KEYWORDS:
        if any(k in t for k in keywords):
            return event
    return None


def kws_to_event(label, conf: float = 1.0, threshold: float = 0.6):
    """A Lesson 10 KWS label (+confidence) -> a mission event, or None.

    `None`/`background`/low-confidence -> None, so silence never switches phase
    (the same 'when unsure, do nothing' rule Lesson 10 relies on)."""
    if label is None or conf < threshold:
        return None
    return _KWS_TO_EVENT.get(str(label))


def default_event_map():
    """event string -> zero-arg factory returning a mission `State`.
    `hover` holds until the next event (a very long Hover)."""
    return {
        "takeoff": lambda: Takeoff(height=1.0),
        "hover": lambda: Hover(seconds=1e9),
        "land": lambda: Land(),
    }


class VoiceEventSource:  # pragma: no cover - needs a mic; the user runs this
    """Adapt Lesson 9's `VoiceListener`: `poll()` -> mission event or None.
    Tracks `rejected` (heard a phrase, but it wasn't a phase event)."""

    def __init__(self, listener):
        self._listener = listener
        self.rejected = 0

    def poll(self):
        phrase = self._listener.poll()
        if not phrase:
            return None
        event = phrase_to_event(phrase)
        if event is None:
            self.rejected += 1
        return event


class KwsEventSource:  # pragma: no cover - needs a mic + trained model
    """Adapt Lesson 10's `KwsListener`: `poll()` -> mission event or None."""

    def __init__(self, listener, threshold: float = 0.6):
        self._listener = listener
        self.threshold = threshold
        self.rejected = 0

    def poll(self):
        label = self._listener.poll()  # already confidence-gated inside Lesson 10
        if label is None:
            return None
        event = kws_to_event(label, threshold=self.threshold)
        if event is None:
            self.rejected += 1
        return event
