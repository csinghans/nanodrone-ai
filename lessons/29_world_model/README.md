# Lesson 29 — Nano world model: latent-space prediction for proactive avoidance

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Every model so far has been *reactive*: the depth net (Lesson 17) and the RL
policy (Lesson 19) both answer "what should I do about the obstacle that is close
**now**?" But at speed, "now" is already too late — by the time a pillar fills the
frame, a 27 g drone with bounded acceleration cannot turn hard enough to miss it.

A **world model** buys you the missing ingredient: *anticipation*. It learns how
the world will change — and how it changes *because of what you do* — so the
drone can act on what is **about to** happen. This is the frontier the course has
been pointing at; it is the same problem self-driving research attacks with world
models.

The trap is to build it by predicting the **next image** (diffusion / pixel
generation). That is slow and it hallucinates detail a controller can't use. We
take the **V-JEPA** route instead — *predict the next latent embedding, never the
next pixels*. No hallucinated frames, no diffusion latency, a fixed compute cost.

And the signature move returns, at the frontier this time: the real V-JEPA is a
billion-parameter model that needs an Orin-class GPU — it will **never** fit on a
GAP8. So you don't download it; you **train your own nano version** under the
512 KB int8 budget — and then you **close the loop**: a tiny latent MPC flies
from the camera alone and dodges ~700 ms before a reactive controller does.

## Concept

Four tiny networks, reusing the course's conv stack, all int8-able:

- **Encoder** `f_θ`: image → a 64-d latent `z`. Lesson 3's `TinyDronet` conv
  stack — but its global average pool is swapped for a **bearing-aware pooling**
  (four horizontal strips + a small projection). Global pooling averages *where*
  away: it can say "pillar close", never "pillar on the left" — and dodging
  left-vs-right is precisely a "which side" question. (Measured below: with
  global pooling the veer-ranking check sits at chance no matter how it is
  supervised; with strips it reaches 1.00.)
