# Lesson 5（加成課）— 用 Xbox 手把親手飛

**目標：** 用手把遙控模擬無人機 —— 與 Lesson 1–4 的自主形成有趣對照，也是建立飛行直覺最快的方式。

手把不直接控馬達（與 Lesson 1 同樣的雙層架構）：每幀讀搖桿 → 想要的**速度** → 積分成會移動的**目標位置** → PID 飛控去追。鬆開搖桿就懸停。

**執行**

```bash
pip install -r setup/requirements-extra.txt        # pygame（Lesson 5 專用）
python lessons/05_teleop/teleop_xbox.py            # Xbox 手把（否則鍵盤）
python lessons/05_teleop/teleop_xbox.py --list     # 校準軸
```

操控（世界座標）：**右搖桿**水平移動、**左搖桿**改變高度。鍵盤後備：方向鍵 + `W`/`S`。

**驗收 ✅** 視窗開啟、無人機隨你的搖桿飛行，鬆手即懸停。不用手把也能驗證迴圈：`python lessons/05_teleop/teleop_xbox.py --input selftest`。

➡️ 完整課程（程式碼 + 講解）：[lessons/05_teleop](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/05_teleop)
