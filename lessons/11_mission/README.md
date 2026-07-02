# Lesson 11 — Mission state machine (orchestration + failsafe)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Build a mission brain that walks the drone through take off, go, hover, land — and drops into a safety state when things go wrong. · **Builds on:** L5

## Why

Every flight script so far (Lessons 5–10, the DroneVoice bridge) copied the same
`CtrlAviary + DSLPIDControl` loop: build the env, each frame work out a target,
hand it to the controller, step the physics. To string behaviours together —
*"take off → go somewhere → hover → land"* — you first need something that knows
**which phase you are in** and **when to move on**.

That something is a **state machine**, the mental model real autonomy stacks
(ROS, PX4) are built on. This lesson is the turning point of the course:
Lessons 1–10 were about *building* capabilities (training models, writing
perception); from here on we *compose* them. Everything later — voice-driven
missions, find-and-follow, mapping, the graduation project — stands on this.

## Concept

`nanodrone/mission.py` factors the shared loop out once:

- **`State`** — one phase. It reads the live drone state off the mission and
  returns the high-level setpoint it wants this frame: `(target_pos, yaw)`.
  Built-ins: `Takeoff`, `Hover`, `GoTo`, `Land`, and `Failsafe`.
- **`Mission`** — the runner: owns the env + controller + the one shared
  while-loop, steps through your list of states, and **watches a geofence every
  frame**. If a phase ever asks to leave the safe box (6×6 m, 0.3–2.5 m high),
  or you call `request_failsafe(...)` yourself (e.g. a lost radio link), it drops
  everything into `Failsafe` — hold position, then land — no matter what the
  rest of the plan wanted.

The two-layer split still holds: a `State` only ever produces a setpoint;
`DSLPIDControl` (the firmware) turns it into motor speeds. **A state never
touches a motor.** Note the runner indexes `obs[0]` but does not bake
`num_drones=1` into the loop body — there is room to grow.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/11_mission/mission_demo.py            # GUI: takeoff→goto→hover→land
python lessons/11_mission/mission_demo.py --headless  # same, no window
python lessons/11_mission/mission_demo.py --selftest   # scripted checks (CI)
```

Read [`mission_demo.py`](mission_demo.py) (how you assemble a plan from states)
and then [`nanodrone/mission.py`](../../nanodrone/mission.py) — each `State` is a
few lines, and the `Mission.run()` loop is the heartbeat every earlier lesson
copied: **sense → decide → act → transition.**

## Checkpoint ✅

`--selftest` runs two headless checks and prints (measured locally):

```
MISSION OK: ran 4 states [Takeoff>GoTo>Hover>Land], moved 1.04 m, landed at z=0.40
FAILSAFE OK: geofence breach -> Hover -> Land, ended safe (z=0.39)
```

The first asserts the full plan runs, moves, and lands; the second asserts an
out-of-bounds goal trips `Failsafe` and the drone still ends safely on the
ground.

## Going further

- Compare the `Mission.run()` loop to a ROS 2 behaviour tree / PX4 commander —
  the same state machine migrates to a real flight controller.
- Add a `Turn` state, or give `GoTo` a speed limit.
- **Next:** Lesson 12 drives these transitions *by voice* — the same state
  machine, with spoken commands choosing the next phase.

---

<a name="中文"></a>
# Lesson 11 — 任務狀態機（編排 + failsafe）

🌐 [English](#lesson-11--mission-state-machine-orchestration--failsafe) · **繁體中文**（以下）

> **一句話：**打造任務大腦：讓無人機照起飛、前往、懸停、降落一步步走，出狀況就自動進入安全狀態。 · **建立在：**第 5 課

## 為什麼

到目前為止每一支飛行腳本（Lesson 5–10、DroneVoice 橋接）都抄了同一套
`CtrlAviary + DSLPIDControl` 迴圈：建環境、每幀算出一個目標、交給控制器、推進物理。
要把多個行為串起來 —— *「起飛 → 飛到某處 → 懸停 → 降落」* —— 你得先有一個東西，
知道**現在在哪個階段**、以及**何時切換到下一個**。

那個東西就是**狀態機（state machine）**，也是 ROS、PX4 等真實自主系統的核心心智模型。
這一課是整個課程的轉折點：Lesson 1–10 在「**打造**能力」（訓模型、寫感知），
從這課起進入「**組合**能力」。後面所有課（語音任務、找人跟隨、建圖、畢業專題）都站在它上面。

## 概念

`nanodrone/mission.py` 把共用迴圈抽出來一次：

- **`State`** — 一個階段。它從 mission 讀無人機當前狀態，回傳這一幀要的高階 setpoint：
  `(target_pos, yaw)`。內建：`Takeoff`、`Hover`、`GoTo`、`Land`、`Failsafe`。
- **`Mission`** — 執行器：擁有環境 + 控制器 + 那一份共用 while 迴圈，依序跑你給的狀態清單，
  並**每一幀盯著地理圍欄（geofence）**（6×6 公尺、0.3–2.5 公尺高）。只要某個階段想離開安全框，
  或你自己呼叫 `request_failsafe(...)`（例如失聯），它就把一切丟進 `Failsafe` —— 先穩住、再降落 ——
  不管原本計畫想做什麼。

雙層架構依然成立：`State` 永遠只產生 setpoint；`DSLPIDControl`（韌體）把它變成馬達轉速。
**狀態永遠不碰馬達。** 注意執行器雖然索引 `obs[0]`，但沒把 `num_drones=1` 寫死進迴圈本體 —— 留了未來擴充空間。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/11_mission/mission_demo.py            # GUI：起飛→飛點→懸停→降落
python lessons/11_mission/mission_demo.py --headless  # 同上，不開視窗
python lessons/11_mission/mission_demo.py --selftest   # 腳本化驗收（CI）
```

請讀 [`mission_demo.py`](mission_demo.py)（如何用 states 組一個任務），
再看 [`nanodrone/mission.py`](../../nanodrone/mission.py) —— 每個 `State` 都只有幾行，
而 `Mission.run()` 迴圈就是每一課以前都在抄的心跳：**感知 → 決策 → 動作 → 轉移。**

## 驗收 ✅

`--selftest` 跑兩段 headless 檢查並印出（本機實測）：

```
MISSION OK: ran 4 states [Takeoff>GoTo>Hover>Land], moved 1.04 m, landed at z=0.40
FAILSAFE OK: geofence breach -> Hover -> Land, ended safe (z=0.39)
```

第一段確認整個計畫能跑、會移動、會降落；第二段確認「越界目標」會觸發 `Failsafe`，
且無人機仍安全落地。

## 延伸

- 把 `Mission.run()` 迴圈和 ROS 2 行為樹 / PX4 commander 對照 —— 同一套狀態機可遷移到真實飛控。
- 加一個 `Turn` 狀態，或給 `GoTo` 加上速度上限。
- **下一課：** Lesson 12 用**語音**驅動這些轉移 —— 同一套狀態機，改由說出的命令決定下一個階段。
