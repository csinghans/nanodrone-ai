# Capstone rubric · 畢業專題評分標準

🌐 English · 繁體中文（下方）

Design your own mission by composing the blocks you built, then grade it here.
Use `validate_mission.py` to check the hard gates automatically.

## Hard gates (must all pass — no partial credit)

| Gate | How it's checked |
|------|------------------|
| Starts with `Takeoff`, ends with `Land` | `validate_mission.py` |
| Every non-terminal phase is **guarded** (overrides `is_done`) | `validate_mission.py` |
| A **Failsafe** is wired in (geofence / lost-link / timeout → land) | `validate_mission.py` |
| A `--selftest` that prints `XXX OK` and **asserts** behaviour, headless | your script |
| `$0`, sim-first, runs without hardware (mic/camera scripted in selftest) | your script |
| Bilingual docs (en + zh-TW), like every other lesson | your `README.md` |

## Scored dimensions (100 pts)

| Dimension | Pts | What earns full marks |
|-----------|----:|------------------------|
| **Integration breadth** | 30 | Combines **≥ 3** capabilities — e.g. voice transitions (L12), find/follow (L13), mapping (L14a) — on one `nanodrone.mission` state machine |
| **Safety** | 25 | Real use of `Failsafe`; sensible geofence; a lost-target or lost-link path that lands, not crashes |
| **On-board awareness** | 20 | Shows it could run on GAP8: int8 footprint < 512 KB and a latency check (L14b) for any learned model used |
| **Verification** | 15 | `--selftest` is meaningful (asserts the *outcome*, not just "ran"); deterministic; green |
| **Docs & demo** | 10 | Clear bilingual README; a GIF/video of the mission flying |

## Going to real hardware (optional, beyond $0)

Take the mission to a real drone — the protocol/controller is all that changes:
Tello over Wi-Fi (~US$100, AI off-board) or Crazyflie + AI-deck (~US$545,
offline, on-board). Always: open space, props clear, RC override ready, and
verify in sim first.

---

# 畢業專題評分標準

用你做出來的積木組一個自己的任務，再用這份標準評分。可用 `validate_mission.py` 自動檢查硬性門檻。

## 硬性門檻（全部必過，沒有部分分）

| 門檻 | 怎麼檢查 |
|------|----------|
| 以 `Takeoff` 開始、`Land` 結束 | `validate_mission.py` |
| 每個非終端階段都**有把關**（覆寫 `is_done`） | `validate_mission.py` |
| 有接上 **Failsafe**（越界／失聯／逾時 → 降落） | `validate_mission.py` |
| 有 headless 的 `--selftest`，印 `XXX OK` 並 **assert** 行為 | 你的腳本 |
| `$0`、sim-first、不靠硬體（麥克風/相機在 selftest 用腳本化） | 你的腳本 |
| 雙語文件（en + zh-TW），跟其他每一課一樣 | 你的 `README.md` |

## 評分維度（100 分）

| 維度 | 分 | 滿分條件 |
|------|---:|----------|
| **整合廣度** | 30 | 在同一台 `nanodrone.mission` 狀態機上結合 **≥ 3** 種能力 —— 例如語音轉移(L12)、找人跟隨(L13)、建圖(L14a) |
| **安全** | 25 | 真的用到 `Failsafe`；合理的 geofence；目標丟失或失聯時會降落而非墜機 |
| **板載意識** | 20 | 展現可上 GAP8：用到的學習模型 int8 footprint < 512 KB，且做了延遲檢查(L14b) |
| **驗證** | 15 | `--selftest` 有意義（assert *結果*，不只「跑過」）；可重現；綠燈 |
| **文件與展示** | 10 | 清楚的雙語 README；一段任務飛行的 GIF/影片 |

## 上真機（選配，超出 $0）

把任務搬上真機 —— 只有協定／controller 要換：Tello over Wi-Fi（約 US$100，AI 在機外）或
Crazyflie + AI-deck（約 US$545，離線、板載）。永遠：空曠處、螺旋槳遠離人、備好 RC 可接管、先在模擬驗證。
