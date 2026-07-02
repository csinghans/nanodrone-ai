# 總覽

**nanodrone-ai** 教你打造奈米無人機的板載 AI 自主能力，全程從模擬器起步（免費），最終做到一台能離線自飛的真實 Crazyflie。

## 心智模型

自主，就是一個永遠在跑的迴圈：**感知 → 決策 → 動作。**

- **感知：** 讀感測器（相機、測距、IMU、位置）。
- **決策：** 由規劃器或神經網路決定下一步做什麼。
- **動作：** 送一個高階指令給飛控，由飛控處理「維持穩定」這個又快又危險的工作。

自駕車做的正是這件事。我們把它縮小到一台 27 克的四旋翼上。

## 為什麼先做模擬

1. **免費** — 到 Lesson 4 才需要硬體。
2. **安全** — 出 bug 撞壞的是畫面裡的圖，不是真的螺旋槳打到你的手。
3. **快** — 一個晚上就能讓 AI 練上千次飛行。

我們用 [gym-pybullet-drones](https://github.com/utiasDSL/gym-pybullet-drones)，它建模了真實的 Crazyflie 2.x，且能在 Apple Silicon 原生執行。

## 為什麼用奈米機（Crazyflie）

最終目標是**板載、離線**的 AI。Crazyflie + AI-deck 是目前最便宜、又能真正在機身上（用 GAP8 晶片）跑神經網路的可信平台 — 與學術專案 [PULP-Dronet](https://github.com/pulp-platform/pulp-dronet) 同一套作法。

## 課程地圖

課程從第 1 課（你的第一次懸停）一路到第 30 課（總結），分成五個階段：

| 階段 | 課次 | 白話說明 |
|---|---|---|
| 會飛、會看、會決定 | 1–10 | 懸停、相機感知、第一個學出來的行為、手把＋語音控制 |
| 任務 | 11–16 | 把技能組成有安全機制的完整任務，收在有評分表的 capstone |
| 上晶片 | 14b、17–22 | 深度、光流、RL 避障——每一項都蒸餾到塞得進無人機晶片 |
| 前沿 | 23–30 | 飛行黑盒子、真機踏腳石、共用指令協議、nano 世界模型、課程總結 |
| 支線 | DroneVoice | 用同一份協議、開口就能飛無人機的 iPhone app |

一頁式快速上手與閱讀順序在[從這裡開始](START-HERE.md)；
完整的課程依賴圖與設計理由在 [Roadmap](ROADMAP.md)。

下一步：[Lesson 1 — 飛行控制基礎](https://github.com/csinghans/nanodrone-ai/blob/main/lessons/01_hover/README.md)。
