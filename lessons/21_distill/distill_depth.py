"""
Lesson 21 — knowledge distillation + compression (extend L4's quantize)
=======================================================================
Lesson 4 only checked a model's footprint and exported it. But Lessons 17/20 may
grow a depth model bigger than you want on GAP8. The fix is **distillation**:
train a large, accurate teacher, then train a much smaller student to mimic it.
The student keeps most of the accuracy at a fraction of the size — the active
"make it fit" step Lesson 4 stopped short of, complementing Lesson 14b (which
measured whether a model fits; this makes one fit).

Run (depends on Lesson 17's network):
  python lessons/21_distill/distill_depth.py
  python lessons/21_distill/distill_depth.py --selftest   # tiny run, asserts (local)
Exports output/student_depth.onnx (git-ignored).
"""

import os
import sys

import torch
import torch.nn as nn

try:
    _L17 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "17_depth"
    )
    sys.path.insert(0, _L17)
    from train_depth import MAX_DEPTH, TinyDepthNet, abs_rel, gen_dataset
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 17's depth network:", exc)
    sys.exit(1)

GAP8_BUDGET_KB = 512
OUT_ONNX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "student_depth.onnx"
)


class StudentDepthNet(nn.Module):
    """A much smaller encoder-decoder (half-ish the channels) — the compressed
    model meant to run on GAP8."""

    def __init__(self):
        super().__init__()
        self.enc = nn.Sequential(
            nn.Conv2d(3, 8, 5, stride=2, padding=2),
            nn.ReLU(),
            nn.Conv2d(8, 16, 3, stride=2, padding=1),
            nn.ReLU(),
            nn.Conv2d(16, 16, 3, stride=2, padding=1),
            nn.ReLU(),
        )
        self.dec = nn.Sequential(
            nn.Upsample(scale_factor=2, mode="bilinear", align_corners=False),
            nn.Conv2d(16, 8, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(8, 1, 3, padding=1),
            nn.Sigmoid(),
        )

    def forward(self, x):
        return self.dec(self.enc(x)).squeeze(1)


def _train(net, X, target, epochs, device):
    opt = torch.optim.Adam(net.parameters(), lr=1e-3)
    loss_fn = nn.L1Loss()
    y = target.to(device)
    for _ in range(epochs):
        net.train()
        order = torch.randperm(len(X))
        for i in range(0, len(X), 32):
            b = order[i : i + 32]
            opt.zero_grad()
            loss_fn(net(X[b]), y[b]).backward()
            opt.step()
    net.eval()
    return net


def _kb(net):
    return sum(p.numel() for p in net.parameters()) / 1024


def main() -> None:
    selftest = "--selftest" in sys.argv
    n, e = (180, 40) if selftest else (320, 60)
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print(f"[INFO] generating {n} samples ...")
    X, D = gen_dataset(n)
    Xt = torch.tensor(X).permute(0, 3, 1, 2).to(device)
    yt = torch.tensor(D / MAX_DEPTH).to(device)
    n_val = max(8, int(0.25 * len(Xt)))
    Xtr, Xva = Xt[n_val:], Xt[:n_val]
    Dva = D[:n_val]

    # 1. teacher: train the full TinyDepthNet on the true depth
    teacher = _train(TinyDepthNet().to(device), Xtr, yt[n_val:], e, device)
    # 2. student: distill — learn to MATCH the teacher's predictions, not labels
    with torch.no_grad():
        soft = teacher(Xtr)
    student = _train(StudentDepthNet().to(device), Xtr, soft, e, device)

    with torch.no_grad():
        t_err = abs_rel(teacher(Xva).cpu().numpy() * MAX_DEPTH, Dva)
        s_err = abs_rel(student(Xva).cpu().numpy() * MAX_DEPTH, Dva)
    kept = 100 * t_err / max(s_err, 1e-6)
    t_kb, s_kb = _kb(teacher), _kb(student)

    os.makedirs(os.path.dirname(OUT_ONNX), exist_ok=True)
    torch.onnx.export(
        student.to("cpu"),
        torch.zeros(1, 3, 64, 64),
        OUT_ONNX,
        input_names=["image"],
        output_names=["depth"],
        opset_version=17,
        dynamo=False,
    )
    print(
        f"DISTILL OK: teacher {t_kb:.1f} KB / student {s_kb:.1f} KB "
        f"({t_kb / s_kb:.1f}x smaller, <{GAP8_BUDGET_KB} fits), "
        f"AbsRel teacher={t_err:.3f} student={s_err:.3f} (kept {kept:.0f}%)"
    )
    if selftest:
        assert s_kb < GAP8_BUDGET_KB, f"student too big ({s_kb:.1f} KB)"
        assert (
            s_kb < 0.6 * t_kb
        ), f"student not smaller enough ({s_kb:.1f} vs {t_kb:.1f})"
        assert kept > 60, f"student lost too much accuracy (kept {kept:.0f}%)"


if __name__ == "__main__":
    main()
    sys.exit(0)
