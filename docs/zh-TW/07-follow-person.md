# Lesson 7 — 跟著飛手

**目標：** 在模擬器裡驅動一個人到處走，無人機自己跟著你。

大家想像中的「follow-me 空拍機」。融合 Lesson 5（你操控人）、Lesson 6（視覺跟隨）與**機頭轉向**：每個 tick 無人機偵測橘色的人、算出你的世界座標、**轉向面對你**、尾隨你後方的定點。轉向面對你，正是能跟著你「繞圈」而非只左右移動的關鍵。

**執行**

```bash
pip install -r setup/requirements-extra.txt   # pygame（手把，來自 Lesson 5）
python lessons/07_follow_person/follow_person.py            # 你操控、無人機跟
python lessons/07_follow_person/follow_person.py --headless # 腳本化 demo / CI
```

用右搖桿或方向鍵驅動**人**；無人機是自主的。

**驗收 ✅** headless 讓人走一圈並印出 `FOLLOW OK: ... mean bearing error 1.5 deg` —— 約 1° 代表它全程鎖定你。

➡️ 完整課程（程式碼 + 講解）：[lessons/07_follow_person](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/07_follow_person)
