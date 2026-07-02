# Lesson 13 — Multimodal mini-capstone: find → follow → land

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Combine voice, vision and the mission brain into one flight: the drone finds a person, follows them, and lands when you say so. · **Builds on:** L11, L12, L8

## Why

This is the first time the whole course collapses into one sentence you can say
out loud: *"take off, find the person, follow them, and land when I say so."*
Four capabilities you built separately now cooperate on one state machine:

- **orchestration** — the Lesson 11 mission state machine
- **a spoken command** — "land", highest priority (Lesson 12 events)
- **learned vision** — Lesson 8's person follower
- **a NEW small model** — a "person vs background" confirm classifier

Why the new model? Lesson 8's detector *always* answers "which way is the
person?" — even when there is no person, it points at *something*. A mission that
must decide **whether to start following** can't trust that, or it would chase a
floor seam. So we train one more tiny model — the course's signature move, one
more time — to gate the Search → Follow transition.

## Concept

States run on the Lesson 11 runner: **Takeoff → Search → Follow → Land**, with a
strict priority: `land` (spoken) > `Failsafe` > vision.

- **Search** hovers and sweeps the yaw. Every few frames it runs the **confirm
  classifier** on the camera; only when `P(person) > 0.6` does it hand off to
  Follow. The trained model — not a colour rule — decides when to follow.
- **Follow** reuses Lesson 8's math exactly: bearing from the learned PersonCNN
  (if you trained it) and range from the depth sensor; it eases toward the
  person at `DESIRED_DIST`.
- A spoken `land` (here, a scripted command) interrupts everything and lands.

The lesson uses two extension points the runner gained for richer missions:
`setup(m)` (spawn the person, load the models) and `on_frame(m)` (move the person,
fire the land command). States read the camera through `m.env`.

