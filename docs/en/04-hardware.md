# Lesson 4 — Real hardware & on-board offline AI

**Goal:** run the autonomy **on a real nano-drone, fully offline** — no laptop,
no Wi-Fi. Part is free now; the rest needs hardware (~US$545).

The neural network runs on the **GAP8** chip on the Crazyflie AI-deck (the
PULP-Dronet setup), while the STM32 flight controller stabilizes and executes.

**Do now (free):** shrink Lesson 3's CNN and export it for the GAP8 toolchain.

```bash
pip install -r setup/requirements-hardware.txt
python lessons/04_hardware_gap8/quantize_cnn.py
```

It confirms the int8 model (~26 KB) fits the GAP8's memory and writes
`dronet_cnn.onnx`.

**With hardware:** buy the Bitcraze AI bundle, bring up flight with
`fly_crazyflie.py` (failsafes included), then convert + flash the model to the
AI-deck via the Linux GAP SDK (NNTool + Autotiler) and fly **offline**.

➡️ Full lesson (code + walkthrough): [lessons/04_hardware_gap8](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/04_hardware_gap8)
