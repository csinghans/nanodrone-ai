# Lesson 4 — Real hardware & on-board offline AI

🌐 **English** (below) · [跳到繁體中文](#中文)

> This is the finish line: the same autonomy you built in simulation, running
> **on a real nano-drone, fully offline** — no laptop, no Wi-Fi. Part of this
> lesson you can do **right now for free**; the rest needs hardware (~US$545).

---

## Why

Everything so far ran on your Mac. Real autonomy means the neural network runs
**on the drone itself**. On a 27 g Crazyflie that means the **GAP8 chip** on the
AI-deck — the same setup as the PULP-Dronet research this course is based on.
This lesson bridges simulation → silicon.

## Concept — what runs where

```
        AI-deck (GAP8)                 Crazyflie main MCU (STM32)
   ┌──────────────────────┐          ┌──────────────────────────┐
   │ camera → TinyDronet   │  bearing │ flight controller         │
   │ int8 CNN inference    │ ───────► │ stabilize + execute        │
   │ (Lesson 3's model)    │          │ (firmware, like Lesson 1)  │
   └──────────────────────┘          └──────────────────────────┘
            ON the drone, no PC, no radio link needed = OFFLINE
```

Two separate jobs:

1. **Flight bring-up** — talk to the drone from your PC (cflib) to test takeoff,
   telemetry, and failsafes. Host-side, used only for testing.
2. **AI deployment** — convert TinyDronet to int8 and flash it onto the GAP8 so
   it runs *without* the PC. This is the real goal.

## Hands-on

### ✅ Do this now (free, no hardware)

Shrink Lesson 3's CNN and export it for the GAP8 toolchain:

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-hardware.txt
python lessons/04_hardware_gap8/quantize_cnn.py
```

Verified output on this machine:

```
Parameters      : 26,465
float32 weights :   103.4 KB  (training / desktop)
int8 weights    :    25.8 KB  (what GAP8 stores)
Fits GAP8 (<512 KB int8)? YES
float32 MAE on dataset : 2.02 deg
Exported ONNX   : .../output/dronet_cnn.onnx (105.5 KB)
```

That `25.8 KB` is the whole point: the model the drone learned comfortably fits
the GAP8's memory. `dronet_cnn.onnx` is the file you hand to the GAP8 toolchain.

### 🔌 Do this when you have hardware (~US$545)

1. **Buy** the [Bitcraze AI bundle](https://store.bitcraze.io/products/the-ai-bundle):
   Crazyflie 2.1+, AI-deck 1.1 (GAP8), Flow deck v2, Crazyradio 2.0.
2. **Assemble & update** firmware with the `cfclient` app; note your radio URI.
3. **First flight (props off!)** to confirm connection + telemetry, then a real
   gentle flight with failsafes:
   ```bash
   python lessons/04_hardware_gap8/fly_crazyflie.py --uri radio://0/80/2M/E7E7E7E7E7
   ```
   Read [`fly_crazyflie.py`](fly_crazyflie.py): battery gate, geofenced moves,
   and `MotionCommander` which **always lands on exit** (even on error).
4. **Deploy the AI to the GAP8** (Linux + the [GAP SDK](https://github.com/GreenWaves-Technologies/gap_sdk)):
   feed `dronet_cnn.onnx` to **NNTool** for int8 quantization, generate code with
   the **Autotiler**, and flash it onto the AI-deck. Start from the
   [PULP-Dronet repo](https://github.com/pulp-platform/pulp-dronet), which has the
   full toolchain and examples — this is the hardest, most involved step.
5. **Go offline.** Unplug the PC, turn off the radio link, and confirm the drone
   navigates using only the model on its own GAP8.

## Checkpoint ✅

- **Now:** `quantize_cnn.py` reports the int8 model fits the GAP8 and writes
  `dronet_cnn.onnx`.
- **Hardware:** the drone takes off and lands cleanly from `fly_crazyflie.py`;
  then, with the AI flashed to the AI-deck, it avoids an obstacle **with the
  laptop unplugged** — the course's goal achieved.

## Safety & legal (non-negotiable for hardware)

- Open area, props clear of people; manual RC override ready.
- Failsafes on: link-loss return/land, **geofence**, low-battery land.
- Validate every behaviour in simulation (Lessons 1–3) **before** flying it.
- Follow local rules (e.g. Taiwan CAA remote-drone regulations).

## Going further

- Feed the AI-deck's bearing into an avoidance maneuver on the STM32 (close the
  full on-board loop).
- Re-train TinyDronet on real AI-deck images (sim-to-real gap) to improve it.
- Add ranging/Flow-deck data for robust indoor flight without GPS.

---

<a name="中文"></a>
# Lesson 4 — 真機與板載離線 AI

🌐 [English](#lesson-4--real-hardware--on-board-offline-ai) · **繁體中文**（以下）

> 這是終點線：把你在模擬器裡做出的自主能力，跑在**真實奈米無人機上、完全離線** —— 不靠筆電、不靠 Wi-Fi。這一課有一部分**現在就能免費做**；其餘需要硬體（約 US$545）。

## 為什麼

到目前為止一切都跑在你的 Mac 上。真正的自主，意味著神經網路跑在**無人機本身**。在 27 克的 Crazyflie 上，就是 AI-deck 上的 **GAP8 晶片** —— 與本課程所本的 PULP-Dronet 研究同一套配置。這一課把模擬 → 矽晶接起來。

## 概念 —— 什麼跑在哪裡

```
        AI-deck (GAP8)                 Crazyflie 主控 (STM32)
   ┌──────────────────────┐          ┌──────────────────────────┐
   │ 相機 → TinyDronet      │   方位   │ 飛控                       │
   │ int8 CNN 推論          │ ───────► │ 穩定 + 執行                 │
   │ （Lesson 3 的模型）     │          │ （韌體，如 Lesson 1）       │
   └──────────────────────┘          └──────────────────────────┘
        在無人機上，不需 PC、不需無線連線 = 離線
```

兩件分開的工作：

1. **飛行 bring-up** —— 從 PC 用 cflib 跟無人機溝通，測試起飛、遙測、failsafe。屬主機端，只用於測試。
2. **AI 部署** —— 把 TinyDronet 轉成 int8 並燒進 GAP8，讓它**不靠 PC** 自己跑。這才是真正目標。

## 動手做

### ✅ 現在就做（免費、不需硬體）

把 Lesson 3 的 CNN 瘦身並匯出給 GAP8 工具鏈：

```bash
conda activate nanodrone-ai
pip install -r setup/requirements-hardware.txt
python lessons/04_hardware_gap8/quantize_cnn.py
```

本機實測輸出：

```
Parameters      : 26,465
float32 weights :   103.4 KB  (training / desktop)
int8 weights    :    25.8 KB  (what GAP8 stores)
Fits GAP8 (<512 KB int8)? YES
float32 MAE on dataset : 2.02 deg
Exported ONNX   : .../output/dronet_cnn.onnx (105.5 KB)
```

那個 `25.8 KB` 就是重點：無人機學到的模型輕鬆塞進 GAP8 的記憶體。`dronet_cnn.onnx` 就是你交給 GAP8 工具鏈的檔案。

### 🔌 有硬體後再做（約 US$545）

1. **購買** [Bitcraze AI bundle](https://store.bitcraze.io/products/the-ai-bundle)：Crazyflie 2.1+、AI-deck 1.1（GAP8）、Flow deck v2、Crazyradio 2.0。
2. **組裝並更新**韌體（用 `cfclient` app）；記下你的 radio URI。
3. **第一次飛行（先拆槳！）** 確認連線與遙測正常，再做一次有 failsafe 的溫和飛行：
   ```bash
   python lessons/04_hardware_gap8/fly_crazyflie.py --uri radio://0/80/2M/E7E7E7E7E7
   ```
   請讀 [`fly_crazyflie.py`](fly_crazyflie.py)：電量門檻、地理圍欄式移動，以及 `MotionCommander`（**離開 `with` 一定降落**，連出錯也是）。
4. **把 AI 部署到 GAP8**（需 Linux + [GAP SDK](https://github.com/GreenWaves-Technologies/gap_sdk)）：把 `dronet_cnn.onnx` 餵給 **NNTool** 做 int8 量化、用 **Autotiler** 產生程式碼、燒進 AI-deck。從 [PULP-Dronet repo](https://github.com/pulp-platform/pulp-dronet) 入手（有完整工具鏈與範例）—— 這是全程最難、最繁瑣的一步。
5. **斷線離線。** 拔掉 PC、關閉無線連線，確認無人機**只靠機上 GAP8 的模型**自己導航。

## 驗收 ✅

- **現在：** `quantize_cnn.py` 回報 int8 模型可塞進 GAP8，並寫出 `dronet_cnn.onnx`。
- **硬體：** 無人機能從 `fly_crazyflie.py` 乾淨起飛降落；接著在 AI 燒進 AI-deck 後，**拔掉筆電**仍能避障 —— 達成本課程的最終目標。

## 安全與法規（動硬體不可妥協）

- 空曠處、螺旋槳遠離人；隨時備好可手動接管的 RC。
- 開啟 failsafe：失聯返航/降落、**地理圍欄**、低電降落。
- 任何行為先在模擬（Lesson 1–3）驗證**過**再上真機。
- 遵守當地法規（例如台灣民航局遙控無人機管理規則）。

## 延伸

- 把 AI-deck 的方位輸出餵進 STM32 上的避障動作（閉合完整的板載迴圈）。
- 用真實 AI-deck 影像重新訓練 TinyDronet（縮小 sim-to-real 落差）。
- 加入測距／Flow deck 資料，在無 GPS 的室內穩定飛行。
