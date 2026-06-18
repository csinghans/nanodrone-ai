"""
Lesson 10 — shared bits for your own voice keyword-spotting (KWS) model.

Defines the command set, the audio feature (MFCC -> a fixed-size "image"), and
the small CNN. record_commands.py, train_kws.py and kws_fly.py all import this.
"""

import numpy as np

SAMPLE_RATE = 16000
DURATION = 1.2  # seconds recorded per command (room for reaction time)
N_SAMPLES = int(SAMPLE_RATE * DURATION)
N_MFCC = 13
N_FRAMES = 44  # MFCC frames kept per sample (pad / truncate to this)

# command label -> world-frame velocity (vx, vy, vz); "land" is special.
COMMANDS = {
    "forward": (1, 0, 0),
    "back": (-1, 0, 0),
    "left": (0, 1, 0),
    "right": (0, -1, 0),
    "up": (0, 0, 1),
    "down": (0, 0, -1),
    "stop": (0, 0, 0),
    "land": (0, 0, 0),
}
# A "background" class for silence / ambient noise. When the model hears it,
# the flight loop ignores it — so not speaking never triggers a random command
# (the main reason naive KWS feels inaccurate).
BACKGROUND = "background"
LABELS = list(COMMANDS) + [BACKGROUND]  # fixed order -> class indices

# Suggested 中文 word to say for each command. The label is just an internal id,
# so you can record ANY sound per slot (Chinese, English, a whistle) — say the
# same thing when flying. These are only shown as a hint while recording.
SAY = {
    "forward": "前進",
    "back": "後退",
    "left": "向左",
    "right": "向右",
    "up": "上升",
    "down": "下降",
    "stop": "停止",
    "land": "降落",
    "background": "（保持安靜）",
}


def wav_to_feat(signal: np.ndarray, sr: int = SAMPLE_RATE) -> np.ndarray:
    """Audio waveform -> (N_FRAMES, N_MFCC) MFCC feature. winstep is chosen so
    N_FRAMES spans the WHOLE clip (the earlier 0.01 s step only covered the first
    ~0.45 s, cutting off words spoken after the prompt)."""
    from python_speech_features import mfcc  # lazy: only needed for real audio

    feat = mfcc(signal, sr, numcep=N_MFCC, winlen=0.025, winstep=0.025, nfft=512)
    if len(feat) < N_FRAMES:
        feat = np.pad(feat, ((0, N_FRAMES - len(feat)), (0, 0)))
    else:
        feat = feat[:N_FRAMES]
    # per-sample normalize so loudness/level doesn't dominate
    return ((feat - feat.mean()) / (feat.std() + 1e-6)).astype(np.float32)


def synthetic_raw(label_idx: int, rng) -> np.ndarray:
    """A fake but class-separable waveform, so the pipeline can be tested without
    a microphone (used by record_commands.py --synthetic and CI). Each command is
    a different tone; the background class is quiet noise."""
    if LABELS[label_idx] == BACKGROUND:
        return (rng.standard_normal(N_SAMPLES) * 50).astype(np.int16)
    t = np.arange(N_SAMPLES) / SAMPLE_RATE
    freq = 200 + label_idx * 150
    sig = np.sin(2 * np.pi * freq * t) * 8000 + rng.standard_normal(N_SAMPLES) * 200
    return sig.astype(np.int16)


def make_net():
    """A compact CNN over the (1, N_FRAMES, N_MFCC)=(1,44,13) MFCC 'image'.

    We FLATTEN the conv features (instead of global-average-pooling) so the
    time-frequency pattern that tells words apart is kept — global pooling threw
    away the temporal structure and the model couldn't separate the commands.
    Two stride-2 convs: 44x13 -> 22x7 -> 11x4, so 32*11*4 = 1408 features."""
    import torch.nn as nn

    return nn.Sequential(
        nn.Conv2d(1, 16, 3, stride=2, padding=1),
        nn.ReLU(),
        nn.Conv2d(16, 32, 3, stride=2, padding=1),
        nn.ReLU(),
        nn.Flatten(),
        nn.Dropout(0.3),
        nn.Linear(32 * 11 * 4, 64),
        nn.ReLU(),
        nn.Linear(64, len(LABELS)),
    )
