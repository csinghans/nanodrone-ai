# Lesson 14a — Simple mapping & autonomous patrol

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Every mission so far chased a single thing — a point, a person. Real autonomy
(inspection drones, PULP-Dronet) also has to **cover a space** and remember
what's in it. This lesson gives the drone its first piece of **spatial memory**:
it patrols the room's corners and, from the depth camera, builds a 2D map of
where the obstacles are. It also puts the whole depth image to work for the
first time — until now depth was only ever sampled at a single point.

## Concept

It runs on the Lesson 11 state machine: the patrol is just `GoTo` waypoints with
a `Scan` (turn in place) at each corner. Two design choices keep it stable and
honest:

- **`nanodrone.map.OccupancyGrid`** tiles the room into cells. Each frame it
  projects whole depth columns into the world — the *same* geometry the follower
  used for one point (Lesson 2/8: `linearize_depth` + `world_point`) — and marks
  the cells a surface was seen in. A middle band of image rows is used, so the
  empty floor reads as out-of-range and is ignored; only real obstacles mark
  cells. (The grid and the multi-pillar `scene.py` are **new** here — not reused
  from Lesson 3, whose single pillar is wired into the RL-only environment.)
- **`GoTo` marches its setpoint** toward the goal at a fixed speed instead of
  jumping the whole way (a far instant setpoint makes the controller pitch hard
  and tumble), and the patrol keeps a fixed heading between corners so there are
  no large yaw flips — the per-corner `Scan` provides the all-round coverage.

Decision is still high-level setpoints; the PID flies. Two layers, as always.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/14a_map_patrol/patrol.py            # GUI patrol, saves output/map.png
python lessons/14a_map_patrol/patrol.py --headless  # same, no window
python lessons/14a_map_patrol/patrol.py --selftest   # asserts the map (CI)
```

Read [`nanodrone/map.py`](../../nanodrone/map.py) (the grid + depth projection),
then [`patrol.py`](patrol.py) (the `Scan` state and the patrol plan). After a run
look at `output/map.png`: the bright cells are the mapped obstacles, the red ×
marks are the truth, and the white line is the drone's path.

## Checkpoint ✅

`--selftest` flies the patrol headless and prints (measured locally):

```
PATROL OK: visited 4/4 waypoints, mapped 33 occupied cells, found 2/2 known obstacles, saved .../output/map.png
```

It asserts all four corners were reached, the drone landed, and an occupied cell
was mapped within 0.5 m of each known pillar.

## Going further

- The grid's resolution × extent = its memory footprint. How big is it in bytes,
  and would it fit GAP8's 256 KB? That question is Lesson 14b.
- Add ray-casting "free space" (mark cells *along* a ray as empty), not just the
  hit cell — a real occupancy map tracks free vs unknown vs occupied.
- Feed the map back into planning: route the next patrol around mapped obstacles.

---

<a name="中文"></a>
# Lesson 14a — 簡單建圖與自主巡邏

🌐 [English](#lesson-14a--simple-mapping--autonomous-patrol) · **繁體中文**（以下）

## 為什麼

到目前為止每個任務都在追*單一*目標 —— 一個點、一個人。真實自主（巡檢無人機、PULP-Dronet）
還得**涵蓋一塊空間**並記住裡面有什麼。這一課給無人機第一份**空間記憶**：它巡邏房間的四個角落，
用深度相機建出一張「障礙在哪」的 2D 地圖。這也是課程第一次真正用上*整張*深度圖 ——
在此之前深度只被拿來對單一點測距。

## 概念

它跑在 Lesson 11 的狀態機上：巡邏就是一串 `GoTo` 航點，每到一角做一次 `Scan`（原地轉一圈）。
兩個設計選擇讓它既穩又誠實：

- **`nanodrone.map.OccupancyGrid`** 把房間切成格子。每幀把整條深度欄投影到世界 —— 用的是
  跟跟隨器對單點時*同一套*幾何（Lesson 2/8 的 `linearize_depth` + `world_point`）—— 並標記
  看到表面的格子。只取影像中間一段列，所以空地板會被當成超出量程而忽略，只有真正的障礙會標格。
  （佔據格與多柱 `scene.py` 是這一課**新增**的 —— 不是沿用 Lesson 3，那根柱子綁死在 RL 專用環境裡。）
- **`GoTo` 把 setpoint 以固定速度推向終點**，而不是一次瞬移過去（遠距離瞬移目標會讓控制器猛仰衝、翻覆），
  且巡邏在各段之間保持固定機頭、不做大角度轉向 —— 全方位覆蓋交給每個角落的 `Scan`。

決策仍是高階 setpoint，飛行交給 PID。一如往常，雙層架構。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/14a_map_patrol/patrol.py            # GUI 巡邏，存 output/map.png
python lessons/14a_map_patrol/patrol.py --headless  # 同上，不開視窗
python lessons/14a_map_patrol/patrol.py --selftest   # 驗收地圖（CI）
```

請讀 [`nanodrone/map.py`](../../nanodrone/map.py)（佔據格 + 深度投影），再看 [`patrol.py`](patrol.py)
（`Scan` 狀態與巡邏計畫）。跑完看 `output/map.png`：亮的格子是建出的障礙、紅色 × 是真實位置、
白線是無人機航跡。

## 驗收 ✅

`--selftest` headless 飛完巡邏並印出（本機實測）：

```
PATROL OK: visited 4/4 waypoints, mapped 33 occupied cells, found 2/2 known obstacles, saved .../output/map.png
```

它驗證四個角落都到達、無人機降落、且每根已知柱子 0.5 公尺內都有被標為佔據的格子。

## 延伸

- 佔據格的解析度 × 範圍 = 它的記憶體佔用。它有幾 KB？塞得進 GAP8 的 256 KB 嗎？這個問題就是 Lesson 14b。
- 加上射線的「自由空間」標記（把整條射線*沿途*標為空），不只標命中格 —— 真正的佔據圖會分「空 / 未知 / 佔據」。
- 把地圖回饋給規劃：讓下一趟巡邏繞開已標記的障礙。