> **Training the gate**: `train_confirm.py` makes its own data from the simulator
> (person in front = 1, person behind = 0 — labels are free) and trains a tiny
> classifier with a max-pool head, so a person *anywhere* in view lights it up.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/13_find_follow_land/train_confirm.py    # 1. train the confirm gate
python lessons/13_find_follow_land/mission.py           # 2. watch it (GUI)
python lessons/13_find_follow_land/mission.py --headless   # scripted demo
python lessons/13_find_follow_land/mission.py --selftest    # asserts (no GUI)
```

Read [`mission.py`](mission.py) — the `Search`/`Follow` states and the priority
rule — then [`train_confirm.py`](train_confirm.py). Following uses Lesson 8's
PersonCNN if `output/person_cnn.pth` exists; otherwise the follow loop falls back
to the simulator's ground-truth bearing, so the orchestration and the confirm
gate are exercised end-to-end even before you train Lesson 8.

## Checkpoint ✅

`train_confirm.py --selftest` trains on a small self-generated set and prints:

```
CONFIRM-CNN OK: trained 160 samples, val acc=1.00, saved .../output/confirm_cnn.pth
```

`mission.py --selftest` then runs the whole mission headless and prints
(measured locally):

```
CAPSTONE-MINI OK: Search->Follow in 0.1s (confirm gate p=1.00), tracked 47 frames mean bearing err 10.2 deg, land->landed z=0.40
```

It asserts the run went Search → Follow (through the confirm gate), tracked the
person within ~18° mean bearing error, never tripped Failsafe, and landed on a
`land` command.

## Going further

- Quantize the confirm CNN to int8 and check it fits the GAP8 budget — that's
  Lesson 14b.
- Replace the scripted `land` with a live mic (Lesson 12's `VoiceEventSource`).
- Honest gap: here the person is scripted and bearing error is scored against
  ground truth. On a real drone there is no ground truth and people get
  occluded — the tracking robustness work lives in the later lessons.

---

<a name="中文"></a>
# Lesson 13 — 多模態 mini-capstone：找人 → 跟隨 → 降落

🌐 [English](#lesson-13--multimodal-mini-capstone-find--follow--land) · **繁體中文**（以下）

> **一句話：**把語音、視覺和任務大腦合成一趟飛行：無人機自己找到人、跟著走，你一聲令下就降落。 · **建立在：**第 11 課、第 12 課、第 8 課

## 為什麼

這是整門課第一次能濃縮成一句你能講出口的話：*「起飛、找到那個人、跟著他、我說降落就降落。」*
你分頭做出來的四種能力，現在在同一台狀態機上協作：

- **編排** —— Lesson 11 的任務狀態機
- **口語命令** —— 「降落」，最高優先（Lesson 12 的事件）
- **學習式視覺** —— Lesson 8 的跟人偵測器
- **一個新的小模型** —— 「人 vs 背景」確認分類器

為什麼要新模型？Lesson 8 的偵測器*永遠*回答「人在哪個方向？」—— 就算根本沒有人，它也會指向*某個東西*。
一個必須決定**該不該開始跟隨**的任務不能信這個，否則會去追一條地板接縫。所以我們再訓一個小模型 ——
課程的招牌動作再來一次 —— 來把關 Search → Follow 的轉移。

## 概念

狀態跑在 Lesson 11 的 runner 上：**Takeoff → Search → Follow → Land**，並有嚴格優先序：
`land`（口語）> `Failsafe` > 視覺。

- **Search** 原地懸停並掃描 yaw。每幾幀對相機跑**確認分類器**；只有當 `P(人) > 0.6` 才交棒給 Follow。
  決定何時跟隨的是訓練出的模型，不是顏色規則。
- **Follow** 完全沿用 Lesson 8 的數學：方位由學習式 PersonCNN（若你有訓練）給、距離由深度感測器給；
  以 `DESIRED_DIST` 為目標緩緩靠近。
- 口語 `land`（這裡是腳本化命令）會打斷一切並降落。

本課用到 runner 為更複雜任務新增的兩個擴充點：`setup(m)`（生成人、載入模型）與
`on_frame(m)`（移動人、觸發 land）。狀態透過 `m.env` 讀相機。

> **訓練這個門**：`train_confirm.py` 自己從模擬器產資料（人在前方=1、人在後方=0 —— 標籤免費），
> 用 max-pool head 訓一個 tiny 分類器，讓視野中*任何位置*的人都能點亮它。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/13_find_follow_land/train_confirm.py    # 1. 先訓練確認門
python lessons/13_find_follow_land/mission.py           # 2. 看它跑（GUI）
python lessons/13_find_follow_land/mission.py --headless   # 腳本化展示
python lessons/13_find_follow_land/mission.py --selftest    # 驗收（不開視窗）
```

請讀 [`mission.py`](mission.py) —— `Search`/`Follow` 兩個狀態與優先序規則 —— 再看
[`train_confirm.py`](train_confirm.py)。跟隨在 `output/person_cnn.pth` 存在時用 Lesson 8 的 PersonCNN；
否則 follow 迴圈退回模擬器的 ground-truth 方位，所以即使你還沒訓練 Lesson 8，編排與確認門也能端到端跑通。

## 驗收 ✅

`train_confirm.py --selftest` 用小批自產資料訓練並印出：

```
CONFIRM-CNN OK: trained 160 samples, val acc=1.00, saved .../output/confirm_cnn.pth
```

`mission.py --selftest` 接著 headless 跑完整任務並印出（本機實測）：

```
CAPSTONE-MINI OK: Search->Follow in 0.1s (confirm gate p=1.00), tracked 47 frames mean bearing err 10.2 deg, land->landed z=0.40
```

它驗證流程走了 Search → Follow（經過確認門）、跟隨期平均方位誤差在 ~18° 內、全程未觸發 Failsafe、
並在 `land` 命令下降落。

## 延伸

- 把確認 CNN 量化成 int8、檢查是否塞得進 GAP8 預算 —— 那是 Lesson 14b。
- 把腳本化的 `land` 換成真麥克風（Lesson 12 的 `VoiceEventSource`）。
- 誠實的落差：這裡的人是腳本化的、方位誤差是對 ground truth 量的。真機沒有 ground truth、人會被遮擋 ——
  追蹤魯棒性的工作留在後面的課。
