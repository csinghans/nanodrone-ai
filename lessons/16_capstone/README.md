# Lesson 16 — Graduation project: design your own mission

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Design your own mission from every block you've built, fly it in sim, and grade it against a rubric — your graduation project. · **Builds on:** L11, L12, L13, L14a, L14b

## Why

Every lesson so far handed you the task. The capstone flips it: **you** design a
mission from the blocks you built, and grade it against a rubric. This is the end
of the $0, sim-first journey — and the bridge to real hardware. It's also where
the course's arc closes: Lessons 1–10 were about *building* capabilities (and the
signature move, *training your own small model*); Lessons 11–16 were about
*composing* them on one state machine. Your capstone is the proof you can do both.

## Concept

Two files:

- **`template_mission.py`** — a minimal, valid mission to copy and grow: take off,
  fly a little patrol, come home, land. It already obeys every course rule (`$0`,
  `--selftest` that asserts, a built-in Failsafe), so you start from green.
- **`validate_mission.py`** — checks the *structure* of any mission (yours or the
  template) against the rubric's hard gates: starts with `Takeoff`, ends with
  `Land`, every phase is **guarded** (overrides `is_done`, so the mission can
  actually advance), a Failsafe is wired in, and its `--selftest` is green.

To make it *your* capstone, combine **at least three** capabilities — voice
transitions (Lesson 12), find/follow (Lesson 13), mapping (Lesson 14a) — and, for
any learned model, show it fits GAP8 (Lesson 14b). See [`RUBRIC.md`](RUBRIC.md).

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/16_capstone/template_mission.py            # GUI: fly the template
python lessons/16_capstone/template_mission.py --selftest  # asserts (CI)
python lessons/16_capstone/validate_mission.py             # grade the structure
```

Copy `template_mission.py`, redesign `build_plan()` into your mission, keep its
`--selftest` meaningful, then point `validate_mission.py` at your `build_plan` and
grade with `RUBRIC.md`.

## Checkpoint ✅

```
CAPSTONE-DEMO OK: ran 6 states [Takeoff>GoTo>GoTo>Hover>GoTo>Land], returned home, landed at z=0.40
CAPSTONE OK: graph valid (6 states, 5 transitions), has Takeoff+Land+Failsafe, all transitions guarded, selftest green
```

Your own capstone must clear the same two checks — and the rubric's hard gates —
before you grade the scored dimensions.

## Going further

- Take it to real hardware (Lesson 4 Crazyflie, or a Tello) — only the controller
  behind the protocol changes; verify in sim first, always.
- Record a GIF of your mission and add it to your README (10 rubric pts).
- Share it — a well-built capstone is the best thing to show for the course.

---

<a name="中文"></a>
# Lesson 16 — 畢業專題：設計你自己的任務

🌐 [English](#lesson-16--graduation-project-design-your-own-mission) · **繁體中文**（以下）

> **一句話：**用你蓋好的所有積木自己設計一趟任務，在模擬裡飛完並照評分表打分——這是你的畢業專題。 · **建立在：**第 11 課、第 12 課、第 13 課、第 14a 課、第 14b 課

## 為什麼

到目前為止每一課都把題目給你。畢業專題反過來：**你**用做出來的積木設計一個任務，並按評分標準自評。
這是 $0、sim-first 旅程的終點 —— 也是通往真機的橋。它也讓整門課的弧線收束：Lesson 1–10 在「**打造**能力」
（以及招牌動作：**訓練你自己的小模型**）；Lesson 11–16 在同一台狀態機上「**組合**它們」。
你的畢業作品就是你兩者都會的證明。

## 概念

兩個檔案：

- **`template_mission.py`** —— 一個最小、合法、可複製擴充的任務：起飛、飛一小段巡邏、返航、降落。
  它已遵守每一條課程規則（`$0`、會 assert 的 `--selftest`、內建 Failsafe），所以你從綠燈開始。
- **`validate_mission.py`** —— 檢查任何任務（你的或範本）的*結構*是否符合評分標準的硬性門檻：
  以 `Takeoff` 開始、`Land` 結束、每個階段都**有把關**（覆寫 `is_done`，任務才推得動）、有接上 Failsafe，
  且它的 `--selftest` 是綠燈。

要做成*你的*畢業專題，結合**至少三種**能力 —— 語音轉移(Lesson 12)、找人跟隨(Lesson 13)、建圖(Lesson 14a) ——
並且若用到學習模型，要展現它塞得進 GAP8(Lesson 14b)。見 [`RUBRIC.md`](RUBRIC.md)。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/16_capstone/template_mission.py            # GUI：飛範本任務
python lessons/16_capstone/template_mission.py --selftest  # 驗收（CI）
python lessons/16_capstone/validate_mission.py             # 檢查結構評分
```

複製 `template_mission.py`，把 `build_plan()` 重新設計成你的任務，讓它的 `--selftest` 有意義，
再把 `validate_mission.py` 指向你的 `build_plan` 並用 `RUBRIC.md` 評分。

## 驗收 ✅

```
CAPSTONE-DEMO OK: ran 6 states [Takeoff>GoTo>GoTo>Hover>GoTo>Land], returned home, landed at z=0.40
CAPSTONE OK: graph valid (6 states, 5 transitions), has Takeoff+Land+Failsafe, all transitions guarded, selftest green
```

你自己的畢業作品也要先過這兩項檢查 —— 以及評分標準的硬性門檻 —— 才進入計分維度。

## 延伸

- 搬上真機（Lesson 4 的 Crazyflie，或一台 Tello）—— 只有協定背後的 controller 要換；永遠先在模擬驗證。
- 錄一段你任務的 GIF 放進 README（評分 10 分）。
- 分享出去 —— 一個做得好的畢業作品，是這門課最好的成果展示。
