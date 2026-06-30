# DroneVoice — the Apple app (Phases 2–4)

🌐 **English** (below) · [跳到繁體中文](#中文)

> **This is an Xcode iOS app target, not a Python lesson.** The Swift files here
> are a reference scaffold — they compile in Xcode as one app module (the
> cross-file types resolve there; a standalone editor will flag them). What's
> *testable in this repo* is the protocol the app speaks: see the **Verify**
> section. The same JSON protocol drives `bridge/sim_server.py` today and a real
> drone later (`hardware/tello_server.py`, `hardware/crazyflie_server.py`).

---

## Why

Bridge phase 1 (`bridge/sim_server.py`) can already be driven by `send.py`. The
product is to drive it from your **phone**: speak, and the drone obeys. Each phase
adds one layer, and at every step someone *without* an iPhone can verify the part
that matters (the protocol) with the Python stand-ins.

## The phases

- **Phase 2 — voice entry.** `SpeechController` (a `SpeechAnalyzer` /
  `SFSpeechRecognizer` recognizer) → text → `CommandParser.keyword` (the bilingual
  table mirroring Lesson 9 / `parse_text.py`) → `DroneCommand` → `BridgeClient`
  sends the same newline-JSON as `send.py`. App Intents expose the same actions to
  Siri / Shortcuts.
- **Phase 3 — on-device LLM.** `CommandParser.parse` uses Apple's **Foundation
  Models** with **guided generation**: the output is constrained to the
  `@Generable DroneCommand`, so a free sentence ("nudge forward about two metres")
  becomes a schema-valid command — no cloud, no training. This is the course's
  *counter-example* (Lesson 28): here a general model + structured constraints
  beats training your own small model.
- **Phase 4 — SwiftUI app.** `ContentView`: connection settings, a live command
  log, telemetry, and a big **EMERGENCY STOP** that always gets through. The UI is
  part of the failsafe — risky commands confirm, and the app enforces safe
  ordering (no moving before takeoff), mirroring `bridge/validate_protocol.py`.

> **API caveat:** `FoundationModels` and the `SpeechAnalyzer` APIs need iOS 26 +
> an Apple-Intelligence device (A17 Pro / M-series), and reflect WWDC25 /
> knowledge cutoff Jan 2026 — confirm names against the current Apple docs in
> Xcode. The `#if canImport(FoundationModels)` guards let the rest build without it.

## Verify (no iPhone needed)

```bash
conda activate nanodrone-ai
python bridge/send_text.py --selftest "go forward 2 metres"   # the Phase-2 parse path
python bridge/eval_parsers.py --selftest                       # Phase 2 vs 3 arena (Lesson 28)
python bridge/validate_protocol.py --selftest                  # the command-stream conformance the app must meet
```

These prove the protocol the app speaks is correct. Phase 5 (real drone) lives in
[`../../hardware/`](../../hardware/).

---

<a name="中文"></a>
# DroneVoice — Apple App（Phase 2–4）

🌐 [English](#dronevoice--the-apple-app-phases-24) · **繁體中文**（以下）

> **這是 Xcode iOS app target，不是 Python 課。** 這裡的 Swift 檔是參考 scaffold ——
> 在 Xcode 裡以單一 app module 編譯（跨檔型別在那裡解析；獨立編輯器會報錯）。本 repo 裡*可測*的，
> 是 app 講的協定：見 **驗證** 段。同一套 JSON 協定今天驅動 `bridge/sim_server.py`，之後驅動真機
> （`hardware/tello_server.py`、`hardware/crazyflie_server.py`）。

## 為什麼

橋接 phase 1（`bridge/sim_server.py`）已能用 `send.py` 驅動。產品目標是用**手機**驅動它：開口說，無人機照做。
每個 phase 加一層，而每一步，沒有 iPhone 的人都能用 Python 替身驗證真正重要的部分（協定）。

## 各 Phase

- **Phase 2 — 語音入口。** `SpeechController`（`SpeechAnalyzer` / `SFSpeechRecognizer` 辨識器）→ 文字 →
  `CommandParser.keyword`（對應 Lesson 9 / `parse_text.py` 的雙語表）→ `DroneCommand` → `BridgeClient`
  送出與 `send.py` 相同的 newline-JSON。App Intents 把同樣的動作開放給 Siri／捷徑。
- **Phase 3 — on-device LLM。** `CommandParser.parse` 用 Apple **Foundation Models** + **guided generation**：
  輸出被約束成 `@Generable DroneCommand`，所以一句自然語（「往前推大概兩公尺」）變成 schema 合法的指令 ——
  不上雲、不訓練。這是課程的*反例*（Lesson 28）：這裡通用模型 + 結構化約束勝過自訓小模型。
- **Phase 4 — SwiftUI app。** `ContentView`：連線設定、即時指令記錄、遙測，以及一顆永遠送得出去的大
  **EMERGENCY STOP**。UI 是 failsafe 的一部分 —— 危險指令會確認，app 強制安全順序（起飛前不准移動），
  對應 `bridge/validate_protocol.py`。

> **API 注意：** `FoundationModels` 與 `SpeechAnalyzer` 需要 iOS 26 + 支援 Apple Intelligence 的裝置
> （A17 Pro / M 系列），且反映 WWDC25／知識截止 Jan 2026 —— 請在 Xcode 對最新 Apple 文件核對名稱。
> `#if canImport(FoundationModels)` 守衛讓其餘部分在沒有它時也能 build。

## 驗證（不需 iPhone）

```bash
conda activate nanodrone-ai
python bridge/send_text.py --selftest "go forward 2 metres"   # Phase 2 解析路徑
python bridge/eval_parsers.py --selftest                       # Phase 2 vs 3 擂台（Lesson 28）
python bridge/validate_protocol.py --selftest                  # app 必須符合的指令串一致性
```

這些證明 app 講的協定正確。Phase 5（真機）在 [`../../hardware/`](../../hardware/)。
