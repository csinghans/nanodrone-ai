"""
Lesson 4 (runnable now) — shrink the CNN for a microcontroller
==============================================================
The AI-deck's GAP8 has only a few hundred KB of memory and no floating-point
luxury budget -- models run in 8-bit integers. Before touching hardware you can
already do the first, most important step on your Mac: check that Lesson 3's
TinyDronet is small enough, and export it to ONNX (the format you hand to the
GAP8 toolchain).

This script:
  * counts the parameters and prints the float32 vs int8 footprint,
  * confirms the model still works (MAE on the Lesson 3 dataset), and
  * exports output/dronet_cnn.onnx for the GAP8 NNTool/Autotiler flow.

It does NOT do the final GAP8 int8 conversion -- that happens in the
Linux-only GAP SDK (see the README). Here we prove the model is deployable.

Run (after Lesson 3 produced its model + dataset):
  python lessons/04_hardware_gap8/quantize_cnn.py
"""

import os
import sys

import numpy as np
import torch

# Reuse Lesson 3's network definition, trained weights, and dataset.
LESSON3 = os.path.join(os.path.dirname(__file__), "..", "03_autonomy_ai")
sys.path.insert(0, os.path.abspath(LESSON3))

try:
    from train_cnn import BEARING_SCALE, DATA, MODEL, TinyDronet  # noqa: E402
except ImportError as exc:  # pragma: no cover
    print("Could not import Lesson 3's CNN:", exc)
    sys.exit(1)

OUT_ONNX = os.path.join(os.path.dirname(__file__), "output", "dronet_cnn.onnx")
# AI-deck GAP8 L2 memory is ~512 KB; weights must fit alongside code + buffers.
GAP8_BUDGET_KB = 512


def main() -> None:
    if not os.path.exists(MODEL):
        raise SystemExit(
            f"No trained model at {MODEL}.\n"
            "Run Lesson 3 first:\n"
            "  python lessons/03_autonomy_ai/gen_dataset.py\n"
            "  python lessons/03_autonomy_ai/train_cnn.py"
        )

    model = TinyDronet()
    model.load_state_dict(torch.load(MODEL, map_location="cpu"))
    model.eval()

    # --- Footprint analysis -------------------------------------------------
    n_params = sum(p.numel() for p in model.parameters())
    fp32_kb = n_params * 4 / 1024
    int8_kb = n_params * 1 / 1024  # what GAP8 actually stores (8-bit weights)
    print(f"Parameters      : {n_params:,}")
    print(f"float32 weights : {fp32_kb:7.1f} KB  (training / desktop)")
    print(f"int8 weights    : {int8_kb:7.1f} KB  (what GAP8 stores)")
    fits = "YES" if int8_kb < GAP8_BUDGET_KB else "NO"
    print(f"Fits GAP8 (<{GAP8_BUDGET_KB} KB int8)? {fits}")

    # --- Sanity: does the trained model still predict well? -----------------
    if os.path.exists(DATA):
        blob = np.load(DATA)
        X = torch.tensor(blob["X"]).permute(0, 3, 1, 2)
        y = torch.tensor(blob["y"])
        with torch.no_grad():
            pred = model(X) * BEARING_SCALE
        mae = (pred - y).abs().mean().item()
        print(f"float32 MAE on dataset : {mae:.2f} deg")

    # --- Export to ONNX (the hand-off format for the GAP8 toolchain) --------
    os.makedirs(os.path.dirname(OUT_ONNX), exist_ok=True)
    dummy = torch.zeros(1, 3, 64, 64)
    torch.onnx.export(
        model,
        dummy,
        OUT_ONNX,
        input_names=["image"],
        output_names=["bearing"],
        opset_version=17,
        dynamo=False,
    )
    onnx_kb = os.path.getsize(OUT_ONNX) / 1024
    print(f"Exported ONNX   : {OUT_ONNX} ({onnx_kb:.1f} KB)")
    print(
        "\nNext (on Linux, with hardware): feed this ONNX to the GAP8 NNTool "
        "for int8 conversion + Autotiler code generation. See the README."
    )


if __name__ == "__main__":
    main()