- **Predictor** `g_φ`: `(z_t, action) → ẑ_{t+k}` at **four horizons**
  `k ∈ {4, 8, 16, 32}` steps (~83 / 167 / 333 / 667 ms at 48 Hz) — one shared
  trunk, one tiny residual head per horizon (`ẑ = z_t + Δ_k`, so "nothing
  changes" is the free baseline). "Proactive" is a claim about *time*: a
  controller that reacts ~700 ms early needs a model that predicts ~700 ms
  ahead, not one fixed 167 ms hop.
- **Collision heads**: `ẑ_k → P(too close within k steps)`, one per horizon —
  the *anticipation* signal.
- **Danger-now head**: `z_t → P(too close right now)` — the *reactive* signal,
  kept on purpose: it is the honest baseline the anticipation must beat with
  the sensor held equal.

The trick that makes latent prediction work without a pixel loss (and without
collapsing to a constant) is a **target encoder**: an EMA copy of `f_θ` with a
stop-gradient, à la V-JEPA / BYOL, plus a VICReg-style variance guard:

```
Σ_k ‖ g_φ(f_θ(x_t), a_t)_k − sg(f_EMA(x_{t+k})) ‖²  +  variance-guard  +  danger BCEs
```

**The dataset is an experiment, not footage.** Each rollout resets the sim
(fresh trial), cruises forward, then flies a chain of **held segments**: every
~1 s a random high-level command — forward / slow / veer_left / veer_right /
climb / hover — held long enough to cover the longest horizon. We record the
**commanded setpoint**, not the measured velocity: a controller can only feed
the model a command, so that is what it must condition on. Labels stay free
(the simulator's signature move) and go further: a **counterfactual oracle**
labels *every* frame × candidate × horizon by rolling the command forward
kinematically through the known pillar layout. Executed rollouts teach "what
happened"; a planner needs "what would happen if". One honesty rule: a positive
label caused by a pillar **outside the camera's 60° FOV** is unanswerable from
a single frame, so it is masked out of both training and grading.

**What it took to close the loop (all measured on this repo):** the first
version had collision AUC 0.9 — and ranked "veer left vs veer right" at
chance. AUC is a *distance* question; planning is a *choice* question. Fixing
the choice took, in order: intervention segments (counterfactual contrasts),
the counterfactual oracle (dense ranking supervision), FOV masking (37 of 45
failing probe frames had the threat at 66–84° bearing — invisible), and
finally the bearing-aware pooling above (the root cause). The lesson: **a high
AUC does not mean a model can rank actions — test the decision, not the
detection.** That test ships here as the `veer-ranking` metric: on held-out
frames where geometry says one veer is truly safer, does the model rank it
safer? Chance is 0.5; this model measures 1.00 (n=34).

**Why latent (V-JEPA), not explicit 4D geometry (4D-GS)?** Both are world models;
they sit at opposite ends of the trade-off.

| | **V-JEPA (this lesson)** | **4D Gaussian Splatting** |
|---|---|---|
| Represents | an implicit *latent* manifold | explicit metric 3D + time geometry |
| Predicts | the future *embedding* | renders the future *scene* |
| Strength | anticipation, abstraction, **bounded latency** | metric precision, photorealism |
| Cost | fixed FLOPs, **distils to int8 < 512 KB** | scales with #Gaussians → Orin-class |
| Hallucination | none (no pixels committed) | geometric "floaters" when extrapolating |

4D-GS is the heavyweight explicit-geometry cousin of the **2D occupancy grid you
built in Lesson 14a** — extended to 3D and time. It is wonderful for metric
precision but it does not fit on a GAP8. V-JEPA is the latent path that does,
which is why it is our on-board backbone.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/29_world_model/gen_wm_dataset.py --rollouts 64    # 1. intervention trials
python lessons/29_world_model/train_world_model.py --epochs 80   # 2. train the nano V-JEPA
python lessons/29_world_model/proactive_avoid.py                 # 3. the timing schematic
python lessons/29_world_model/wm_closed_loop.py                  # 4. closed loop from vision
python lessons/29_world_model/eval_world_model_policy.py         # 4b. the 100-seed scoreboard
```

Step 3 (`proactive_avoid.py`) isolates decision *timing* with privileged
geometry — a schematic. Step 4 removes the crutch: the danger signal in the
control loop comes from the **camera alone** (encoder → predictor → collision
heads), while pillar positions only stage the course and score the flight. The
planner is a tiny **latent MPC** at 12 Hz: encode the frame *once*, imagine
every candidate command through the small MLPs (the expensive encoder is
shared, so on a GAP8 the whole deliberation is nearly free), pick the cheapest
future under `6·danger + heading + 0.5·switch − 1.5·progress`. The reactive
baseline gets the same encoder — and, deliberately, a *privileged* evasion
direction. It can only lose on timing, so the comparison isolates anticipation.

Each script self-generates what it needs and runs on its own with `--selftest`.

## Checkpoint ✅

Step 1 (measured locally, full run):

```
WM-DATA OK: 64 rollouts x 120 steps @ 48 Hz, 89 held intervention segments, labels [k=4: n=7070 pos=0.19, k=8: n=6468 pos=0.20, k=16: n=5268 pos=0.23, k=32: n=2982 pos=0.31], saved .../output/wm_dataset.npz
```

Step 2 asserts the predictor beats "future == present", per-horizon AUC, the
danger-now head, **and the veer ranking** — the number that says the model can
choose, not just detect (rollout-level split, so nothing leaks):

```
WORLD-MODEL OK: 2408 train seqs, latent MSE@32=0.587 (no-op 3.745), AUC@4/8/16/32=0.98/0.98/0.98/0.99, now-AUC=0.91, veer-ranking=1.00 (n=34), int8 weights=81.0 KB (<512 fits), saved .../output/world_model.pth
```

Step 4 flies the same course twice from vision alone and asserts the earlier
trigger, the clearance gain, no crash, goal reached — no privileged look-ahead
anywhere in control:

```
WM-CLOSED-LOOP OK: reactive min-clear=0.35 m (trigger@64), wm min-clear=0.43 m (trigger@28), lead=+36 steps (~750 ms earlier), crashes reactive/wm = 0/0, goal steps = 187/199 — danger signal from camera alone (no privileged look-ahead in control)
```

Step 4b is the honest scoreboard — 100 random courses (70 threatened, 30 clear
for false-positive probing) plus the on-board bill an embedded engineer asks
for (weights are not the whole story: activations and DMA workspace share the
same 512 KB):

```
WORLD-POLICY OK: seeds=100 (70 in-path / 30 clear)
  crash_rate:        reactive 0% -> wm 0%
  mean_min_clearance: 0.40 m -> 0.50 m
  mean_trigger_lead: +725 ms (n=70 both triggered)
  false_positive:    reactive 0% -> wm 0% of clear runs
  goal_time:         wm +8% vs reactive (n=69 clean)
  decision latency:  0.4 ms measured (this CPU) | ~8 ms est @ GAP8 0.5 GMAC/s (3.9 M MACs, encoder shared across 6 candidates)
ONBOARD-BUDGET OK: weights=81.0 KB + peak_activation=28.0 KB + workspace(dbl-buf)=28.0 KB = 137.0 KB < 512 KB
```

Read the numbers like a robot person: anticipation buys **+25 % clearance** and
a **+725 ms** head start at an **+8 %** time cost, with **zero** false evasions
on safe courses — and the whole stack fits the GAP8 budget almost 4× over. At
this cruise speed (0.8 m/s) the generously-handicapped reactive baseline also
stays crash-free: the world model's win here is *margin and time*, which is
exactly what turns into crashes-avoided as speed rises (see *Going further*).

## Going further

- **Raise the speed until reaction breaks.** Both controllers fly 0.8 m/s here.
  Sweep the cruise speed upward and the reactive baseline starts clipping
  pillars while the anticipating MPC keeps its margin — that sweep turns the
  clearance gap into a crash-rate gap.
- **Give the model memory.** Fixed-yaw translation leaves side threats outside
  the 60° FOV (this lesson honestly masks those labels as unanswerable). A tiny
  GRU over `z_t`, or yaw-aligned flight, would let the drone *remember* the
  pillar it just saw — the next real step toward cluttered courses.
- **Metric-ground the latent (research-grade).** Use **4D-GS offline** to
  produce geometry-consistent occupancy and add a geometry-grounded
  latent-prediction loss, so `ẑ_{t+k}` decodes to a collision-checkable
  distance — V-JEPA's latency with 4D-GS's grounding.
- **Feed it to the policy.** Add the predicted per-horizon danger to Lesson
  19's RL observation — a learned proactive avoider instead of a hand-coded
  cost function.
- **Honest gaps.** The counterfactual oracle exists because sim labels are
  privileged anyway; with real-world data you are back to executed-action
  supervision and need far more of it. The danger labels are planar (visual-only
  pillars), which is also why `climb` sits in the model's vocabulary but off the
  planner's menu. And this is a *nano distillation* of the V-JEPA idea — the
  real V-JEPA 2 is Orin-class; here we teach the principle under the GAP8
  budget, then domain-randomize (Track B, L20) before any sim-to-real claim.

---

<a name="中文"></a>
# Lesson 29 — nano 世界模型：隱空間預測做預判式避障

🌐 [English](#lesson-29--nano-world-model-latent-space-prediction-for-proactive-avoidance) · **繁體中文**（以下）

## 為什麼

目前為止每個模型都是**反應式**的：深度網路（Lesson 17）與 RL 策略（Lesson 19）回答的都是
「對**現在**已經很近的障礙我該怎麼辦？」但在高速下，「現在」已經太遲——等柱子塞滿畫面，
一台加速度有上限的 27 克無人機根本轉不過來。

**世界模型**補上缺的那一塊：**預判（anticipation）**。它學會世界將如何變化——以及世界會
**因為你的動作**而如何變化——讓無人機對**即將**發生的事先動作。這正是本課一路指向的前沿，
也是自駕研究用世界模型攻堅的同一個問題。

陷阱是用「預測下一張影像」（擴散／像素生成）來做，那既慢又會幻想出控制器根本用不到的細節。
我們改走 **V-JEPA** 路線——**預測下一個隱空間 embedding，而不是下一格像素**。沒有幻覺影格、
沒有擴散延遲、算力固定。

而招牌動作在前沿再現一次：真正的 V-JEPA 是十億參數、需要 Orin 級 GPU 的大模型，**永遠**塞不進
GAP8。所以你不是下載它，而是在 512KB int8 預算內**訓練你自己的 nano 版**——然後**把迴路閉起來**：
一個 tiny latent MPC 只靠相機飛行，比反應式控制器早 ~700ms 開始閃避。

## 概念

四個小網路，沿用課程既有的 conv stack，全部可 int8：

- **Encoder** `f_θ`：影像 → 64 維隱向量 `z`。用 Lesson 3 `TinyDronet` 的 conv stack——但把
  全域平均池化換成**方位感知池化**（4 條水平帶 + 一層小投影）。全域池化會把「在哪裡」平均掉：
  它說得出「柱子很近」，說不出「柱子在左邊」——而往左躲還是往右躲，正是「在哪一側」的問題。
  （下方實測：用全域池化時，不管怎麼監督，veer-ranking 都停在隨機；換帶狀池化後到 1.00。）
- **Predictor** `g_φ`：`(z_t, action) → ẑ_{t+k}`，**四個 horizon** `k ∈ {4, 8, 16, 32}` 步
  （48Hz 下約 83 / 167 / 333 / 667 ms）——一個共享 trunk，每個 horizon 一顆小殘差 head
  （`ẑ = z_t + Δ_k`，「什麼都不變」是免費基線）。「預判」是關於**時間**的宣稱：要提早 ~700ms
  反應，模型就得預測 ~700ms 遠，而不是固定一跳 167ms。
- **Collision heads**：`ẑ_k → P(k 步內太靠近)`，每個 horizon 一顆——**預判**訊號。
- **Danger-now head**：`z_t → P(現在就太靠近)`——**反應式**訊號，刻意保留：它是預判必須在
  「同一顆感測器」條件下打敗的誠實基線。

讓隱空間預測「不用像素 loss 也不塌縮」的關鍵是 **target encoder**：`f_θ` 的 EMA 複本加
stop-gradient（V-JEPA / BYOL 的做法），再加一個 VICReg 式變異數護欄：

```
Σ_k ‖ g_φ(f_θ(x_t), a_t)_k − sg(f_EMA(x_{t+k})) ‖²  +  變異數護欄  +  danger BCEs
```

**資料集是實驗，不是錄影。**每條 rollout 都重置模擬器（全新試驗）、先向前巡航，然後飛一串
**held segments**：每 ~1 秒抽一個高階指令——forward / slow / veer_left / veer_right / climb /
hover——持續到蓋滿最長 horizon。記錄的是**commanded setpoint** 而非量測速度：控制器只能餵指令
給模型，模型就必須以指令為條件。標籤照樣免費（模擬器的招牌動作）而且更進一步：一個
**counterfactual oracle** 對*每一幀 × 每個候選動作 × 每個 horizon* 都給標籤——把指令沿已知柱子
佈局做運動學前推。執行過的 rollout 教「發生了什麼」；planner 需要的是「如果做了會怎樣」。
一條誠實規則：由**相機 60° FOV 之外**的柱子造成的陽性標籤，單幀模型根本答不了，訓練與評分
一律遮罩。

**閉環的代價（全部在本 repo 實測）：**第一版 collision AUC 0.9——但「往左躲 vs 往右躲」的排序
是隨機。AUC 是*距離*問題；規劃是*選擇*問題。把選擇修好，依序花了：intervention segments
（counterfactual 對比）、counterfactual oracle（密集排序監督）、FOV 遮罩（45 個失敗 probe 幀
裡 37 個的威脅在 66–84° 方位——根本看不見）、最後是上面的方位感知池化（根因）。教訓是：
**AUC 高不代表模型會排序動作——要測決策，不是只測偵測。**這個測試以 `veer-ranking` 指標
隨課出貨：在幾何上一側明確較安全的 held-out 幀上，模型是否把較安全的那側排前面？隨機是 0.5；
本模型實測 1.00（n=34）。

**為什麼選隱空間（V-JEPA），而非顯式 4D 幾何（4D-GS）？**兩者都是世界模型，但在權衡的兩端。

| | **V-JEPA（本課）** | **4D Gaussian Splatting** |
|---|---|---|
| 表徵 | 隱式*隱空間*流形 | 顯式度量 3D + 時間幾何 |
| 預測 | 未來的*embedding* | 渲染未來的*場景* |
| 強項 | 預判、抽象、**延遲有上限** | 度量精準、擬真 |
| 成本 | 定長 FLOP、**可蒸餾成 int8 < 512KB** | 隨 Gaussian 數擴張 → Orin 級 |
| 幻覺 | 無（不 commit 像素） | 外推時出現幾何 floater |

4D-GS 是你在 **Lesson 14a 建的 2D occupancy grid** 的重量級顯式幾何表親——延伸到 3D 加時間。
它度量精準得很美，卻塞不進 GAP8。V-JEPA 是塞得進的隱空間路線，所以是我們的機上骨幹。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/29_world_model/gen_wm_dataset.py --rollouts 64    # 1. intervention 試驗
python lessons/29_world_model/train_world_model.py --epochs 80   # 2. 訓練 nano V-JEPA
python lessons/29_world_model/proactive_avoid.py                 # 3. 決策時機示意
python lessons/29_world_model/wm_closed_loop.py                  # 4. 純視覺閉環
python lessons/29_world_model/eval_world_model_policy.py         # 4b. 100-seed 記分板
```

Step 3（`proactive_avoid.py`）用 privileged 幾何隔離出決策*時機*——一張示意圖。Step 4 拆掉
柺杖：控制迴路裡的危險訊號**只來自相機**（encoder → predictor → collision heads），柱子位置
只用來佈置場景與事後評分。planner 是一個 12Hz 的 tiny **latent MPC**：每幀 encode **一次**，
用小 MLP 把每個候選指令的未來都「想」一遍（昂貴的 encoder 共用，所以在 GAP8 上整段深思幾乎
免費），以 `6·danger + heading + 0.5·switch − 1.5·progress` 挑最便宜的未來。反應式基線用同一顆
encoder——並且**刻意**拿到 privileged 的閃避方向：它只可能輸在時機上，比較因此把「預判」單獨
隔離出來。

每支腳本都自產所需資料，可用 `--selftest` 獨立執行。

## 驗收 ✅

Step 1（本機實測，完整跑）：

```
WM-DATA OK: 64 rollouts x 120 steps @ 48 Hz, 89 held intervention segments, labels [k=4: n=7070 pos=0.19, k=8: n=6468 pos=0.20, k=16: n=5268 pos=0.23, k=32: n=2982 pos=0.31], saved .../output/wm_dataset.npz
```

Step 2 驗證 predictor 贏過「未來＝現在」、各 horizon 的 AUC、danger-now head、
**以及 veer ranking**——證明模型會「選」而不只會「偵測」的那個數字（rollout 層級切分，零洩漏）：

```
WORLD-MODEL OK: 2408 train seqs, latent MSE@32=0.587 (no-op 3.745), AUC@4/8/16/32=0.98/0.98/0.98/0.99, now-AUC=0.91, veer-ranking=1.00 (n=34), int8 weights=81.0 KB (<512 fits), saved .../output/world_model.pth
```

Step 4 只靠視覺把同一條航道飛兩次，驗證更早觸發、更大淨空、不墜機、抵達終點——控制路徑中
沒有任何 privileged look-ahead：

```
WM-CLOSED-LOOP OK: reactive min-clear=0.35 m (trigger@64), wm min-clear=0.43 m (trigger@28), lead=+36 steps (~750 ms earlier), crashes reactive/wm = 0/0, goal steps = 187/199 — danger signal from camera alone (no privileged look-ahead in control)
```

Step 4b 是誠實記分板——100 條隨機航道（70 條有威脅、30 條乾淨，用來抓 false positive），
加上嵌入式工程師真正會問的機上帳單（weights 不是全部：activation 與 DMA workspace 共用同一塊
512 KB）：

```
WORLD-POLICY OK: seeds=100 (70 in-path / 30 clear)
  crash_rate:        reactive 0% -> wm 0%
  mean_min_clearance: 0.40 m -> 0.50 m
  mean_trigger_lead: +725 ms (n=70 both triggered)
  false_positive:    reactive 0% -> wm 0% of clear runs
  goal_time:         wm +8% vs reactive (n=69 clean)
  decision latency:  0.4 ms measured (this CPU) | ~8 ms est @ GAP8 0.5 GMAC/s (3.9 M MACs, encoder shared across 6 candidates)
ONBOARD-BUDGET OK: weights=81.0 KB + peak_activation=28.0 KB + workspace(dbl-buf)=28.0 KB = 137.0 KB < 512 KB
```

用機器人工程師的方式讀這些數字：預判用 **+8% 的時間成本**買到 **+25% 淨空**與 **+725ms** 的
提前量，乾淨航道上**零**誤閃避——而且整套堆疊塞進 GAP8 預算還剩近 4 倍空間。在這個巡航速度
（0.8 m/s）下，拿了 privileged 方向的反應式基線也不會墜機：世界模型在這裡贏的是**餘裕與時間**，
而那正是速度一拉高就會變成「少墜機」的東西（見*延伸*）。

## 延伸

- **把速度拉高到反應式撐不住。**這裡雙方都飛 0.8 m/s。把巡航速度往上掃，反應式基線會開始
  擦到柱子，而會預判的 MPC 保得住餘裕——那次掃描會把「淨空差」變成「墜機率差」。
- **給模型記憶。**固定 yaw 的平移會讓側面威脅留在 60° FOV 之外（本課誠實地把那些標籤遮罩為
  「答不了」）。在 `z_t` 上加一顆 tiny GRU、或改成 yaw 對齊速度的飛法，無人機就能*記得*剛看過
  的柱子——通往雜亂場景的下一步。
- **把隱空間度量接地（研究級）。**用 **4D-GS 離線**產生幾何一致的 occupancy，加一個
  geometry-grounded latent-prediction loss，讓 `ẑ_{t+k}` 能解碼成可做碰撞檢測的距離——
  V-JEPA 的延遲換到 4D-GS 的接地。
- **餵給策略。**把各 horizon 的預測危險加進 Lesson 19 的 RL 觀測——用學出來的預判避障，
  取代手寫 cost function。
- **誠實的落差。**counterfactual oracle 之所以存在，是因為模擬器標籤本來就是 privileged 的；
  換成真實資料就回到只有 executed-action 監督、而且需要多得多的資料。danger 標籤是平面的
  （柱子只有視覺體），這也是為什麼 `climb` 在模型詞彙表裡、卻不在 planner 菜單上。而這是
  V-JEPA 想法的 *nano 蒸餾版*——真正的 V-JEPA 2 是 Orin 級；這裡在 GAP8 預算下教原理，
  且任何 sim-to-real 宣稱之前要先過域隨機化（Track B 的 L20）。
