"""
Lesson 28 — the parser arena (the signature counter-example, quantified)
========================================================================
The course's drumbeat is "a general model isn't good enough -> train your own
small one" (L3/L8/L10/L13/L17). This lesson asks the opposite, and proves the
answer with numbers: for turning a *flexible sentence* into a structured command,
a self-trained fixed-vocabulary classifier (Lesson 10 KWS style) is the WRONG
tool — it has no slot for "two metres". A general parser (or, in Phase 3, an
on-device LLM with guided generation that's forced to emit a schema-valid object)
is right. Judgement, not dogma: train when the data is yours and must run on
GAP8; reach for a general model + structured constraints for open language.

Backends scored against bridge/golden_intents.jsonl on four axes:
  accuracy  — full command (action + quantity) matches the golden expected
  schema    — fraction of outputs that pass nanodrone.protocol.validate
  coverage  — fraction of phrases it produced any command for
  cost      — offline & $0 here; the LLM backend needs Apple hardware (Phase 3)

Run:
  python bridge/eval_parsers.py            # print the comparison table
  python bridge/eval_parsers.py --selftest  # asserts (CI)
"""

import json
import os
import sys

from nanodrone.protocol import validate

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_text import parse_fixed_vocab, parse_text  # noqa: E402

GOLDEN = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "golden_intents.jsonl"
)

# Backend C (guided-generation LLM) is the Phase 3 Apple Foundation Model; there's
# no offline stand-in here, so it's reported as SKIPPED rather than faked.
BACKENDS = [
    ("ruleA (rule parser)", parse_text),
    ("kwsB (fixed vocab)", parse_fixed_vocab),
]


def load_golden():
    with open(GOLDEN, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def score(fn, golden):
    n = len(golden)
    exact = covered = valid = 0
    for item in golden:
        cmd = fn(item["text"])
        if cmd is None:
            continue
        covered += 1
        if validate(cmd)[0]:
            valid += 1
        if cmd == item["expected"]:
            exact += 1
    return {
        "acc": exact / n,
        "schema": valid / max(1, covered),
        "coverage": covered / n,
    }


def main() -> None:
    golden = load_golden()
    results = {name: score(fn, golden) for name, fn in BACKENDS}

    print(f"{'backend':22} {'accuracy':>9} {'schema':>8} {'coverage':>9}")
    for name, s in results.items():
        print(f"{name:22} {s['acc']:>9.2f} {s['schema']:>8.2f} {s['coverage']:>9.2f}")
    print(f"{'C (Apple FM, Phase 3)':22} {'SKIPPED — needs Apple Intelligence':>9}")

    a = results["ruleA (rule parser)"]
    b = results["kwsB (fixed vocab)"]
    print(
        f"EVAL OK: ruleA acc={a['acc']:.2f} schema={a['schema']:.2f} | "
        f"kwsB acc={b['acc']:.2f} | covered {len(golden)} phrases"
    )
    if "--selftest" in sys.argv:
        assert (
            a["schema"] == 1.0
        ), f"rule parser emitted invalid commands ({a['schema']:.2f})"
        assert b["acc"] < a["acc"], (
            f"fixed-vocab should lose on flexible sentences "
            f"(kwsB {b['acc']:.2f} vs ruleA {a['acc']:.2f})"
        )


if __name__ == "__main__":
    main()
    sys.exit(0)
