"""
Lesson 10 (step 1) — record your own voice command samples
==========================================================
Say each command a few times; we save the MFCC features as your dataset. Because
it's *your* voice and accent, the model trained on it beats a generic model.

  python lessons/10_voice_train/record_commands.py --reps 8      # record (mic)
  python lessons/10_voice_train/record_commands.py --synthetic 12  # fake (no mic)

Output: output/kws_dataset.npz
"""

import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kws import (  # noqa: E402
    BACKGROUND,
    DURATION,
    LABELS,
    SAMPLE_RATE,
    SAY,
    synthetic_raw,
)

OUT = os.path.join(os.path.dirname(__file__), "output", "kws_dataset.npz")


def record_one() -> np.ndarray:
    """Record one clip and return the RAW waveform (features are computed at
    train time, so we can tweak the feature pipeline without re-recording)."""
    import sounddevice as sd

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    return audio[:, 0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=12, help="samples per command")
    ap.add_argument("--synthetic", type=int, default=0, help="fake N/class, no mic")
    args = ap.parse_args()

    X, y = [], []
    if args.synthetic:
        rng = np.random.default_rng(0)
        for idx in range(len(LABELS)):
            for _ in range(args.synthetic):
                X.append(synthetic_raw(idx, rng))
                y.append(idx)
        print(f"Synthetic dataset: {len(y)} samples.")
    else:
        print(
            "Auto-record: one Enter per class, then it records all reps back-to-back."
        )
        for idx, label in enumerate(LABELS):
            hint = SAY.get(label, label)
            if label == BACKGROUND:
                input(
                    f"\n[{label} / {hint}] stay SILENT — Enter to record {args.reps}x"
                )
            else:
                input(f"\n[{label} / {hint}] — Enter, then say it {args.reps}x")
            for r in range(args.reps):
                print(f"  {r + 1}/{args.reps}  …now…", end="\r", flush=True)
                X.append(record_one())
                y.append(idx)
                time.sleep(0.25)
            print(f"  {label}: recorded {args.reps}        ")
        print(f"Recorded {len(y)} samples across {len(LABELS)} classes.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(  # X is raw int16 waveforms (N, samples)
        OUT, X=np.array(X, dtype=np.int16), y=np.array(y), labels=LABELS
    )
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
