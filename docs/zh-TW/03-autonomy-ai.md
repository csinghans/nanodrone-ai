# Lesson 3 — 自主決策 AI

**目標：** 讓無人機自己**決策**。兩條路線，RL 為主線。

- **Route A（主線）— 強化學習。** 自訂環境獎勵「朝目標前進」、懲罰撞柱；PPO 自行找出繞過去的弧線。（實測：20 回合 100% 到達、0 撞擊。）
- **Route B — 模仿學習。** Lesson 2 的偵測器當*老師*：它替相機影像標註，小 CNN（`TinyDronet`，受 PULP-Dronet 啟發）學會單憑像素預測方位。（實測：驗證誤差約 2°。）

**執行**

```bash
python lessons/03_autonomy_ai/train_rl.py                 # Route A：訓練 + 評估
python lessons/03_autonomy_ai/gen_dataset.py --samples 500  # Route B：產資料（老師）
python lessons/03_autonomy_ai/train_cnn.py                 # Route B：訓練 CNN
```

**驗收 ✅** RL 評估印出 `20 reached goal, 0 crashed (success rate 100%)`，並產生俯視 `trajectory.png` 顯示學到的弧線；CNN 達到很低的驗證 MAE（度）。

➡️ 完整課程（程式碼 + 講解）：[lessons/03_autonomy_ai](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/03_autonomy_ai)

下一步：[Lesson 4 — 真機與板載離線 AI](04-hardware.md)
