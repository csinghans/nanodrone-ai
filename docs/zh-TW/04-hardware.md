# Lesson 4 — 真機與板載離線 AI

**目標：** 讓自主能力跑在**真實奈米無人機上、完全離線** —— 不靠筆電、不靠 Wi-Fi。一部分現在就能免費做，其餘需要硬體（約 US$545）。

神經網路跑在 Crazyflie AI-deck 的 **GAP8** 晶片上（PULP-Dronet 的配置），由 STM32 飛控負責穩定與執行。

**現在就做（免費）：** 把 Lesson 3 的 CNN 瘦身並匯出給 GAP8 工具鏈。

```bash
pip install -r setup/requirements-hardware.txt
python lessons/04_hardware_gap8/quantize_cnn.py
```

它會確認 int8 模型（約 26 KB）塞得進 GAP8 記憶體，並寫出 `dronet_cnn.onnx`。

**有硬體後：** 購買 Bitcraze AI bundle、用 `fly_crazyflie.py` 做飛行 bring-up（含 failsafe），再透過 Linux 上的 GAP SDK（NNTool + Autotiler）把模型轉換並燒進 AI-deck，最後**離線**飛行。

➡️ 完整課程（程式碼 + 講解）：[lessons/04_hardware_gap8](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/04_hardware_gap8)
