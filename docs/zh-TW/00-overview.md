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

| 課程 | 你會學到 |
|------|----------|
| 0 | 在 Mac 上建好 Python + 模擬器 |
| 1 | 讓無人機懸停與飛航點 |
| 2 | 從相機偵測障礙物 |
| 3 | 讓神經網路駕駛無人機（避障） |
| 4 | 部署到真機，完全離線飛行 |
| 5 *(加成)* | 用 Xbox 手把親手飛模擬無人機 |
| 6 | 用相機跟隨移動目標（視覺伺服） |
| 7 | 跟隨你操控的人（轉機頭面對） |
| 8 | 用訓練出的偵測器跟隨「真人」（CNN） |

下一步：[Lesson 1 — 飛行控制基礎](https://github.com/csinghans/nanodrone-ai/blob/main/lessons/01_hover/README.md)。
