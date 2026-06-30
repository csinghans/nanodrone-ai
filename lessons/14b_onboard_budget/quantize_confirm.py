"""
Lesson 14b (step 1) — quantize the confirm classifier for GAP8
==============================================================
Lesson 13 trained a "person vs background" confirm classifier on your Mac in
float32. The AI-deck's GAP8 has no float budget and only a few hundred KB — models
run in 8-bit integers. This sews that capability back toward the on-board target
(the whole point of the course) by answering, honestly, the three questions
Lesson 4 first raised, now for a perception model that actually gates a mission:

  1. How big is it in int8, and does it fit the GAP8 budget (<512 KB)?
  2. How much accuracy do we lose going float32 -> int8?
  3. Can we hand it to the GAP8 toolchain? (export ONNX)

Reuses Lesson 4's footprint math and Lesson 13's ConfirmCNN + data generator.

Run (after Lesson 13's train_confirm.py):
  python lessons/14b_onboard_budget/quantize_confirm.py
  python lessons/14b_onboard_budget/quantize_confirm.py --selftest   # asserts (local)
"""

import copy
import os
import sys

import torch

try:
    _L13 = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "13_find_follow_land",
    )
    sys.path.insert(0, _L13)
    from train_confirm import MODEL as CONFIRM_MODEL
    from train_confirm import ConfirmCNN, gen_dataset
except ImportError as exc:  # pragma: no cover - friendly beginner message
    print("Could not import Lesson 13's confirm model:", exc)
    sys.exit(1)

GAP8_BUDGET_KB = 512
OUT_ONNX = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "output", "confirm_int8.onnx"
)


def fake_int8(model):
    """Per-tensor symmetric 8-bit quantize-then-dequantize of every weight, so we
    can measure the accuracy int8 would cost — without the brittle backend-
    specific quantization APIs. (On GAP8 the NNTool does the real conversion.)"""
    q = copy.deepcopy(model)
    with torch.no_grad():
        for p in q.parameters():
            mx = float(p.abs().max())
            if mx > 0:
                scale = mx / 127.0
                p.copy_((p / scale).round().clamp(-127, 127) * scale)
    return q


def accuracy(model, X, y, device) -> float:
    with torch.no_grad():
        prob = torch.sigmoid(model(X.to(device))).cpu()
    return float(((prob > 0.5).float() == y).float().mean())


def main() -> None:
    selftest = "--selftest" in sys.argv
    if not os.path.exists(CONFIRM_MODEL):
        raise SystemExit(
            f"No confirm model at {CONFIRM_MODEL}.\n"
            "Train it first: python lessons/13_find_follow_land/train_confirm.py"
        )
    device = "cpu"  # tiny model; CPU keeps quantize/eval deterministic
    model = ConfirmCNN().to(device)
    model.load_state_dict(torch.load(CONFIRM_MODEL, map_location=device))
    model.eval()

    # --- Footprint (same math as Lesson 4) ---------------------------------
    n_params = sum(p.numel() for p in model.parameters())
    fp32_kb = n_params * 4 / 1024
    int8_kb = n_params * 1 / 1024
    fits = int8_kb < GAP8_BUDGET_KB

    # --- Accuracy cost of int8 ---------------------------------------------
    n_eval = 80 if selftest else 200
    Xn, yn = gen_dataset(n_eval, seed=1)
    X = torch.tensor(Xn).permute(0, 3, 1, 2)
    y = torch.tensor(yn)
    acc_fp32 = accuracy(model, X, y, device)
    acc_int8 = accuracy(fake_int8(model), X, y, device)
    drop = acc_fp32 - acc_int8

    # --- Export ONNX for the GAP8 toolchain --------------------------------
    os.makedirs(os.path.dirname(OUT_ONNX), exist_ok=True)
    torch.onnx.export(
        model,
        torch.zeros(1, 3, 64, 64),
        OUT_ONNX,
        input_names=["image"],
        output_names=["person_logit"],
        opset_version=17,
        dynamo=False,
    )

    print(f"Parameters      : {n_params:,}")
    print(f"float32 weights : {fp32_kb:7.1f} KB")
    print(f"int8 weights    : {int8_kb:7.1f} KB  (what GAP8 stores)")
    print(
        f"QUANT OK: int8 model {int8_kb:.1f} KB < {GAP8_BUDGET_KB} KB budget, "
        f"val acc fp32 {acc_fp32:.2f} -> int8 {acc_int8:.2f} (drop {drop:.2f}), "
        f"ONNX {os.path.getsize(OUT_ONNX) / 1024:.1f} KB"
    )
    if selftest:
        assert fits, f"int8 model {int8_kb:.1f} KB does not fit {GAP8_BUDGET_KB} KB"
        assert acc_fp32 > 0.8, f"fp32 model unexpectedly weak ({acc_fp32:.2f})"
        assert drop < 0.15, f"int8 accuracy drop too large ({drop:.2f})"


if __name__ == "__main__":
    main()
    sys.exit(0)
