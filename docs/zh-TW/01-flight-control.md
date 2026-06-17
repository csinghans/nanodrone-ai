# Lesson 1 — 飛行控制基礎

**目標：** 讓模擬的 Crazyflie 懸停、再飛航點 —— 免費、不需硬體。

無人機有兩個控制層。**飛控**（韌體）負責穩定、把「飛到 X」轉成馬達轉速；**你的程式**負責挑目標。這個迴圈 —— **感知 → 決策 → 動作** —— 貫穿整門課。

**執行**

```bash
python lessons/01_hover/hover_demo.py
```

**驗收 ✅** PyBullet 視窗中四旋翼升到約 1 公尺並穩定懸停；終端機印出 `Done: hovered at [0.0, 0.0, 1.0] for 10 s.`

➡️ 完整課程（程式碼 + 講解）：[lessons/01_hover](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/01_hover)

下一步：[Lesson 2 — 感知](02-perception.md)
