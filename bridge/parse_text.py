"""
Lesson 28 — text -> command parsers (the backends the arena compares)
=====================================================================
Two ways to turn a sentence into a drone command, both pure-Python and offline:

  * parse_text       (backend A) — a bilingual *rule* parser: keyword -> action,
                       plus a number+unit grab, so "往前兩公尺" -> forward 2 m.
  * parse_fixed_vocab (backend B) — a *fixed-vocabulary* classifier in the spirit
                       of Lesson 10's KWS: it can pick the action but has no slot
                       for a quantity, so it drops the "two metres".

Lesson 28 grades these (and, optionally, a guided-generation LLM) against a golden
set to show *when* you should train your own small model and when a general model
with structured constraints is the right tool. All outputs are checked against
nanodrone.protocol so nothing illegal reaches a drone.
"""

import re

from nanodrone.protocol import validate

# Bilingual keyword -> action. Order matters: turn / land / takeoff phrases come
# before the single-word movements (so "左轉" is a turn, not a "左" strafe).
_KW = [
    ("turn_left", ["turn left", "左轉", "左转", "向左轉", "向左转"]),
    ("turn_right", ["turn right", "右轉", "右转", "向右轉", "向右转"]),
    ("takeoff", ["takeoff", "take off", "起飛", "起飞"]),
    ("emergency_stop", ["emergency", "緊急", "紧急"]),
    ("land", ["land", "降落", "著陸", "着陆"]),
    ("forward", ["forward", "前進", "前进", "向前", "往前"]),
    ("back", ["backward", "back", "後退", "后退", "向後", "向后", "往後", "往后"]),
    ("up", ["up", "上升", "向上"]),
    ("down", ["down", "下降", "向下"]),
    ("left", ["left", "向左", "左"]),
    ("right", ["right", "向右", "右"]),
    ("stop", ["stop", "hover", "停止", "停", "懸停", "悬停"]),
]
_MOVES = {"forward", "back", "left", "right", "up", "down"}
_CN_NUM = {
    "零": 0,
    "一": 1,
    "兩": 2,
    "两": 2,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
}


def _action(text: str):
    for action, keywords in _KW:
        if any(k in text for k in keywords):
            return action
    return None


def _number(text: str):
    m = re.search(r"(\d+(?:\.\d+)?)", text)
    if m:
        return float(m.group(1))
    for ch, v in _CN_NUM.items():  # a few written Chinese numerals
        if ch in text:
            return float(v)
    return None


def parse_text(s: str):
    """Backend A — rule parser. Sentence -> a full command (with quantity), or
    None. e.g. 'turn left 90 degrees' -> {'action':'turn_left','degrees':90.0}."""
    t = str(s).lower().strip()
    action = _action(t)
    if action is None:
        return None
    cmd = {"action": action}
    num = _number(s)
    if num is not None:
        if action in ("turn_left", "turn_right"):
            cmd["degrees"] = num
        elif action in _MOVES:
            cmd["distance"] = num
    ok, _ = validate(cmd)
    return cmd if ok else None


def parse_fixed_vocab(s: str):
    """Backend B — fixed-vocabulary classifier (Lesson 10 KWS style): action
    only, no quantity slot. Right verb, but it can't carry 'two metres'."""
    action = _action(str(s).lower().strip())
    return {"action": action} if action else None
