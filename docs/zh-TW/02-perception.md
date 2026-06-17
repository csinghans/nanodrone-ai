# Lesson 2 — 感知

**目標：** 給無人機一台相機，偵測障礙物 —— *有多遠*、*在哪個方向*。

我們裝上前向相機、在前方放紅色障礙，跑經典電腦視覺流程（「感知」階段）：用 OpenCV HSV 門檻化紅色像素 → 找出色塊形心 → 由形心在視野中的位置算出**方位**、由深度影像（把 PyBullet 深度緩衝轉成公尺）算出**距離**。

**執行**

```bash
python lessons/02_perception/perception_demo.py
```

**驗收 ✅** 印出類似 `Obstacle detected: 1.80 m ahead, bearing -12.2 deg (left).`，並存下標註圖 `detection.png`。

➡️ 完整課程（程式碼 + 講解）：[lessons/02_perception](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/02_perception)

下一步：[Lesson 3 — 自主決策 AI](03-autonomy-ai.md)
