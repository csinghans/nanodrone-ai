# 課程完結 — v1.0

🌐 [English](COURSE_COMPLETE.md) · **繁體中文**

三十課之前，目標只有一句話：**一台 27 克、離線、在 512 KB 晶片上自己飛的無人機——
從 $0 的模擬器出發。**到 v1.0 為止課程已完結：每一課都實作完成、雙語齊備，
並由 `--selftest` 印出 `XXX OK` 並 assert 驗證。

## 課程範圍

| 層級 | 課次 | 內容 |
|---|---|---|
| **核心路徑** | 1–13、14a、16 | 會飛、會看、會決定——再把技能組成有守衛的任務狀態機，收在有評分表的 capstone。請按順序走。 |
| **上晶片軌** | 4、14b、17–22 | 深度、光流、RL 避障、域隨機化、蒸餾——一切往 512 KB int8 裡壓。 |
| **sim-to-real 軌** | 23–26 | 飛行黑盒子、$100 Tello 踏腳石、gap 量測、外場 SOP＋台灣法規。 |
| **協議與 app** | 27–28、DroneVoice | 模擬器、Tello、Crazyflie 與 iPhone app 共用的一份 13 動作 JSON 合約。 |
| **Research preview** | 29 | nano V-JEPA 世界模型——隱空間預測、collision heads、純視覺 latent MPC 與學習型策略，全部量測。 |
| **總結** | 30 | 用數字回望整條弧線＋重新驗證共用合約的畢業檢查。 |

## 皇冠數字（全部實測、全部可重現）

| 主張 | 數字 |
|---|---|
| 模型會「選」，不只會「偵測」 | veer-ranking **1.00**（隨機 0.5） |
| 在世界模型上學出的策略 | 0.8–1.6 m/s 整條掃描帶（150 條航道）*與*雜訊航道墜機 **0%** |
| 對照：反應式 | 高速下墜機最高 **60–70%** |
| 整套堆疊上 GAP8 預算 | **137.3 KB < 512 KB**，每次決策 ~8 ms |
| sim-to-real gap：標價，然後買回 | AUC 0.96 → 0.82 → **0.92** |

## 凍結政策

v1.0 凍結課程範圍。此後本 repo 接受 **bug 修正、文件改進與 CI 維護**——
不再新增大型課程。一直長大的課程永遠教不完；這是一本寫完的書。
（修正請走 issue 流程——見 [CONTRIBUTING.zh-TW.md](CONTRIBUTING.zh-TW.md)。）

## 故事的下一站

Lesson 29 刻意做成 *preview*：教會概念、在模擬器裡證明它們。深入研究——
更難的世界、模型側記憶、度量接地的隱空間、Crazyflie＋AI-deck 真機——
在續作研究專案裡繼續：

**→ [microdrone-world-model](https://github.com/csinghans/microdrone-world-model)**

課程 repo 證明「這學得會」；研究 repo 負責「把它磨利」。
