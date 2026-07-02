# nanodrone-ai

給新手的雙語課程：打造**奈米無人機的板載 AI 自主飛行** —
從 $0 純模擬起步，最終做到一台能離線自飛的真實 Crazyflie。

- 第一次來？先看[總覽](00-overview.md)。
- 接著依序完成各課（用上方導覽，或看 [`lessons/`](https://github.com/csinghans/nanodrone-ai/tree/main/lessons) 資料夾）。

![hover](https://raw.githubusercontent.com/csinghans/nanodrone-ai/main/assets/lesson1.gif)
![avoid](https://raw.githubusercontent.com/csinghans/nanodrone-ai/main/assets/lesson3.gif)

*左：模擬懸停（Lesson 1）。右：RL 策略繞過障礙（Lesson 3）。全部在模擬器免費產生。*

<!-- LESSON-TABLE:START -->
| 課程 | 主題 | 成本 |
|------|------|------|
| 0 | [環境建置與專案骨架](00-overview.md) | $0 |
| 1 | [飛行控制基礎（懸停與航點）](01-hover.md) | $0 |
| 2 | [感知（看見障礙物）](02-perception.md) | $0 |
| 3 | [自主決策 AI](03-autonomy-ai.md) | $0 |
| 4 | [真機與板載離線 AI](04-hardware-gap8.md) | 約 US$545 |
| 5 *(加成)* | [用 Xbox 手把親手飛](05-teleop.md) | $0 |
| 6 | [跟隨模式](06-follow-me.md) | $0 |
| 7 | [跟著飛手](07-follow-person.md) | $0 |
| 8 | [跟隨真人（學習式偵測器）](08-follow-real.md) | $0 |
| 9 | [語音操控飛行](09-voice.md) | $0 |
| 10 | [訓練你自己的語音命令](10-voice-train.md) | $0 |
| 11 | [任務狀態機（編排 + failsafe）](11-mission.md) | $0 |
| 12 | [語音驅動的任務轉移](12-voice-mission.md) | $0 |
| 13 | [多模態 mini-capstone：找人 → 跟隨 → 降落](13-find-follow-land.md) | $0 |
| 14a | [簡單建圖與自主巡邏](14a-map-patrol.md) | $0 |
| 14b | [板載預算下的感知（把能力縫回 GAP8）](14b-onboard-budget.md) | $0 |
| 16 | [畢業專題：設計你自己的任務](16-capstone.md) | $0 |
| 17 | [單目深度估計（訓練一個 dense 模型）](17-depth.md) | $0 |
| 18 | [光流 / 視覺里程計（無 GPS 自估狀態）](18-flow.md) | $0 |
| 19 | [更難的多障礙 RL（把感知併入觀測）](19-multi-avoid.md) | $0 |
| 20 | [域隨機化（縮小 sim-to-real 落差）](20-domain-rand.md) | $0 |
| 21 | [知識蒸餾 + 模型壓縮](21-distill.md) | $0 |
| 22 | [把多個能力蒸餾成單一板載策略（Track B 畢業專題）](22-unified.md) | $0 |
| 23 | [飛行黑盒子：遙測與回放](23-telemetry.md) | $0 |
| 24 | [你的第一台真機：平價 Tello（Wi-Fi）](24-tello.md) | $0 |
| 25 | [誠實量測 sim-to-real 落差](25-sim2real.md) | $0 |
| 26 | [實地測試 SOP 與台灣法規](26-field-test.md) | $0 |
| 27 | [一套飛行協定，到處重用](27-protocol.md) | $0 |
| 28 | [解析器擂台（招牌反例，量化版）](28-parser-arena.md) | $0 |
| 29 | [nano 世界模型：隱空間預測做預判式避障](29-world-model.md) | $0 |
| 30 | [課程總結:你蓋出了什麼,數字說話](30-summary.md) | $0 |
<!-- LESSON-TABLE:END -->

> 🌐 Switch language: use the language selector at the top-right to switch to **English**.
