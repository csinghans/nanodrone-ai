# Lesson 8 — 跟隨真人（學習式偵測器）

**目標：** 跟隨一個色彩規則無法分離的真實人物 —— 所以我們訓練一個 CNN。

這是課程中第一個「**需要先訓練**」才會動的能力。人物是多色小人（藍衣甚至會跟地板混淆），所以我們不用色彩門檻，而是訓練一個小 `PersonCNN` 回答「人在哪個方向」。標籤由模擬器真值免費提供；距離來自深度感測器；yaw 跟隨迴圈沿用 Lesson 7。

**執行（先訓練，再飛）**

```bash
python lessons/08_follow_real/gen_person_dataset.py    # 1. 產資料（真值標籤）
python lessons/08_follow_real/train_person_cnn.py      # 2. 訓練（MPS）
python lessons/08_follow_real/follow_real.py           # 3. 你操控、無人機跟
python lessons/08_follow_real/follow_real.py --headless # 腳本化 demo / 驗證
```

**驗收 ✅** 訓練達到約 1.2° 驗證 MAE；headless 跟隨印出 `FOLLOW OK (CNN): ... mean true bearing error 14.1 deg` —— 無人機用自己學來的偵測器跟上人，全程沒有色彩規則。

➡️ 完整課程（程式碼 + 講解）：[lessons/08_follow_real](https://github.com/csinghans/nanodrone-ai/tree/main/lessons/08_follow_real)
