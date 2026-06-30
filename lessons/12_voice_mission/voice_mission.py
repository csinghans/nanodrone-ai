"""
Lesson 12 — Voice-driven mission transitions
=============================================
Lessons 9/10 turned speech into a *continuous nudge* ("hold forward"). Real
missions need spoken commands that switch the **whole phase**: "take off",
"hover", "land". This lesson wires a voice source into the Lesson 11 state
machine, so a word triggers a *transition* instead of a drift.

The key idea is an **adapter layer** (`nanodrone.mission_events`): a keyboard, a
Lesson 9 mic, a Lesson 10 KWS model, and later the DroneVoice app are all just
different ways to produce the same small event vocabulary. The mission only
learns one mapping (`default_event_map`), and silence / unknown words are
rejected so noise never flips a phase.

Run:
  python lessons/12_voice_mission/voice_mission.py             # mic (needs L9 Vosk)
  python lessons/12_voice_mission/voice_mission.py --lang zh   # speak 中文
  python lessons/12_voice_mission/voice_mission.py --selftest  # scripted, no mic (CI)
"""

import os
import sys

try:
    from nanodrone.mission import Mission
    from nanodrone.mission_events import (
        VoiceEventSource,
        default_event_map,
        phrase_to_event,
    )
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import the mission runner:", exc)
    sys.exit(1)


class ScriptedEventSource:
    """Scripted spoken phrases at timestamps (no mic), edge-triggered and adapted
    to mission events. Stands in for `VoiceEventSource` under --selftest/CI, and
    tracks `rejected` (heard a phrase, but it was not a phase command)."""

    def __init__(self, cues, dt: float):
        self._cues = sorted(cues)  # (second, phrase) — mixed en + 中文 + 1 noise
        self._dt = dt
        self._t = 0.0
        self._fired = 0
        self.rejected = 0

    def poll(self):
        self._t += self._dt
        phrase = None
        while self._fired < len(self._cues) and self._cues[self._fired][0] <= self._t:
            phrase = self._cues[self._fired][1]
            self._fired += 1
        if not phrase:
            return None
        event = phrase_to_event(phrase)
        if event is None:  # heard something, but it was not a phase command
            self.rejected += 1
        return event


def live(lang: str) -> None:
    """Fly from the mic, reusing Lesson 9's offline Vosk listener."""
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.join(os.path.dirname(here), "09_voice"))
    from voice import VoiceListener  # Lesson 9's offline speech-to-text

    listener = VoiceListener(lang)
    listener.start()
    source = VoiceEventSource(listener)
    try:
        Mission([], start=(0.0, 0.0, 0.3), gui=True).run(
            max_seconds=1e9, event_source=source
        )
    except KeyboardInterrupt:
        print("\nStopping (you quit).")
    finally:
        listener.stop()


def selftest() -> None:
    """Headless: scripted spoken phrases drive phase transitions; the lone noise
    phrase is rejected, not acted on."""
    dt = 1.0 / 48.0  # matches the mission's ctrl_freq
    cues = [
        (0.5, "takeoff"),
        (3.0, "hover"),
        (4.0, "banana milkshake"),  # noise: not a phase command -> rejected
        (5.0, "降落"),  # land (中文) — proves bilingual events
    ]
    source = ScriptedEventSource(cues, dt)
    m = Mission([], start=(0.0, 0.0, 0.3), gui=False)
    r = m.run(max_seconds=15.0, event_source=source, event_map=default_event_map())

    print(
        "VOICE-MISSION OK: events=[takeoff,hover,land] "
        f"transitions={r['transitions']}, ended in {r['history'][-1]}, "
        f"landed (z={r['final_z']:.2f}), {source.rejected} noise-event rejected"
    )
    assert r["transitions"] == 3, f"expected 3 transitions, got {r['transitions']}"
    assert r["history"][-1] == "Land", r["history"]
    assert r["landed"], f"did not land (z={r['final_z']:.2f})"
    assert source.rejected == 1, f"noise should be rejected once, got {source.rejected}"
    assert not r["in_failsafe"], "voice mission should not trip failsafe"


def main() -> None:
    if "--selftest" in sys.argv:
        selftest()
    else:
        lang = "zh" if "--lang" in sys.argv and "zh" in sys.argv else "en"
        live(lang)


if __name__ == "__main__":
    main()
    sys.exit(0)
