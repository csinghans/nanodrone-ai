# Lesson 12 — Voice-driven mission transitions

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Wire your voice into the mission brain so saying 'take off' or 'land' switches the whole flight phase, not just a small nudge. · **Builds on:** L11, L9, L10

## Why

Lessons 9 and 10 turned speech into a *continuous nudge* — "forward" meant
"drift forward while I hold it." Real missions need spoken commands that switch
the **whole phase**: "take off", "hover", "land". This lesson feeds a voice
source into the Lesson 11 state machine, so a word triggers a **transition**,
not a drift. It's the smallest possible "command → phase" integration, and it
introduces an idea the rest of the course leans on: the command front-end is
swappable.

## Concept

The new piece is an **adapter layer**, `nanodrone/mission_events.py`. A keyboard,
a Lesson 9 mic, a Lesson 10 KWS model, and later the DroneVoice app are all just
different ways to produce the same small **event vocabulary** — `takeoff`,
`hover`, `land`. Each source has a different raw output, so each gets a tiny
adapter; the mission only learns one mapping (`default_event_map`).

- **`phrase_to_event(text)`** — maps a spoken/typed phrase (English or 中文) to an
  event. Note it maps at the *keyword* level, because Lesson 9's `parse_command`
  collapses takeoff / stop / hover into the same zero nudge — useless for a phase
  machine that must tell them apart.
- **`kws_to_event(label, conf)`** — maps a Lesson 10 KWS label; `background` /
  low-confidence → `None`, so silence never flips a phase (Lesson 10's "when
  unsure, do nothing" rule).
- The mission gains `Mission.go(state)` — jump to a state *now*, driven by an
  event instead of the plan. Between events the drone idle-holds; a `land` event
  ends the run.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/12_voice_mission/voice_mission.py            # mic (needs the Lesson 9 Vosk model)
python lessons/12_voice_mission/voice_mission.py --lang zh   # speak 中文
python lessons/12_voice_mission/voice_mission.py --selftest  # scripted events, no mic (CI)
```

Read [`voice_mission.py`](voice_mission.py) (how the event source plugs into
`Mission.run(event_source=...)`) and
[`nanodrone/mission_events.py`](../../nanodrone/mission_events.py) — the adapters
are a few lines each. Live mode reuses Lesson 9's offline Vosk listener.

## Checkpoint ✅

`--selftest` injects a scripted sequence of spoken phrases (no mic), including
one piece of noise, and prints (measured locally):

```
VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed (z=0.40), 1 noise-event rejected
```

It asserts three phase transitions fired, the run ended in `Land` on the ground,
**and** the lone unknown phrase ("banana milkshake") was rejected — not acted on.

## Going further

- Add a `follow` event and a `Follow` state — that's the seed of Lesson 13.
- Wire `KwsEventSource` to your Lesson 10 model and fly by your own voice.
- The DroneVoice app's JSON is just another member of this event family — same
  `default_event_map`, different transport.

---

<a name="中文"></a>
# Lesson 12 — 語音驅動的任務轉移

🌐 [English](#lesson-12--voice-driven-mission-transitions) · **繁體中文**（以下）

> **一句話：**把語音接上任務大腦：說一聲『起飛』『降落』就切換整個飛行階段，而不只是輕推一下。 · **建立在：**第 11 課、第 9 課、第 10 課

## 為什麼

Lesson 9、10 把語音變成**持續的微調** ——「前進」意思是「我一直喊它就一直往前飄」。
真實任務需要的是切換**整個階段**的口語命令：「起飛」「懸停」「降落」。這一課把語音來源接進
Lesson 11 的狀態機，讓一個詞觸發一次**轉移**，而不是一直漂。這是最小的「命令 → 階段」整合，
也帶出整門課後面都倚賴的觀念：命令前端是可抽換的。

## 概念

新東西是一層 **adapter（轉接層）**，`nanodrone/mission_events.py`。鍵盤、Lesson 9 麥克風、
Lesson 10 KWS 模型，乃至之後的 DroneVoice app，都只是產生同一套小**事件詞彙**的不同方式 ——
`takeoff`、`hover`、`land`。每個來源的原始輸出型別不同，所以各配一個小 adapter；狀態機只學一張對照表
（`default_event_map`）。

- **`phrase_to_event(text)`** —— 把口語/打字的句子（英文或中文）映成事件。注意它在*關鍵字*層映射，
  因為 Lesson 9 的 `parse_command` 把 takeoff／stop／hover 收斂成同一個零微調 —— 對「必須區分階段」的
  狀態機沒用。
- **`kws_to_event(label, conf)`** —— 映 Lesson 10 的 KWS 標籤；`background`／低信心 → `None`，
  所以靜音永遠不會切階段（Lesson 10 的「不確定就不動作」原則）。
- 狀態機新增 `Mission.go(state)` —— 由事件（而非計畫）**立刻**跳到某個狀態。事件之間無人機原地待命；
  收到 `land` 事件就結束。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/12_voice_mission/voice_mission.py            # 麥克風（需 Lesson 9 的 Vosk 模型）
python lessons/12_voice_mission/voice_mission.py --lang zh   # 講中文
python lessons/12_voice_mission/voice_mission.py --selftest  # 腳本化事件、不用麥克風（CI）
```

請讀 [`voice_mission.py`](voice_mission.py)（事件來源如何接進 `Mission.run(event_source=...)`）與
[`nanodrone/mission_events.py`](../../nanodrone/mission_events.py) —— 每個 adapter 都只有幾行。
Live 模式沿用 Lesson 9 的離線 Vosk 聽寫。

## 驗收 ✅

`--selftest` 注入一段腳本化的口語序列（不用麥克風），其中故意夾一段雜訊，印出（本機實測）：

```
VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed (z=0.40), 1 noise-event rejected
```

它驗證三次階段轉移有發生、任務在地面以 `Land` 結束，**而且**那段不認得的句子（"banana milkshake"）
被拒絕、沒有被執行。

## 延伸

- 加一個 `follow` 事件與 `Follow` 狀態 —— 那就是 Lesson 13 的種子。
- 把 `KwsEventSource` 接到你 Lesson 10 訓練的模型，用你自己的聲音飛。
- DroneVoice app 的 JSON 只是這個事件家族的另一個成員 —— 同一張 `default_event_map`，不同傳輸層。
