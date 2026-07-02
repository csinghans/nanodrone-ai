# Lesson 30 — Course summary: what you built, by the numbers

🌐 **English** (below) · [跳到繁體中文](#中文)

---

> **In one line:** Step back and tally the whole journey — what you built, what the measurements say, and what honestly remains to be done. · **Builds on:** —

## Why

Thirty lessons ago the goal fit in one sentence: **a 27 g drone that flies
itself, offline, on a 512 KB chip — starting from $0 in a simulator.** This
lesson is the look back: what you actually built, what the measurements say,
and what honestly remains. A summary in this course has to play by the
course's own rule — claims come with numbers, and the load-bearing pieces get
re-asserted, not just remembered.

## Concept — the arc, in five tracks

- **Foundations (L0–L10).** Hover, see, decide: a PID two-layer split (your AI
  never drives motors — it sends setpoints, the flight controller keeps the
  aircraft alive), a first perception net, a first learned behaviour, voice in
  two languages. The signature move appears in Lesson 3 and never leaves:
  *the simulator hands you labels for free, so you train your own tiny model.*
- **Track A — orchestration (L11–L16).** Missions as guarded state machines,
  voice-driven plans, find-follow-land — capped by a capstone with a rubric
  and a validator that *flies* your graph before it grades it.
- **Track B — on-device depth (L14b, L17–L22, L29).** Depth, optical flow,
  multi-obstacle RL, domain randomization, distillation — everything squeezed
  toward int8 under 512 KB — capped by the nano world model: latent prediction
  (never pixels), a vision-only latent MPC, and closed-loop numbers.
- **Track C — DroneVoice.** The Apple app speaking the same 13-action JSON
  protocol as the sim, a Tello, and a Crazyflie — one contract, no drift.
- **Track E — sim-to-real groundwork (L23–L26).** Telemetry black box, a $100
  Tello stepping stone, gap measurement, field SOP + regulations. The real
  hardware is a *deliberate* next step, not a skipped one.

(No Track D here: in the ROADMAP it is the docs-only "going further" shelf —
swarm, Kalman tracking — signposts rather than lessons; its domain-randomization
idea was promoted into Lesson 20.)

Two themes carried the whole way: **on-board honesty** (if it will not fit in
512 KB int8 with its activations, it does not ship) and **measure, don't
claim** (every script prints an `XXX OK` line and asserts it; every limit —
FOV blind sides, planar labels, sim-only optics — is stated where it bites).

## What the crown lesson measured

Lesson 29 closed the loop the whole course pointed at. Its scoreboard, all
measured on 100+ seeded courses:

| claim | number |
|---|---|
| the model can *choose*, not just detect | veer-ranking **1.00** (chance 0.5) |
| anticipation vs reaction, at speed (hand MPC) | crash **0–10 % vs 40–60 %** (1.4–1.6 m/s) |
| the crown: a policy *learned* over the same model | crash **0 %** — the whole 0.8–1.6 m/s sweep *and* the cluttered courses |
| clearance at speed | **2–3×** the reactive baseline's |
| false evasions on safe courses | **0 %** |
| the whole stack on a GAP8 | **137.3 KB < 512 KB**, ~8 ms/decision |
| the sim-to-real gap, priced then bought back | AUC 0.96 → 0.82 → **0.92** |
| the hand MPC's honest tail (FOV blind side, cluttered) | **16 %** — erased to **0 %** by the learned policy's memory (step 6) |

And the meta-result step 6 acted on: after eight measured planner
configurations, the *model* stopped being the bottleneck — the hand-written
cost function was. So the policy was *learned* instead (PPO over the world
model's outputs, with a one-second observation memory): the hand planner's
cluttered-course tail — 16 % on the 100-seed scoreboard, 17 % on step 6's
60-course rerun — went to **0 %**, and the learned policy flew the entire
0.8–1.6 m/s sweep — 150 courses — **without a single crash**, where reaction
ends at 60 % on the sweep (70 % on the single-pillar rerun at 1.6 m/s).
Sixteen minutes of training against eight rounds of hand-tuning.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/30_summary/course_check.py
```

One script, three shared contracts re-asserted end to end: the 13-action
protocol (+ machine-readable schema), the safety layer's full failsafe truth
table, and the mission graph — validated *and flown headless* by Lesson 16's
own validator. With PyTorch present it also reloads Lesson 29's world model
and re-checks the on-board budget; without it, the contracts still pass
(they are torch-free by design, which is why this runs in the torch-free CI).

## Checkpoint ✅

```
COURSE OK: protocol 13 actions + schema | safety 4/4 failsafe verdicts + geofence | mission graph 6 states (flown + validated) | world model reloads, on-board budget 137.3 KB < 512 KB
```

If that line prints, the course's spine still holds: one command contract,
one safety layer, one mission pattern, one on-board budget — the four things
every later lesson trusted.

## Going further — where this goes next

- **Push the learned policy further (L29 step 6).** The stacked-memory PPO
  beats every other policy everywhere measured (0 % across the sweep and the
  cluttered courses). The recurrent variant got its fair budget, then an
  edge-biased data diet: the speed extreme closed (40 % → 3 %) but the
  cluttered tail reopened (2 % → 10 %) — every re-weighting moves the hole.
  The open follow-up is one memory that holds the whole envelope, or a
  model-side GRU.
- **Cross the sim-to-real bridge (Track E).** The Crazyflie + AI-deck path is
  prepared, deliberately unspent: domain randomization priced the modelled
  gap; the unmodelled one is measured on hardware, with Lesson 26's SOP.
- **The research edge.** Metric-ground the latent with offline 4D-GS; that is
  an ICRA-flavoured contribution waiting on the foundation you now have.
- **Fork it.** The course's real deliverable is the method: labels from the
  sim, nano models of your own, a selftest for every claim, and limits stated
  out loud. Point it at your own robot.

---

<a name="中文"></a>
# Lesson 30 — 課程總結：你蓋出了什麼，數字說話

🌐 [English](#lesson-30--course-summary-what-you-built-by-the-numbers) · **繁體中文**（以下）

> **一句話：**回頭盤點整趟旅程：你做出了哪些東西、數據怎麼說，以及還有哪些事老實說沒做完。 · **建立在：**無（從這裡開始）

## 為什麼

三十課之前，目標只有一句話：**一台 27 克、離線、在 512 KB 晶片上自己飛的無人機——從 $0 的
模擬器出發。**這一課是回望：你真正蓋出了什麼、量測數字怎麼說、還有哪些誠實的未竟之事。
總結也得守這門課自己的規矩——主張要附數字，承重的部分要重新驗證，不能只是憑記憶。

## 概念——五條軌道的弧線

- **基礎（L0–L10）。**懸停、看見、決策：PID 兩層架構（你的 AI 永遠不直接驅動馬達——它送
  setpoint，飛控保住飛機）、第一個感知網路、第一個學出來的行為、雙語語音。招牌動作在
  Lesson 3 登場後再也沒離開：*模擬器免費把標籤交給你，所以你訓練自己的小模型。*
- **Track A——任務編排（L11–L16）。**把任務寫成有守衛的狀態機、語音驅動的計畫、
  find-follow-land——以一個帶評分表的 capstone 收尾，它的 validator 會先*實飛*你的
  狀態圖再打分。
- **Track B——板載感知深化（L14b、L17–L22、L29）。**深度、光流、多障礙 RL、域隨機化、
  蒸餾——一切往 512 KB int8 裡壓——由 nano 世界模型收官：隱空間預測（絕不生成像素）、
  純視覺 latent MPC、閉環數字。
- **Track C——DroneVoice。**Apple app 與模擬器、Tello、Crazyflie 說同一份 13 動作 JSON
  協議——一份合約，不漂移。
- **Track E——sim-to-real 打底（L23–L26）。**飛行黑盒子、$100 的 Tello 踏腳石、gap 量測、
  外場 SOP 與法規。真機是*刻意保留*的下一步，不是被跳過的一步。

（這裡沒有 Track D：它在 ROADMAP 裡是純文件的「延伸指路」書架——swarm、卡爾曼追蹤——
只指路、不成課；其中的域隨機化後來升格為第 20 課。）

兩個主題貫穿全程：**板載誠實**（連 activation 一起算、塞不進 512 KB int8 的東西不出貨）
與**量測而非宣稱**（每支腳本印一行 `XXX OK` 並 assert；每個極限——FOV 盲側、平面標籤、
模擬光學——都寫在它咬人的地方）。

## 皇冠課量到了什麼

Lesson 29 把整門課指向的迴路閉上了。它的記分板，全部在 100+ 條 seeded 航道上實測：

| 主張 | 數字 |
|---|---|
| 模型會「選」，不只會「偵測」 | veer-ranking **1.00**（隨機 0.5） |
| 高速下，預判 vs 反應（手工 MPC） | 墜機 **0–10% vs 40–60%**（1.4–1.6 m/s） |
| 皇冠：在同一個模型上*學出來*的策略 | 墜機 **0%**——0.8–1.6 m/s 整條掃描帶*與*雜訊航道 |
| 高速下的淨空 | 反應式基線的 **2–3 倍** |
| 安全航道上的誤閃避 | **0%** |
| 整套堆疊上 GAP8 | **137.3 KB < 512 KB**，每次決策 ~8 ms |
| sim-to-real gap：標價，然後買回 | AUC 0.96 → 0.82 → **0.92** |
| 手工 MPC 的誠實尾巴（FOV 盲側、雜訊航道） | **16%**——被 step 6 學出的記憶抹到 **0%** |

還有 step 6 已經回應的後設結論：量測了八種 planner 配置之後，*模型*不再是瓶頸——手寫的
cost 函數才是。所以策略改用**學的**（PPO 讀世界模型的輸出、帶一秒的觀測記憶）：手工 planner
的雜訊尾巴——100 seed 記分板 16%、step 6 的 60 條重跑 17%——歸 **0%**，而學出來的策略把
0.8–1.6 m/s 整條掃描帶——150 條航道——**一次都沒撞**地飛完，反應式在掃描帶尾端墜 60%
（1.6 m/s 單柱重跑 70%）。十六分鐘的訓練，對上八輪的手調。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/30_summary/course_check.py
```

一支腳本，把三份共用合約端到端重新驗證：13 動作協議（含機器可讀 schema）、安全層的完整
failsafe 真值表、任務狀態圖——用 Lesson 16 自己的 validator 驗證*並且無頭實飛*。裝了
PyTorch 的話，它還會重新載入 Lesson 29 的世界模型、重算板載預算；沒裝也照樣全綠
（合約層刻意 torch-free，這正是它能跑在無 torch CI 裡的原因）。

## 驗收 ✅

```
COURSE OK: protocol 13 actions + schema | safety 4/4 failsafe verdicts + geofence | mission graph 6 states (flown + validated) | world model reloads, on-board budget 137.3 KB < 512 KB
```

這行印得出來，課程的脊椎就還立著：一份指令合約、一層安全、一種任務寫法、一條板載預算
——後面每一課信任的四件事。

## 延伸——接下來往哪走

- **把學出來的策略推得更遠（L29 step 6）。**堆疊記憶的 PPO 在所有量測項目上勝過所有其他
  策略（掃描帶與雜訊航道全 0%）。recurrent 變體先拿到公平預算、再拿到邊緣過採樣的資料
  配方：速度極端關上了（40% → 3%），雜訊尾巴卻重新打開（2% → 10%）——每次重加權都只是
  把洞搬家。留給你的後續，是一個撐得住整個包絡的記憶，或模型側的 GRU。
- **跨過 sim-to-real 的橋（Track E）。**Crazyflie + AI-deck 的路已鋪好、刻意還沒花掉：
  域隨機化為「模擬得出來的 gap」標了價；模擬不出來的那部分，拿 Lesson 26 的 SOP 上真機量。
- **研究前沿。**用離線 4D-GS 把隱空間度量接地——一個等著你動手的 ICRA 級題目，而地基
  你已經有了。
- **Fork 它。**這門課真正的交付物是方法：標籤來自模擬器、nano 模型自己訓、每個主張配一個
  selftest、每個極限大聲說。把它指向你自己的機器人。
