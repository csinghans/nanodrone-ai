# Lesson 19 — Harder multi-obstacle RL (perception in the observation)

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

Lesson 3's RL flew around **one** pillar in a **fixed** spot — so the drone's own
position was enough to memorize the detour (its own code comments say so). Real
avoidance is many obstacles, different every time. To generalize, the policy has
to *see* the obstacles: this randomizes 1–3 pillars per episode **and feeds the
nearest obstacle's relative position into the observation**. That's exactly the
slot where Lesson 17's learned depth would supply the obstacle cue on hardware —
perception now drives decision.

## Concept

`MultiAvoidAviary` subclasses Lesson 3's `AvoidAviary` and changes only the task:

- **random layout** — 1–3 pillars at random positions each `reset`;
- **augmented observation** — the base KIN vector **plus** the nearest pillar's
  `(dx, dy)`, so the policy can react to *this* layout instead of memorizing one;
- reward/termination use the nearest pillar.

`train_multi_rl.py` hands it to PPO. **Real RL training is a long run** (hundreds
of thousands of steps) — like Lesson 3's `train_rl`, it's a manual job, not a CI
smoke test. The `--selftest` only proves the env + augmented observation + PPO
loop are wired correctly and a rollout runs; it does **not** train a good policy.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/19_multi_avoid/train_multi_rl.py --timesteps 300000   # real training
python lessons/19_multi_avoid/train_multi_rl.py --selftest            # pipeline smoke (local)
```

Read [`multi_avoid_aviary.py`](multi_avoid_aviary.py) (the obs override is the
key idea) and [`train_multi_rl.py`](train_multi_rl.py). Needs PyTorch +
stable-baselines3, so it's verified locally, not in the torch-free CI.

## Checkpoint ✅

```
MULTI-AVOID OK: obs adds obstacle dims (72->74), trained 2000 steps, eval 0/4 reached goal (smoke — train longer for a good policy)
```

The self-test asserts the observation really carries the obstacle info (two extra
dims) and the PPO pipeline runs end to end. The `0/4` is expected after a 2k-step
smoke run — train for ~300k to get a policy that actually clears random layouts.

## Going further

- Feed Lesson 17's depth (nearest-obstacle bearing/range) as the obstacle cue
  instead of the privileged position — true on-board perception → control.
- Add a curriculum: start with 1 pillar, raise to 3 as success climbs.
- This avoidance policy is one of the teachers Lesson 22 distills into a single
  on-board network.

---

<a name="中文"></a>
# Lesson 19 — 更難的多障礙 RL（把感知併入觀測）

🌐 [English](#lesson-19--harder-multi-obstacle-rl-perception-in-the-observation) · **繁體中文**（以下）

## 為什麼

Lesson 3 的 RL 繞**一根**固定位置的柱子飛 —— 所以光靠無人機自己的位置就能背出那條繞道（它自己的註解就這麼說）。
真實避障是很多障礙、每次都不同。要泛化，policy 得*看見*障礙：這一課每回合隨機 1–3 根柱子，
**並把最近障礙的相對位置併入觀測**。那正是 Lesson 17 學到的深度在真機上提供障礙線索的位置 ——
感知開始驅動決策。

## 概念

`MultiAvoidAviary` 子類化 Lesson 3 的 `AvoidAviary`，只改任務：

- **隨機佈局** —— 每次 `reset` 在隨機位置放 1–3 根柱子；
- **擴充觀測** —— 基礎 KIN 向量**加上**最近柱子的 `(dx, dy)`，讓 policy 對*這個*佈局反應，而非背一條路；
- reward/終止用最近柱子。

`train_multi_rl.py` 把它交給 PPO。**真實 RL 訓練是長時間的跑**（數十萬步）—— 跟 Lesson 3 的 `train_rl` 一樣，
是手動工作，不是 CI 煙霧測試。`--selftest` 只證明 env + 擴充觀測 + PPO 迴圈接線正確、rollout 能跑；
它**不會**訓出好 policy。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/19_multi_avoid/train_multi_rl.py --timesteps 300000   # 真實訓練
python lessons/19_multi_avoid/train_multi_rl.py --selftest            # pipeline 煙霧（本機）
```

請讀 [`multi_avoid_aviary.py`](multi_avoid_aviary.py)（觀測覆寫是關鍵點子）與 [`train_multi_rl.py`](train_multi_rl.py)。
需要 PyTorch + stable-baselines3，所以在本機驗證，不進 torch-free 的 CI。

## 驗收 ✅

```
MULTI-AVOID OK: obs adds obstacle dims (72->74), trained 2000 steps, eval 0/4 reached goal (smoke — train longer for a good policy)
```

自我測試驗證觀測真的帶了障礙資訊（多 2 維）且 PPO pipeline 端到端能跑。`0/4` 是 2k 步煙霧跑後的預期 ——
訓到約 30 萬步才會得到真能通過隨機佈局的 policy。

## 延伸

- 用 Lesson 17 的深度（最近障礙 bearing/距離）當障礙線索，取代特權位置 —— 真正的板載感知 → 控制。
- 加 curriculum：從 1 根柱子開始，成功率上升後加到 3 根。
- 這個避障 policy 是 Lesson 22 蒸餾成單一板載網路的 teacher 之一。
