# Lesson 26 — Field-test SOP & Taiwan regulations

🌐 **English** (below) · [跳到繁體中文](#中文)

---

## Why

The last mile of real flight isn't code — it's **procedure and compliance**.
Beginners skip it: pre-flight checks, who the safety pilot is, what to do when it
goes wrong, and what Taiwan's CAA actually requires. Even a toy Tello deserves the
habit, so flying a bigger drone later doesn't end badly. This lesson automates the
*programmable* part of a pre-flight checklist into one GO / NO-GO gate, and the
human/legal parts live below.

## Concept

`preflight_check.py` reuses Lesson 24's `nanodrone.safety` and Lesson 23's log
format to gate the things a machine can check — battery above threshold, the log
directory is writable, the geofence is sane, the take-off height is inside it, and
the failsafe layer is importable. Any failure → **NO-GO** with the reason. The
rest of the SOP and the regulations are a checklist you run yourself.

## Hands-on

```bash
conda activate nanodrone-ai
python lessons/26_field_test/preflight_check.py            # GO / NO-GO report
python lessons/26_field_test/preflight_check.py --selftest  # asserts (CI)
```

## Checkpoint ✅

```
PREFLIGHT OK: 5/5 automated checks pass (battery/log-writable/geofence/takeoff-height/failsafe-importable), GO
```

The self-test asserts a healthy setup returns **GO (5/5)** and that a low battery
returns **NO-GO** naming the battery check — no hardware, so it runs in CI.

## Field-test SOP (run this yourself)

**Before:** charged battery (gate passes); props secure & undamaged; open space,
people clear; airspace legal (see below); a safety pilot with an RC override ready;
logging on (Lesson 23). **During:** one task at a time; eyes on the drone, not the
screen; abort to land on anything unexpected. **After:** review the log
(`replay_flight.py`); note battery temperature; log any incident.

## Taiwan CAA checklist (verify the current official rules yourself)

> This is a study checklist, **not legal advice** — drone rules change; always
> confirm the latest 民航局 (CAA) 遙控無人機 announcements before flying.

- **Weight tier** — sub-250 g toys (Tello ~80 g, Crazyflie ~30 g) have the lightest
  rules, but registration/marking thresholds and operating limits still apply by
  weight; check your exact aircraft.
- **Registration / real-name** — required above the weight threshold; mark the
  aircraft as required.
- **No-fly / restricted zones** — airports, government/military areas, crowds;
  check the official zone map for your location.
- **Operating limits** — daylight / visual line of sight / altitude caps as the
  rules specify; no flying over people.
- Indoors (most of this course's hardware) is generally outside airspace rules,
  but battery/prop/safety-pilot discipline still applies.

## Going further

- Wire `preflight_check` into the DroneVoice Phase 4 app as a pre-flight screen.
- Add aircraft-specific gates (Crazyflie radio link, Tello Wi-Fi RSSI).

---

<a name="中文"></a>
# Lesson 26 — 實地測試 SOP 與台灣法規

🌐 [English](#lesson-26--field-test-sop--taiwan-regulations) · **繁體中文**（以下）

## 為什麼

真實飛行的最後一哩不是程式 —— 是**流程與合規**。新手最常略過：起飛前檢查、誰是安全員、出事怎麼辦、
以及台灣民航局到底要求什麼。連玩具 Tello 都值得養成習慣，之後飛大機才不會出事。這一課把飛行前檢查中
*可程式化*的部分自動化成一個 GO / NO-GO gate，人為與法律部分列在下方。

## 概念

`preflight_check.py` 重用 Lesson 24 的 `nanodrone.safety` 與 Lesson 23 的 log 格式，把機器能檢查的事
把關 —— 電量高於門檻、log 目錄可寫、geofence 合理、起飛高度在框內、failsafe 層可載入。任一失敗 →
**NO-GO** 並附原因。其餘 SOP 與法規是你自己跑的清單。

## 動手做

```bash
conda activate nanodrone-ai
python lessons/26_field_test/preflight_check.py            # GO / NO-GO 報告
python lessons/26_field_test/preflight_check.py --selftest  # 驗收（CI）
```

## 驗收 ✅

```
PREFLIGHT OK: 5/5 automated checks pass (battery/log-writable/geofence/takeoff-height/failsafe-importable), GO
```

自我測試驗證健康設定回傳 **GO (5/5)**，低電量回傳 **NO-GO** 並點名電量檢查 —— 不需硬體，所以能進 CI。

## 實地測試 SOP（自己跑）

**飛行前：** 電池充飽（gate 通過）；螺旋槳鎖緊無損；空曠處、人員淨空；空域合法（見下）；安全員備好 RC 可接管；
log 已開（Lesson 23）。**飛行中：** 一次一個動作；眼睛盯著無人機而非螢幕；任何異常立即中止降落。
**飛行後：** 回放 log（`replay_flight.py`）；注意電池溫度；記錄任何事故。

## 台灣民航局查核清單（請自行核對最新官方規定）

> 這是學習用查核清單，**非法律建議** —— 無人機法規會變；飛行前務必確認最新的民航局遙控無人機公告。

- **重量分級** —— 250 g 以下玩具（Tello 約 80 g、Crazyflie 約 30 g）規定最輕，但註冊/標示門檻與操作限制仍依重量適用；查你的實際機型。
- **註冊 / 實名** —— 超過重量門檻須註冊；依規定在機身標示。
- **禁航 / 限航區** —— 機場、政府/軍事區、人群上空；查你所在地的官方區域圖。
- **操作限制** —— 依規定的日間 / 目視範圍內 / 高度上限；不得在人群上方飛行。
- 室內（本課程多數硬體）一般不在空域規定內，但電池/螺旋槳/安全員紀律仍適用。

## 延伸

- 把 `preflight_check` 接進 DroneVoice Phase 4 app 當飛行前確認頁。
- 加機型專屬 gate（Crazyflie radio 連線、Tello Wi-Fi 訊號）。
