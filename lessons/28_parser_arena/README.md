# Lesson 28 — The parser arena (the signature counter-example, quantified)

🌐 **English** (below) · [跳到繁體中文](#中文)

> The code for this lesson lives in `bridge/` (it extends the DroneVoice bridge):
> [`parse_text.py`](../../bridge/parse_text.py), [`eval_parsers.py`](../../bridge/eval_parsers.py),
> [`send_text.py`](../../bridge/send_text.py), [`golden_intents.jsonl`](../../bridge/golden_intents.jsonl).

---

> **In one line:** Race different command parsers on one shared test set and get numbers for when a general model beats your self-trained one. · **Builds on:** L27, L12, L10

## Why

The course's drumbeat is *"a general model isn't good enough → train your own
small one"* (L3/L8/L10/L13/L17). This lesson asks the **opposite**, and settles
it with numbers. For turning a *flexible sentence* into a structured command, a
self-trained fixed-vocabulary classifier (Lesson 10's KWS style) is the **wrong**
tool — it has no slot for "two metres". A general parser — or, in DroneVoice
Phase 3, an on-device LLM with **guided generation** forced to emit a
schema-valid object — is right. The lesson is judgement, not dogma: train your
own when the data is yours and must run on GAP8; reach for a general model +
structured constraints for open language.

## Concept

Three backends, scored against `bridge/golden_intents.jsonl` on four axes
(accuracy, schema-validity, coverage, cost):

- **ruleA** — a bilingual rule parser: keyword → action **plus** a number+unit
  grab, so "往前兩公尺" → `forward 2 m`.
- **kwsB** — a fixed-vocabulary classifier (Lesson 10 KWS spirit): right verb, but
  no quantity slot, so it drops the "two metres".
- **C** — the guided-generation LLM (Apple Foundation Models, Phase 3). There's no
  offline stand-in, so it's reported **SKIPPED** rather than faked.

Every output is checked against `nanodrone.protocol`, so an invalid command can
never score. `send_text.py` is the no-iPhone "voice stand-in": type a sentence,
ruleA parses it, it's sent over the same JSON protocol the app uses.

## Hands-on

```bash
conda activate nanodrone-ai
python bridge/eval_parsers.py            # the comparison table
python bridge/eval_parsers.py --selftest  # asserts (CI)
python bridge/send_text.py --selftest "go forward 2 metres"   # parse only
python bridge/send_text.py "左轉 90 度"   # with sim_server.py running, really flies
```

## Checkpoint ✅

```
backend                 accuracy   schema  coverage
ruleA (rule parser)         1.00     1.00      1.00
kwsB (fixed vocab)          0.31     1.00      1.00
EVAL OK: ruleA acc=1.00 schema=1.00 | kwsB acc=0.31 | covered 26 phrases
```

The arena asserts every rule-parser output is schema-valid, **and** that the
fixed-vocab classifier scores lower on flexible sentences — the quantified reason
this task wants a general model, not a trained-from-scratch one.

## Going further

- Swap backend C for the real Apple Foundation Model — that's DroneVoice Phase 3,
  and this table becomes its evidence.
- Add adversarial phrases to `golden_intents.jsonl` (typos, compound commands)
  and watch where each backend breaks.

---

<a name="中文"></a>
# Lesson 28 — 解析器擂台（招牌反例，量化版）

🌐 [English](#lesson-28--the-parser-arena-the-signature-counter-example-quantified) · **繁體中文**（以下）

> 本課程式放在 `bridge/`（它延伸 DroneVoice 橋接）：`parse_text.py`、`eval_parsers.py`、
> `send_text.py`、`golden_intents.jsonl`。

> **一句話：**讓不同的指令解析器在同一份考題上比賽，用數字看清什麼時候通用模型贏過你自訓的小模型。 · **建立在：**第 27 課、第 12 課、第 10 課

## 為什麼

整門課的節拍是*「通用模型不夠好 → 訓你自己的小模型」*（L3/L8/L10/L13/L17）。這一課問**相反**的問題，
並用數字定案。對於把*彈性句子*轉成結構化指令，一個自訓的固定詞表分類器（Lesson 10 的 KWS 風格）是**錯**工具 ——
它沒有放「兩公尺」的欄位。通用解析器 —— 或在 DroneVoice Phase 3，一個用 **guided generation** 被強制吐出
schema 合法物件的 on-device LLM —— 才對。這一課教的是判斷力，不是教條：資料是你的、又要跑在 GAP8 上時，自己訓；
開放語言就用通用模型 + 結構化約束。

## 概念

三個 backend，對 `bridge/golden_intents.jsonl` 在四軸上評分（準確率、schema 合法率、涵蓋率、成本）：

- **ruleA** —— 雙語規則解析器：關鍵字 → 動作**外加**數字+單位抽取，所以「往前兩公尺」→ `forward 2 m`。
- **kwsB** —— 固定詞表分類器（Lesson 10 KWS 精神）：動詞對，但沒有數量欄位，所以丟掉「兩公尺」。
- **C** —— guided-generation LLM（Apple Foundation Models，Phase 3）。沒有離線替身，所以標 **SKIPPED**，不造假。

每個輸出都對 `nanodrone.protocol` 檢查，非法指令永遠不會得分。`send_text.py` 是沒 iPhone 的「語音替身」：
打一句話，ruleA 解析，透過 app 用的同一套 JSON 協定送出。

## 動手做

```bash
conda activate nanodrone-ai
python bridge/eval_parsers.py            # 對照表
python bridge/eval_parsers.py --selftest  # 驗收（CI）
python bridge/send_text.py --selftest "go forward 2 metres"   # 只解析
python bridge/send_text.py "左轉 90 度"   # 開著 sim_server.py 時，真的會飛
```

## 驗收 ✅

```
backend                 accuracy   schema  coverage
ruleA (rule parser)         1.00     1.00      1.00
kwsB (fixed vocab)          0.31     1.00      1.00
EVAL OK: ruleA acc=1.00 schema=1.00 | kwsB acc=0.31 | covered 26 phrases
```

擂台驗證每個規則解析器輸出都 schema 合法，**而且**固定詞表分類器在彈性句上分數較低 ——
這就是「這個任務要通用模型、而非從零自訓」的量化理由。

## 延伸

- 把 backend C 換成真的 Apple Foundation Model —— 那就是 DroneVoice Phase 3，這張表成為它的證據。
- 在 `golden_intents.jsonl` 加對抗性句子（錯字、複合指令），看每個 backend 在哪裡壞掉。
