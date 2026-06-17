# Lesson 6 — 跟隨模式

**目標：** 讓無人機只靠相機跟隨一個移動目標。

這是*視覺伺服（visual servoing）*，閉合完整迴圈 **看見 → 定位 → 移動**：偵測綠色目標（HSV，與 Lesson 2 相同）、用深度影像測距、由無人機姿態重建目標世界座標，再用 PID 飛控尾隨它後方的定點。不需訓練 —— 只是一條清楚的規則。

**執行**

```bash
python lessons/06_follow_me/follow_me.py
python lessons/06_follow_me/follow_me.py --headless   # 驗證 / CI
```

**驗收 ✅** headless 印出 `FOLLOW OK: ... mean bearing error 5.3 deg` —— 只有幾度代表無人機把目標保持在畫面中央並跟上了。

➡️ 完整課程（程式碼 + 講解）：[lessons/06_follow_me](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/06_follow_me)
