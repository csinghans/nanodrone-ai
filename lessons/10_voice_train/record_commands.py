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
    DURATION,
    LABELS,
    SAMPLE_RATE,
    SAY,
    synthetic_feat,
    wav_to_feat,
)

OUT = os.path.join(os.path.dirname(__file__), "output", "kws_dataset.npz")


def record_one() -> np.ndarray:
    import sounddevice as sd

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE), samplerate=SAMPLE_RATE, channels=1, dtype="int16"
    )
    sd.wait()
    return wav_to_feat(audio[:, 0])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8, help="samples per command")
    ap.add_argument("--synthetic", type=int, default=0, help="fake N/class, no mic")
    args = ap.parse_args()

    X, y = [], []
    if args.synthetic:
        rng = np.random.default_rng(0)
        for idx in range(len(LABELS)):
            for _ in range(args.synthetic):
                X.append(synthetic_feat(idx, rng))
                y.append(idx)
        print(f"Synthetic dataset: {len(y)} samples.")
    else:
        print("Recording. When prompted, say the word clearly once.")
        for idx, label in enumerate(LABELS):
            for r in range(args.reps):
                input(
                    f"  [{label} / {SAY[label]}] {r + 1}/{args.reps} — Enter, speak..."
                )
                time.sleep(0.2)
                X.append(record_one())
                y.append(idx)
        print(f"Recorded {len(y)} samples across {len(LABELS)} commands.")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    np.savez_compressed(
        OUT, X=np.array(X, dtype=np.float32), y=np.array(y), labels=LABELS
    )
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
