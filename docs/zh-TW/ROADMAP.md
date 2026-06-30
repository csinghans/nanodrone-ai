# Roadmap — Lesson 10 之後的後續課程規劃

> 本文件為規劃藍圖；課程尚未實作，編號與細節可能隨開發調整。它延續 nanodrone-ai 的招牌主題與鐵則：全程 **$0、sim-first**，每課採 **五段式**（為什麼／概念／動手做／驗收／延伸），維護 **en + zh-TW 雙語 docs**，每支腳本都有 `--selftest` 印 `XXX OK` + assert。終極目標不變：GAP8 上 int8、<512KB 的離線板載自飛。

## 一、現況與設計原則

到 L10 為止，課程已走完「sense→decide→act 單一行為」的完整鏈條：感知（L2）、自主避障（L3）、真機板載 int8 部署（L4）、視覺跟隨（L6/L7/L8）、語音與自訓 KWS（L9/L10），並開出 DroneVoice Apple App 橋接支線（phase 1 完成 `bridge/sim_server.py`，一支收 newline-JSON 的 TCP server 驅動 PyBullet sim）。專案的招牌主題是「通用模型不夠好 → 用你自己的資料訓練一個小模型」（L3/L8/L10），終極目標是 GAP8 上 int8、<512KB 的離線板載自飛。

這份規劃的設計原則有五條：

1. **先償還技術債再談整合**——11+ 支飛行腳本各抄一份幾乎逐字相同的 `CtrlAviary+DSLPIDControl` while 迴圈，必須先抽成共用骨幹（L11 `nanodrone.mission`；協定面則由 L27 `nanodrone.protocol` 償還）。
2. **每課必須回扣終極目標與招牌主題**——板載一致性與「訓你自己的模型」是兩個最容易在整合過程中悄悄消失的主題，本規劃明確補上板載收斂課（L14b）、在 L13 強制再訓一個確認分類器，並把「模擬器目前閒置的能力（整張深度圖、光流、域隨機化、蒸餾）逐步榨成自訓小模型」整條補進 Track B，讓招牌主題不只「再現一次」，而是成為一條完整的深化主線。
3. **誠實對待 sim-to-real 落差**——全程用 ground-truth 的課要明說「真機沒有 ground-truth」。Track E 把這條原則做實：先在 $0 sim 打磨遙測／回放／safety 基礎設施，再上平價 Tello 量測真實落差，誠實標硬體成本與「Tello AI 在機外、非離線板載，不是終點」。
4. **嚴守教學鐵則**——五段式、$0 sim-first、雙語 docs、每腳本 `--selftest` 印 `XXX OK` + assert 行為。
5. **能力先在 sim 自產資料、$0、`--selftest` 收斂，硬體與 sim-to-real 落差一律誠實標注、不造假 reuse**——新增的深度／光流／DR／蒸餾課全部沿用既有 `gen_dataset` / `gen_person_dataset` 的「模擬器給 ground truth 當特權標籤」套路與 npz 格式，不重造輪子；真機課（Tello / Crazyflie）一律標明「協定不變、只換 controller」，且明說 AI 在機外（Tello）vs 離線板載（Crazyflie / GAP8）的本質差別。

## 二、軌道（Track）組織

後續課程整併成五條軌道：

- **Track A — 編排主線（Orchestration）**：L11 狀態機骨幹 → L12 語音驅動轉移 → L13 多模態 mini-capstone → L16 畢業專題。這是所有走主線新手的必經路徑。
- **Track B — 板載落地與感知深化（On-device / perception depth）**：L14a 建圖巡邏 → L14b 板載收斂；再往深處走 L17 單目深度 → L18 光流／VO → L19 多障礙 RL（餵感知）→ L20 域隨機化 → L21 蒸餾+壓縮 → L22 多能力蒸餾成單一板載策略。這條把「模擬器目前閒置的能力」逐步榨成自訓 int8 小模型，是招牌主題的深化主幹，也是把課程**貼近真機**而非帶離真機的關鍵。
- **Track C — DroneVoice Apple App（並行選修，需 Apple 硬體）**：L27 協定抽取（前置技術債）→ L28 解析評測擂台（反例對照組的量化地基）→ Phase 2 語音入口 → Phase 3 on-device LLM 解析（反例對照組）→ Phase 4 SwiftUI + 雙向遙測 + app failsafe → Phase 5 sim→真機（5a Tello 先、5b Crazyflie 收束）。無 iPhone 者皆有 100% 等價的 Python 驗收。
- **Track D — 進階 going-further（純文件，不成課）**：swarm、追蹤魯棒性（卡爾曼）、segmentation 標資料等指路文件，給「想再往前」的人指路，不擋畢業。（感測器噪音／domain randomization 已升格為正式課 L20，從本軌移除。）
- **Track E — 真機落地基礎設施（sim-to-real bring-up）**：L23 飛行黑盒子（遙測+回放）→ L24 Tello 平價真機踏腳石 → L25 sim-to-real 落差量測 → L26 實地測試 SOP + 台灣法規。這條把「會飛」變成「合法、安全、可回看、可上真機驗證地飛」，是主線／Track B 訓出的模型真正落地前的最後一哩。

軌道間關係：Track B 訓出的模型（L17 depth / L8 person）是 Track E（L25 量落差）與 Track C（L22 上板敘事）的輸入；Track E 的 `nanodrone/safety.py`（L24 抽出）被 Track C Phase 4/5 與 L26 SOP 共用；Track C 的 `nanodrone.protocol`（L27）是 Tello / Crazyflie / Apple 三端共用的單一事實來源。

## 三、推薦動工順序

**先做 Track A 的 L11，沒有例外。** 理由：L11 是整條 roadmap 最有價值、風險最低的一課——它零硬體、純把 11+ 支腳本的重複 while 迴圈抽成 `nanodrone.mission`，既償還已用 grep 證實的真實技術債，又植入 ROS / PX4 共通的狀態機心智模型，且**後面每一課都依賴它**。L11 一旦動工，必須一次把三件事做對：（a）`mission runner` **不寫死 `num_drones=1`**（為未來預留乾淨介面）；（b）內建 **Failsafe/Return 狀態**；（c）把 `nanodrone/mission.py` 正式納入 `setup/requirements` 與 `.github` CI（含跨課整合 CI）。

之後的順序分成「核心必修」與「進階／選修分支」兩層。

### 核心必修主線（建議依序）

1. **L11**（地基，序列必做第一）
2. **L12**（最簡單的「指令→狀態」整合，中等）— 依賴 L11
3. **L13**（第一個多模態 mini-capstone，進階，內含再訓確認分類器）— 依賴 L11、L12、L8
4. **L14a**（建圖巡邏，進階）— 依賴 L11；**可與 L12/L13 平行**（只依賴 L11，不依賴語音線）
5. **L14b**（板載收斂，進階，補板載裂縫的必修，不可省）— 依賴 L14a、L4、L13
6. **L16**（畢業專題）— 排最後，評的就是前面所有能力

### Track B 感知深化分支（進階選修，但對「想真的上板」的人是核心）

7. **L17 單目深度**（中等）— 依賴 L2/L3/L4。**這條分支的入口**，純監督、直接照搬 `gen_dataset` 套路，最低風險，先做能立刻驗證「我們真的會訓 dense 模型」。
8. **L18 光流／VO**（中等）— 依賴 L1/L3/L8/L4。與 L17 互不依賴，可平行。
9. **L19 多障礙 RL**（進階）— 依賴 L3、L17（depth 當觀測）。必須等感知模態到位才能泛化。
10. **L20 域隨機化**（中等）— 依賴 L17、L2。需要一個已能跑的 depth 模型當受測對象。
11. **L21 蒸餾+壓縮**（進階）— 依賴 L4、L17+L20、L3。需要前面養出的較大模型當 teacher 才有「壓縮」意義。
12. **L22 多能力蒸餾成單一策略**（進階，板載深化線 capstone）— 依賴 L8、L19、L21、L4。必須等避障（L19）與跟隨（L8）兩個 teacher 都在。

> Track B 排序原則：先解鎖新感知模態（深度、光流）→ 餵進更難決策（多障礙 RL）→ 做 sim-to-real 縮差（域隨機化）→ 上板瘦身（蒸餾／壓縮）→ 多能力合一（蒸餾 capstone）。

### Track E 真機落地分支（先 $0 sim，後標硬體）

13. **L23 飛行黑盒子**（入門，$0 純 sim）— 依賴 L1、bridge phase 1。Track E 入口，先把 log 格式／回放工具在 sim 定下來。
14. **L24 Tello 踏腳石**（進階，需 ~US$100 Tello；FakeTello 故 $0 可跑 CI）— 依賴 L23、L11 Failsafe（抽出的 `nanodrone/safety.py`）、bridge phase 1。
15. **L25 sim-to-real 落差量測**（進階，$0 可跑樣本；拍自己的真機落差需 L24 Tello）— 依賴 L8（或 L3）模型、L18（理解感測不完美）、L24（取真機影像，選用）。**呼應並接回 L20 域隨機化的動機。**
16. **L26 實地測試 SOP + 台灣法規**（中等，$0 對 sim／無硬體跑）— 依賴 L23（log）、L11/L24（safety 模組）、L24（真機目標，選用）。

### Track C Apple 產品線分支（並行選修，需 Apple 硬體；無 iPhone 者有 100% 等價 Python 驗收）

17. **L27 協定抽取 `nanodrone.protocol`**（入門，$0）— 依賴 bridge phase 1。**整條 Apple 產品線與真機線的單一事實來源**，必須最先做，否則 Phase 2–5 與 Tello / Crazyflie 各自 reparse JSON、協定必漂移。**強烈建議與 L11 同期償還這筆協定債。**
18. **L28 解析評測擂台**（中等，$0，CI 可跑）— 依賴 L27、L12、L10。把 Phase 3「反例對照組」做成可量化的離線 harness。
19. **DroneVoice Phase 2**（中等，需 iPhone/Xcode；無 iPhone $0）— 依賴 L27、L9
20. **DroneVoice Phase 3**（進階，需 iOS 26 + Apple Intelligence）— 依賴 Phase 2、L27、L28
21. **DroneVoice Phase 4**（進階，SwiftUI + 遙測 + failsafe UI）— 依賴 L27、Phase 3、L23（遙測格式）、L4/L24（failsafe 概念）
22. **DroneVoice Phase 5a（Tello）/ 5b（Crazyflie）**（進階，標硬體）— 依賴 L27、Phase 4、L24（Tello backend）/ L4（cflib）

**可平行**：Track B、Track E、Track C 三條分支彼此解耦，可分頭推進。L14a 與 L12/L13 互不依賴，團隊可分頭做。**最快出真機 demo 的路徑**：L23→L24（Tello over Wi-Fi）比 GAP8 / Crazyflie 路線門檻低得多。**最能補招牌主題的路徑**：L17→L20→L21（自訓 dense 模型→抗 sim-to-real→壓進 512KB）。

---

## 四、各課程 / Phase Outline（五段式）

課程順序：L11 → L12 → L13 → L14a → L14b → L16 → L17 → L18 → L19 → L20 → L21 → L22 → L23 → L24 → L25 → L26 → L27 → L28 → DroneVoice Phase 2 → Phase 3 → Phase 4 → Phase 5a → Phase 5b。

### [Lesson 11] 任務編排骨幹：把飛行迴圈變成狀態機 + 內建 Failsafe（Track A）

- **成本** $0（純 sim、純重構）｜**難度** 中等｜**前置** L5（飛行迴圈）、bridge phase 1（`apply_command` 語意、land 緩降）

**為什麼**：到 L10 為止，每支飛行腳本（L5/L6/L7/L8/L9/L10/bridge）都各自抄了一份幾乎逐字相同的 while 迴圈：建 `CtrlAviary+DSLPIDControl`、每幀算 target/target_yaw、餵 `computeControlFromState`、GUI 路徑 `sync()` / headless 數步數。要把「起飛→找人→跟隨→降落」串起來，得先有一個能管理「現在在哪個階段、何時切下一階段」的東西。新手在這課第一次學到：自主機器人不是一個大 if-else，而是一台**狀態機**——這是 ROS / PX4 / 真實無人機共通的心智模型，越早建立越好。**這也是核心主題的轉折點**：前 10 課在「造能力」（訓模型、寫感知），從這課起進入「組能力」（用既有積木編排）。README 須用一段話明說這個轉折，避免招牌主題像是無聲消失。

**概念**：把既有「雙層架構＋每幀更新 target/target_yaw setpoint」套路正式封裝成 `nanodrone.mission` 模組：一個 `State` 基類（`on_enter()` / `step(state_vector)->(target, target_yaw)` / `is_done()`）＋一個 `Mission` runner，runner 內含的 while 迴圈就是 L5/bridge 那段共用骨架。內建狀態：`Takeoff`（target[2]→1.0，沿用 bridge `apply_command` 的 takeoff 語意）、`Hover`、`GoTo(xyz)`、`Land`（每幀 `z-=0.4*dt` 緩降，逐字搬 bridge 降落邏輯）、以及 **`Failsafe`**（任一狀態偵測到 geofence 越界 / 連續 N 幀感知丟失 / 外部失聯旗標，立即轉入：先 `Hover` 穩住，逾時則 `Land`）。`Failsafe` 是所有後續課程「真機自主必修」的安全網，在地基就內建、全程貫穿，而非只在 L16 rubric 口頭要求。runner **不寫死 `num_drones`**（用 `obs[i]` 索引而非 `obs[0]`），為任何多機延伸預留乾淨介面。

**動手做（交付物）**：
- 新增 `nanodrone/mission.py`：`State` 基類 + `Mission` runner + `Takeoff`/`Hover`/`GoTo`/`Land`/`Failsafe` 內建狀態。
- 新增 `lessons/11_mission/mission_demo.py`：跑腳本化任務「起飛→GoTo(1,0,1.2)→Hover 2s→Land」，並含一個故意觸發 geofence 的測例驗證 `Failsafe`。
- `--selftest`（headless）印兩行：`MISSION OK: ran 4 states [Takeoff>GoTo>Hover>Land], moved 1.0m, landed at z=0.30` 與 `FAILSAFE OK: geofence breach -> Hover -> Land, ended safe`。assert：狀態轉移序列正確、最終高度≈地面、水平位移>0.2m、越界後確實進入 Failsafe 並安全落地。

**驗收 ✅**：`MISSION OK` + `FAILSAFE OK` 兩行綠燈、CI 通過；GUI 模式用 `chase_cam` 看著它依序執行。

**延伸**：把 runner 的 while 迴圈與 ROS 2 行為樹 / PX4 commander 對照，說明這套狀態機如何遷移到真實飛控。

**重用**：逐字重用 `bridge/sim_server.py` 的 `run()` while 迴圈骨架與 land 緩降；`GoTo` 的 setpoint clip 重用 `BOX_XY`/`BOX_Z` geofence；`nanodrone.view` 的 `setup_view`/`chase_cam`；`SelftestInput` 那套「腳本化＋印 OK＋assert」CI 樣板；`Takeoff`/`Land` 語意對齊 bridge `apply_command`。

---

### [Lesson 12] 語音驅動的狀態轉移：用講的切換任務階段（含 source→event adapter）（Track A）

- **成本** $0（CI 完全不需麥克風；想用真語音則沿用 L9/L10 免費 Vosk／自訓模型）｜**難度** 中等｜**前置** L11（狀態機）、L9（`parse_command`）、L10（`KwsListener`）

**為什麼**：L9/L10 教的是「語音→指令→持續速度」，那是「按住搖桿」式的連續控制。真實任務裡你會說「起飛」「跟我來」「降落」這種**切換整體行為**的高階指令。這課讓新手看到：同一句語音接到狀態機上，就從「一直往前飄」升級成「觸發一次階段轉移」。這也示範「指令前端可抽換」——鍵盤、語音、KWS、之後的 app JSON 都只是產生同一種 transition 事件的不同來源。

**概念（明確的 adapter 層）**：`parse_command`（回傳 `(fwd,strafe,up,yaw)` 速度元組或 `'land'`/`None`）、`KwsListener`（回傳 label 字串）、`apply_command`（直接改 target）三者輸出型別根本不同，中間需要一層轉接器。本課明確新增 `nanodrone/mission_events.py`，定義一層 **source→event adapter**：

| 來源 | 原始輸出 | adapter 規則 | 產出 mission event |
|---|---|---|---|
| L9 `parse_command` | `(fwd,strafe,up,yaw)` 元組 / `'land'` / `None` | `'land'`→land；持續正向 fwd 且語境=跟隨→follow；`None`/全零→（不發事件） | `takeoff`/`follow`/`land`/`stop` |
| L10 `KwsListener.poll()` | label 字串 + conf | conf>0.6 才採信；label 直接查表；`background`→不發事件 | 同上（離散 label→event） |
| bridge `apply_command` | 改 target/yaw + mode | mode=`'land'`→land、`'emergency'`→stop；位移類動作→（連續控制，不轉階段） | `land`/`stop` |

runner 加一個 `event->transition` 對照表（沿用 L9 `_CMDS` 的「長詞優先」排序與 L10 `background` 拒絕類別思路，避免噪音誤觸發切階段）。語音線程用 `KwsListener.poll()` 非阻塞模式，飛行迴圈照樣每幀跑。

**動手做（交付物）**：
- 新增 `nanodrone/mission_events.py`（三個 adapter + `event->transition` 表）。
- `lessons/12_voice_mission/voice_mission.py`：語音（或 `--selftest` 腳本化事件）驅動「Idle→(takeoff)→Takeoff→Hover→(land)→Land」。
- `--selftest` 注入時間戳事件序列（復用 L9 `ScriptedVoice` 手法，無需麥克風），印 `VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed, 1 noise-event rejected`。assert 轉移次數、終態、且故意注入的 `background`／低 conf 雜訊事件確實被拒絕（未觸發轉移）。

**驗收 ✅**：`VOICE-MISSION OK` 綠燈；雜訊拒絕 assert 通過。

**延伸**：把 adapter 視為「event source 家族」，預告 DroneVoice 的 JSON 也是同一家族的新成員。

**重用**：L11 `mission` runner 與 `Takeoff`/`Hover`/`Land`；L9 `voice.py` 的 `parse_command` 與 `ScriptedVoice` 時間戳注入；L10 `kws_fly.py` 的 `KwsListener.poll()` 非阻塞輪詢與 `conf>0.6` 拒絕門檻、`background` 安靜類別「不確定就不動作」設計。

---

### [Lesson 13] 多模態完整任務（mini-capstone）：起飛→找到人→跟隨→聽到 land 降落（含再訓一個分類器）（Track A）

- **成本** $0（沿用 L8 在 sim 自產資料訓 PersonCNN；新訓一個輕量入侵者／背景分類器同樣 sim 自產）｜**難度** 進階｜**前置** L11、L12、L8（PersonCNN 與跟隨迴圈）

**為什麼**：這是把整個課程第一次縫成一句人話能描述的完整任務，也是題目原句的直接實作。視覺（L8 學習式找人）負責感知、語音（L12）負責高階指令、狀態機（L11）負責編排、雙層控制負責穩定飛。新手在這課得到第一個能對著鏡頭講「這台無人機會自己找到我、跟著我、我喊降落它就降落」的成品。它也誠實暴露整合才會出現的問題：感知丟失時狀態機該怎麼辦、語音與視覺事件如何不打架。**並且要求學員用 sim 自產資料再訓一個輕量「目標人 vs 背景」二元確認分類器**，掛在 Search→Follow 轉移前當「確認門」（避免把背景色塊誤認成人才轉 Follow）。這讓招牌主題「通用偵測不夠穩 → 訓你自己的小分類器」在 capstone 前再出現一次，且與整合任務有機結合而非硬塞。

**概念（事件優先序表 + 丟失重捕狀態圖）**：把 L8「跟隨真人」整段包成複合狀態塞進 L11 狀態機：

```
Takeoff
  └→ Search（原地慢 yaw 掃描，每 PERCEPTION_EVERY 幀跑偵測）
        ├─ cnn_bearing 命中 且 距離<MAX_RANGE 且【新訓分類器確認=人】 → Follow
        └─ 掃完一圈未命中 → 續掃（逾時 T_search → Failsafe）
  Follow（搬 L8 world_point→target_yaw=theta、reach=dist-DESIRED_DIST 收斂）
        └─ 連續 N=8 幀丟失目標 → 退回 Search
  Land（語音 land 事件，最高優先）
```

**事件優先序表（硬規定）**：`land`(emergency/語音) > `Failsafe`(失聯/越界) > 視覺狀態轉移(Search↔Follow) > 連續控制。`land` 事件在任何狀態都可立即觸發、最高優先；視覺事件絕不覆蓋 land。新增的只有狀態轉移條件、丟失重捕策略與新分類器確認門，感知與跟隨數學完全復用 L8。

**動手做（交付物）**：
- `lessons/13_find_follow_land/train_confirm.py`：sim 自產「人 vs 背景」資料 + 訓一個 tiny CNN 確認器。`--selftest` 印 `CONFIRM-CNN OK: trained on N samples, val acc>0.9`。
- `lessons/13_find_follow_land/mission.py`：完整任務。`--headless` 用 L8 `scripted_person_xy` 走圓 + L12 時間戳 land 事件（第 ~12 秒注入），印 `CAPSTONE-MINI OK: Search→Follow in Ns (confirm-cnn gated), tracked K frames mean bearing err X deg, land event→landed at z=0.30`。assert：(a) 成功 Search→Follow 且經分類器確認門 (b) Follow 期 mean true bearing error<18°（用 `true_bearing_deg` 獨立量測，沿用 L8 門檻）(c) 收到 land 後確實落地 (d) 注入一個假目標背景，分類器確認門擋下、未誤轉 Follow。

**驗收 ✅**：`CONFIRM-CNN OK` + `CAPSTONE-MINI OK` 兩行綠燈，含誤觸發拒絕 assert。

**延伸**：誠實討論——sim 用 `scripted_person` 與 ground-truth bearing 驗收，真機沒有 ground-truth、人會被遮擋；指向 Track D 的卡爾曼濾波重捕。

**重用**：L11 mission runner ＋ `Takeoff`/`Land`/`Failsafe`；L8 `follow_real.py` 的 `cnn_bearing`/`depth_at_bearing`/`world_point` 跟隨數學、PersonCNN、`person.py` 的 `build_person`/`move_person`/`true_bearing_deg`/`scripted_person_xy`；L8 自產資料訓練流程（`gen_person_dataset`/`train_person_cnn` 套路）供新確認器復用；L12 的語音事件→轉移與優先序。

---

### [Lesson 14a] 簡單建圖與自主巡邏：把空間掃一遍並標出障礙（Track B）

- **成本** $0（純 sim、matplotlib 已是現有相依）｜**難度** 進階｜**前置** L11（`GoTo` 航點串接）、L2（取像／測距）

**為什麼**：前面任務都圍著「一個目標／一個人」打轉，但真實自主（PULP-Dronet、巡檢無人機）還需要「涵蓋一塊空間」的能力。這課給新手第一個**空間記憶**的概念：無人機把看過的障礙記在一張 2D 佔據格圖（occupancy grid）上，照預定航點巡邏。它填補最大的感知缺口——深度至今只拿來對單點測距（`dep[cy,cx]`），從沒用整張深度圖。

**概念（如實標示為新增能力）**：**occupancy-grid 投影與多障礙場景 builder 都是新增程式，不是「沿用 L3 場景」**（L3 只有一根柱子且綁在 RL 專用 `AvoidAviary`，不可重用）。把整張（降採樣的）深度圖每一欄轉成一束測距，用 `world_point` 同款幾何把障礙點投影到 numpy 2D occupancy grid（geofence 範圍切格、命中+1）。巡邏本身是 L11 狀態機串一圈 `GoTo` 航點（`GoTo→…→Land`），每到航點掃描更新地圖。把佔據格邏輯抽到新模組 **`nanodrone/map.py`**（供 L14b 與 L16 共用）。決策仍是高階 setpoint，PID 負責穩飛，守雙層架構。

**動手做（交付物）**：
- 新增 `nanodrone/map.py`（occupancy grid + depth-column→world 投影）。
- 新增 `lessons/14a_map_patrol/scene.py`（多柱障礙場景 builder，**自帶、非復用 L3**）。
- `lessons/14a_map_patrol/patrol.py`：巡 4 個角落航點、邊飛邊建地圖，結束存 `output/map.png`（matplotlib，沿用 L2 存圖慣例）。`--headless` 印 `PATROL OK: visited 4/4 waypoints, mapped C occupied cells, obstacles at [(x,y),...]`。assert：(a) 四航點都到達 (b) 兩根已知柱子真實座標附近確有占據格。

**驗收 ✅**：`PATROL OK` 綠燈、`map.png` 產出。

**延伸**：佔據格的解析度 × 範圍 = 記憶體佔用，引出 L14b 的「這在 GAP8 上放不放得下」。

**重用**：L11 mission runner ＋ `GoTo`/`Land` 串航點；`nanodrone.detect` 的 `linearize_depth` 與 `world_point` 幾何；L2 `perception_demo` 的取像與存圖；`env._getDroneImages` 深度通道。

---

### [Lesson 14b] 板載預算下的感知排程與量化：把 mission 能力縫回 GAP8（Track B）

- **成本** $0（純 sim 量測 + 量化；真機驗證選配，沿用 L4 約 US$545 Crazyflie AI bundle）｜**難度** 進階｜**前置** L14a、L4（`quantize_cnn.py` int8/ONNX/<512KB）、L13（被量化的感知模型）

**為什麼（補「與終極目標一致性」裂縫——這是整條 roadmap 的策略補丁）**：L11–L14a 全是 host-side、sim-only 的編排 Python，從沒回頭問「這個能力怎麼板載化」。專案終點是 GAP8 上 int8、<512KB、離線自飛。這課把新能力與 L4 的部署現實縫合，誠實回答三個問題：(1) `PERCEPTION_EVERY=6` 是手調權宜——真實板載推論延遲是多少？(2) L13 的確認 CNN / L8 PersonCNN 量化成 int8 後，精度掉多少、塞不塞得進 <512KB？(3) occupancy grid 的記憶體在 256KB L2 上放不放得下、要怎麼降解析度？這課把「空間記憶 + 學習式感知」與「板載算力預算」正式掛鉤，是把課程**貼近真機**而非帶離真機的關鍵一課。

**概念**：沿用 L4 `quantize_cnn.py` 把 L13 確認 CNN 轉 int8 ONNX，量測 (a) 量化前後精度差 (b) 模型大小 vs <512KB 預算 (c) 在 host 模擬「板載推論延遲」下，感知頻率對狀態機控制穩定性的影響——用一個可調 `INFER_LATENCY_MS` 參數注入延遲，畫出「延遲↑→跟隨 bearing error↑」曲線，解釋為何 `PERCEPTION_EVERY` 不能無腦調小。誠實討論 **sim-to-real 落差**：sim 是完美 ground-truth state，真機有 IMU／位置噪聲、感知有雜訊——指向 L20 的 domain randomization。

**動手做（交付物）**：
- `lessons/14b_onboard_budget/quantize_confirm.py`：把 L13 確認 CNN 量化成 int8 ONNX。`--selftest` 印 `QUANT OK: int8 model 312KB < 512KB budget, val acc 0.93->0.91 (drop 0.02)`。assert 模型 <512KB 且精度掉幅 < 門檻。
- `lessons/14b_onboard_budget/latency_sim.py`：注入 `INFER_LATENCY_MS` 跑 L13 mission，量測 bearing error。`--selftest` 印 `LATENCY OK: at 80ms infer, mean bearing err 16.2deg < 18 (stable); grid fits 64x64 int8 = 4KB`。assert 在合理延遲下控制仍穩、occupancy grid 記憶體 < 板載預算。

**驗收 ✅**：`QUANT OK` + `LATENCY OK` 綠燈。

**延伸**：真機選配——把量化模型實際燒進 AI-deck/GAP8（接 L4 流程），量測真實延遲對照 sim 預測。

**重用**：L4 `quantize_cnn.py` int8/ONNX 量化流程與 <512KB 預算檢查；L13 確認 CNN 與 mission；L14a `nanodrone/map.py` occupancy grid（量其記憶體）；L8 `cnn_bearing`/`depth_at_bearing`。

---

### [Lesson 16] 畢業專題與評分標準：設計你自己的任務（Track A）

- **成本** $0（sim-first 畢業；真機展示選配，沿用 L4 約 US$545 Crazyflie 或 DroneVoice 的 Tello 約 US$100）｜**難度** 進階｜**前置** L11、L12、L13、L14a、L14b

**為什麼**：整個課程到這裡收束成一個讓學員「自己出題、自己整合、能對外展示」的 capstone。前面每課都是給定任務；畢業專題要學員自己用 `nanodrone.mission` 積木組一個新任務（例如「巡邏→發現入侵者→跟隨並語音回報→喊 land 降落」），按一份明確 rubric 自評。這也是 sim-first 全程 $0 旅程的終點站，並給出通往真機的橋（L4 Crazyflie / DroneVoice Phase 5 Tello）。

**概念（顯式交代主題轉折 + 回扣反例）**：不教新演算法，提供 capstone 範本與 rubric：用 L11 狀態機把 L12（語音）＋L13（找人跟隨／再訓分類器）＋L14a（建圖巡邏）＋L14b（板載預算）任選 ≥3 種能力組成自訂任務圖。README 須用一段話**正式交代核心主題的轉折弧**：從「通用模型不夠好→訓你自己的小模型」（L3/L8/L10/L13 確認器）到「用既有能力積木做編排」（L11–L16），並把 DroneVoice Phase 3 那個「通用大模型+結構化約束就夠」的反例，以一段文字回扣對比（何時該訓 vs 何時不必訓），避免招牌主題無聲消失。提供 mission 驗證器，把鐵則「`--selftest`＋印 OK＋assert」升級成「學員自己的任務也要能 `--selftest`」。Rubric 維度：整合廣度、`--selftest` 綠燈（硬門檻）、安全（geofence／failsafe／丟失重捕，須實際用到 L11 `Failsafe` 狀態）、是否含板載考量（L14b）、文件雙語、展示影片。

**動手做（交付物）**：
- `lessons/16_capstone/`：(a) `template_mission.py` 範本 ＋ README 雙語說明 ＋ `RUBRIC.md` 評分表（百分制，`XXX OK` 綠燈為硬性門檻）；(b) `validate_mission.py` 任務驗證器，印 `CAPSTONE OK: graph valid (S states, T transitions), has Takeoff+Land+Failsafe, all transitions guarded, selftest green`。assert 圖合法、含 Failsafe、所有轉移有觸發條件。範本任務本身附 `--selftest` 當示範。

**驗收 ✅**：`CAPSTONE OK` 綠燈；學員自訂任務也須各自 `--selftest` 綠燈。

**延伸**：指向 L4 與 DroneVoice Phase 5 的真機路線，把畢業作品搬上 Tello / Crazyflie。

**重用**：L11 `nanodrone.mission` 全套（含 Failsafe）；L12/L13/L14a/L14b 當可組裝能力積木；全課程「`--selftest`＋OK＋assert＋雙語 docs」鐵則當 rubric 硬指標。

---

### [Lesson 17] 單目深度估計 CNN：第一次訓 dense 模型（Track B）

- **成本** $0（純 sim、自產特權標籤）｜**難度** 中等｜**前置** L2（`detect.linearize_depth`）、L3（`TinyDronet`／訓練骨架）、L4（footprint/ONNX 演算）

**為什麼**：目前深度只被拿來對單點測距（`detect_blob` 的 `dep[cy,cx]`、`follow_real` 的 `depth_at_bearing` 取一小 patch），整張 HxW 深度圖從沒被學過。痛點直指終極目標：真機 AI-deck 只有灰階相機、沒有深度感測器，要避障／測距就得「從單張影像猜深度」——這正是「通用規則不夠 → 訓你自己的小模型」（L3/L8）的經典理由再現，並把模擬器閒置的深度通道變成免費的 dense 特權標籤。這課是 Track B 感知深化分支的入口。

**概念**：監督式 dense regression：影像→每像素深度（log-depth + scale-invariant loss）；encoder-decoder 與 L3 純 encoder 的差別；為何 dense 深度圖能餵後續避障（L19）。GAP8 限制：解析度壓到 64×64、輸出下採樣、int8 footprint 必須 <512KB（沿用 L4 算法）。

**動手做（交付物）**：
- `lessons/17_depth/gen_depth_dataset.py`：sim 自產，`env._getDroneImages` 同時拿 rgb 與整張 dep，`linearize_depth` 逐像素轉公尺當 label，存 `output/depth_dataset.npz`（X/y 格式同 L3/L8）。
- `lessons/17_depth/train_depth_cnn.py`：`TinyDepthNet`，encoder 直接抄 `TinyDronet.features` 三層 conv，加輕量上採樣 head。
- `lessons/17_depth/depth_demo.py`：飛一圈存預測 vs 真值熱圖 PNG。
- `--selftest`（headless）印 `DEPTH OK: trained N samples, val AbsRel=0.XX, int8 footprint=YYY KB (<512 fits)`。assert `AbsRel<0.25` 且 `footprint<512`。

**驗收 ✅**：`DEPTH OK` 綠燈、熱圖 PNG 產出、CI 通過。

**延伸**：dense 深度餵進 L19 多障礙 RL 當觀測；指向 L20「乾淨 sim 深度上真機會垮」。

**重用**：`gen_dataset.py` 的 `CtrlAviary+DSLPIDControl` 取樣迴圈與 box 重置邏輯；`nanodrone.linearize_depth`（`detect.py`）逐像素套用；`train_cnn.py` 的 `TinyDronet.features` 三層 conv 當 encoder、`device='mps'` 與 npz 訓練骨架；L4 `quantize_cnn` 的 `n_params/1024` footprint 與 ONNX 匯出算 int8 大小。誠實標示：encoder-decoder 上採樣 head 是新增（L3 只有 encoder），scale-invariant loss 是新增。

---

### [Lesson 18] 光流 / 視覺里程計：無 GPS 自估狀態（Track B）

- **成本** $0（純 sim、特權位移標籤）｜**難度** 中等｜**前置** L1（hover）、L3（訓練骨架／軌跡圖）、L8（取樣樣板）、L4（footprint）

**為什麼**：目前所有飛行迴圈都吃 `env._getDroneStateVector` / `obs[0]` 的「模擬器特權位置」（如 `follow_real` 的 `drone_pos=state[0:3]`），真機沒有這個外部定位。痛點：要離線自飛就得「只靠機載相機估自己動了多少」。這是新的感知模態（連續兩幀的運動），可訓一個小 CNN 回歸像素位移→機體速度，延續招牌主線又補上自主必備的狀態估計。

**概念**：光流＝連續兩幀的像素位移場；用已知模擬器位移差當特權標籤學「flow→body velocity」；積分得里程計與漂移概念；為何下游 setpoint 控制（雙層架構）需要它。誠實標示真機落差：真機室內定位需向下相機（Crazyflie Flow deck v2 約 US$45，非本課強制），且積分會累積漂移——位置是估計、不是真值。GAP8：兩張 64×64 灰階堆疊輸入、輸出 2~3 個速度數、int8<512KB。

**動手做（交付物）**：
- `lessons/18_flow/gen_flow_dataset.py`：sim 中對 hover 機隨機平移／偏航，存相鄰兩幀 + 真位移差 `(dx,dy,dyaw)` 當 label。
- `lessons/18_flow/train_flow_net.py`：`FlowNet`（雙幀堆疊→小 conv→3 數回歸）。
- `lessons/18_flow/odom_demo.py`：飛預設路徑，把「積分估計軌跡 vs 真實軌跡」畫成 top-down PNG。
- `--selftest` 印 `FLOW OK: N pairs, vel MAE=0.0X m/s, drift over 5s=0.XX m, int8=YYY KB`。assert `vel MAE<0.1` 且 `footprint<512`，並報告漂移量讓學員看到 sim-to-real 隱憂。

**驗收 ✅**：`FLOW OK` 綠燈、軌跡 PNG 產出。

**延伸**：把里程計餵回 L11 狀態機當「沒有特權位置時的 fallback 定位」；指向 L25 真機光流劣化。

**重用**：`gen_person_dataset.py` 的 hover-then-capture 取樣樣板；`train_person_cnn.py` 訓練迴圈與 `BEARING_SCALE` 式標籤縮放慣例（改成速度縮放）；`train_rl.py` 的 `_save_trajectory_plot` 畫軌跡；L4 footprint 算法；`detect.py` 的 `fov_deg` 幾何概念做尺度換算。誠實標示：整張影像做運算（cv2 光流或雙幀 CNN）是 sim 第一次用到，之前只點取樣。本課把古典光流原理（cv2）與「訓你自己的小 CNN（特權標籤）回歸速度」兩種角度合併在同一課，不另開兩門光流課。

---

### [Lesson 19] 更難的多障礙 RL 賽道：餵感知、會泛化（Track B）

- **成本** $0（純 sim）｜**難度** 進階｜**前置** L3（`AvoidAviary`/PPO 全套）、L17（depth 當觀測）

**為什麼**：現有 RL 只有一根固定柱、且綁死在 `AvoidAviary`（程式註解自承：佈局固定才能只靠 KIN 觀測學會繞行，隨機化就得把障礙資訊餵進觀測）。痛點：真實避障是多障礙且每次不同。要泛化就得把 L17 學到的深度（或障礙方位）放進觀測——這把感知課的成果真正接進決策，是 Track B 的高潮前奏。

**概念**：把感知摘要（depth CNN 輸出的數條測距射線 / 最近障礙 bearing+距離）併入 RL 觀測 → policy 對隨機佈局泛化；curriculum 從 1 柱漸增到 3 柱；reward shaping 重用既有 progress+crash+goal 結構。GAP8：policy MLP 本就極小，重點示範「感知前端 int8 + 控制後端」分離部署。

**動手做（交付物）**：
- `lessons/19_multi_avoid/multi_avoid_aviary.py`：`AvoidAviary` 子類，reset 隨機生成 1–3 根柱、把每柱最近距離／方位併入 observation。
- `lessons/19_multi_avoid/train_multi_rl.py`：沿用 PPO + curriculum timesteps。
- eval 畫多柱繞行軌跡 PNG。
- `--selftest`（少步數冒煙）印 `MULTI-AVOID OK: trained Ns, success X/10 on random layouts, 0 crash in selftest ep`。assert 至少完成一條無撞軌跡 + 觀測維度含障礙資訊。

**驗收 ✅**：`MULTI-AVOID OK` 綠燈。

**延伸**：這個避障 policy 是 L22 多能力蒸餾的避障 teacher；指向 L20 把訓練場域隨機化。

**重用**：`avoid_aviary.py` 幾乎整檔當基底（`_spawn_obstacle` 改成迴圈生成多柱、`_computeReward`/`_Terminated`/`_Truncated` 沿用 progress+crash+goal）；`train_rl.py` 的 PPO 設定（`ent_coef=0.01`）、`make_vec_env`、evaluate 與 `_save_trajectory_plot`；L17 depth CNN 推論當觀測前端；**直接復用 L14a 的多柱 `scene.py` builder**（不重造場景）。誠實標示：「感知併入觀測 + curriculum」是新增、是 `avoid_aviary` 註解明確點名的真缺口。

---

### [Lesson 20] 域隨機化：縮小 sim-to-real 落差（Track B）

- **成本** $0（純 sim）｜**難度** 中等｜**前置** L17（depth 模型與資料管線）、L2（視覺場景建構）

**為什麼**：L17–L19 的模型都在乾淨無噪的模擬畫面上訓練（感測器噪音、segmentation、domain randomization 至今全沒用過），一上真機就垮。痛點：sim 太完美→模型過擬合到模擬外觀。解法是訓練時隨機化外觀／光照／噪音，逼模型學穩健特徵——這是讓「自己訓的小模型」真能上板的關鍵一課，仍 $0 全在 sim。它正面回答 L25 量到的 sim-to-real 落差「該怎麼縮」。

**概念**：domain randomization：隨機化牆面／地板顏色、光照方向、相機噪音／模糊、障礙尺寸顏色；為何這比「把 sim 做得更逼真」更划算；用一個 randomized 重訓的 L17 depth CNN 對比 baseline 證明穩健度提升。

**動手做（交付物）**：
- `lessons/20_domain_rand/randomize.py`：一組可重用 randomizer（`changeVisualShape` 改 PyBullet 顏色、加高斯影像噪音、抖動光照）。
- `lessons/20_domain_rand/retrain_depth_dr.py`：呼叫 randomize 後重跑 L17 訓練。
- 對比腳本在「故意換配色的測試場」上比 baseline vs DR 模型。
- `--selftest` 印 `DR OK: baseline AbsRel=0.4X on shifted scene, DR model=0.2X (robustness up YY%)`。assert DR 模型在偏移場上的誤差顯著低於 baseline。

**驗收 ✅**：`DR OK` 綠燈。

**延伸**：把同套 randomizer 套到 L18 光流、L19 RL 場景；指向 L25 用真機影像驗證 DR 是否真有效。

**重用**：L17 `gen_depth_dataset.py` / `train_depth_cnn.py` 整套（randomize 插在取樣迴圈影像捕捉前）；`perception_demo.py` / `gen_dataset.py` 的 `createVisualShape rgbaColor` 模式改用 `changeVisualShape` 動態改色；`person.py` 多色建模思路當「難樣本」參考。誠實標示：噪音／光照／randomization 是模擬器第一次用到。

---

### [Lesson 21] 知識蒸餾 + 模型壓縮：延伸 L4 量化上板（Track B）

- **成本** $0 訓練；硬體仍沿用 L4 既標的約 US$545 AI bundle，**不重複計費**｜**難度** 進階｜**前置** L4（量化/ONNX/footprint）、L17+L20（teacher 模型）、L3（訓練骨架）

**為什麼**：L4 只做了 footprint 檢查與 ONNX 匯出，沒真的「壓縮」。痛點：L17/L20 為了精度可能養出比 `TinyDronet` 更大的 depth 模型，未必塞得進 512KB。解法：用大模型當 teacher 蒸餾出 student 小模型，再量化——直接把 L4 的 int8/<512KB 鐵則推進到「主動壓到能上板」。這與 L14b（板載收斂、量測量化掉幅）互補：L14b 量「塞不塞得下」，L21 教「塞不下時怎麼主動壓」。

**概念**：知識蒸餾：teacher 軟輸出指導 student（dense 深度用 teacher 預測圖當額外監督）；蒸餾 vs 直接訓小模型的精度差；post-training int8 量化的精度掉幅；用 L4 公式驗證 student 真的 <512KB。

**動手做（交付物）**：
- `lessons/21_distill/distill_depth.py`：載入 L20 的大 DR depth 模型當 teacher，訓一個更小 student（conv 通道砍半）。
- `lessons/21_distill/compress_report.py`：擴充 L4 `quantize_cnn`，印 teacher vs student 參數量／footprint／精度三欄對比 + 匯出 student ONNX。
- `--selftest` 印 `DISTILL OK: teacher YYY KB / student ZZZ KB (<512), AbsRel teacher=0.2X student=0.2Y (kept WW%)`。assert student `footprint<512` 且精度保留率 > 門檻。

**驗收 ✅**：`DISTILL OK` 綠燈。

**延伸**：蒸餾流程是 L22 多 teacher 合一的前置；對照 L14b 的延遲曲線討論「小 student 推論更快」。

**重用**：L4 `quantize_cnn.py` 的 footprint 計算、ONNX 匯出、精度 sanity 三段幾乎整段沿用；`train_cnn.py` 訓練骨架；L17/L20 的 depth 模型與資料集當 teacher 與評估集；`TinyDronet`/`PersonCNN` 的 `features` 架構縮減成 student。

---

### [Lesson 22] 多能力蒸餾成單一板載策略（Track B capstone）

- **成本** $0（純 sim）｜**難度** 進階｜**前置** L8（跟隨 teacher）、L19（避障 teacher）、L21（蒸餾流程）、L4（footprint）

**為什麼**：目前避障（L19）與跟隨（L8）是兩個獨立模型／迴圈，真機 GAP8 跑不起多個網路也切不動。痛點：板載算力只夠一個策略。解法：把多個 teacher（避障 policy + 跟隨 CNN）的行為蒸餾成「一個」小策略網路——這是整條板載 AI 深化主線的收尾，把前面所有自訓小模型整合成可上板的單一大腦。與 L16 畢業專題的差別：L16 是「用 mission 積木編排」的 host-side capstone，L22 是「把多能力壓成單一 int8 網路」的板載 capstone，兩者各自收束一條主線。

**概念**：policy/behaviour distillation：在混合情境（要跟人又要繞障）下用 teacher 們產生 (觀測→動作) 示範資料，訓一個 student 策略模仿；模式切換 vs 統一策略；單一 int8 網路的 footprint 與延遲優勢。

**動手做（交付物）**：
- `lessons/22_unified/gen_policy_dataset.py`：在一個同時有人 + 多柱的場景跑 L19 避障與 L8 跟隨 teacher，依情境取較安全動作，存 `(obs,action)` npz。
- `lessons/22_unified/distill_policy.py`：小 MLP/CNN student 模仿。
- `lessons/22_unified/unified_fly.py`：飛一段同時跟人且避障。
- `--selftest` 印 `UNIFIED OK: distilled from 2 teachers, follow err=XX deg & min obstacle dist=0.XX m (no crash), single int8=YYY KB`。assert 跟隨誤差 < 門檻 且 全程未撞 且 `footprint<512`。

**驗收 ✅**：`UNIFIED OK` 綠燈。

**延伸**：把統一策略當 L16 畢業專題或 DroneVoice Phase 5b 的「板上 reflex」；真機選配燒進 GAP8（接 L4）。

**重用**：`follow_real.py` 的跟隨迴圈／`cnn_bearing`/`depth_at_bearing`/`world_point` 當跟隨 teacher 與評估器；L19 multi_avoid policy 當避障 teacher；`train_rl.py` evaluate 的成功／碰撞統計與 `_save_trajectory_plot`；L21 蒸餾骨架與 L4 footprint 驗證；統一飛行外殼接 L11 `mission` runner 與 L27 `protocol.step_target`（不再抄 `sim_server.py`）。

---

### [Lesson 23] 飛行黑盒子：遙測記錄與離線回放（Track E 入口）

- **成本** $0（純 sim、純軟體）｜**難度** 入門｜**前置** L1（飛行迴圈）、bridge phase 1（newline-JSON 協定與 selftest 注入樣板）

**為什麼**：真機落地最先需要的不是更聰明的 AI，而是「飛完能回看發生什麼」。事故、抖動、誤觸發都要靠 log 重現。先在 $0 sim 把 log 格式與回放工具定下來，之後 Tello(L24)/Crazyflie 只要照同一格式吐資料就能用同一套工具回放，避免每換平台重寫分析腳本。這也是 sim-first 鐵則的最佳示範。

**概念**：結構化遙測（每幀 `timestamp/pos/target/yaw/battery` 寫成 newline-JSON，與 bridge 既有協定同源）、固定取樣率時間序列、離線回放（把記錄的 target 餵回飛控重演）、headless 驗收。解釋為何用 newline-JSON 而非二進位：人類可讀、可 grep、可被 L9/L10 的 `ScriptedVoice` 風格注入。

**動手做（交付物）**：
- `lessons/23_telemetry/record_flight.py`：在共用飛行迴圈尾端每幀 append 一筆 JSON 到 `logs/*.jsonl`。
- `lessons/23_telemetry/replay_flight.py`：讀 jsonl，把每幀 target 餵回 `CtrlAviary+DSLPIDControl`（或 L11 mission runner）重演，GUI 可看。
- `nanodrone/telemetry.py`：`FlightLogger.log(state,target,yaw)` / `load_log()` 抽成可重用模組。
- `--selftest`：record 印 `RECORD OK: logged N frames, M fields/frame, file=…`（assert N>0 且每幀欄位數一致）；replay 印 `REPLAY OK: replayed N frames, end-pos within 0.15 m of logged end`（assert 回放終點與記錄終點誤差 <0.15 m，證明回放忠實）。

**驗收 ✅**：`RECORD OK` + `REPLAY OK` 兩行綠燈。

**延伸**：log 是 L26 SOP「飛行中須開 log」的前置；指向把 log 接到視覺化 dashboard（DroneVoice Phase 4 遙測 UI）。

**重用**：直接重用 L11 mission runner（或 `bridge/sim_server.py`）的 `CtrlAviary+DSLPIDControl` + 每幀 target 迴圈與 `chase_cam`/`sync`；log 一行插在 `ctrl.computeControlFromState` 之後。JSON 行格式沿用 bridge `serve()` 的 newline-JSON 慣例。selftest 的 scripted 注入沿用 `sim_server.py` 的 `(t_s, cmd)` 時間戳清單樣板與 `kws_fly.py` scripted_label 樣板。誠實標示：log/replay 格式與工具是真正新內容（codebase 無任何 log/replay）。

---

### [Lesson 24] 第一台會飛的真機：平價 Tello over Wi-Fi（Track E）

- **成本** **需硬體：DJI/Ryze Tello 約 US$100**；軟體 `pip install djitellopy` 免費；`--selftest` 用 FakeTello 故 $0 可跑 CI｜**難度** 進階｜**前置** L23（真機要先能 log）、L11（`Failsafe`，並把它抽成 `nanodrone/safety.py`）、bridge phase 1（指令協定與 `apply_command` 介面）、L5/L9 飛行語意

**為什麼**：GAP8/AI-deck 路線（L4，約 US$545、要焊接燒錄、離線板載）對新手門檻高。Tello 只要約 US$100、Wi-Fi 連線、一個 pip 就能飛，AI 跑在筆電上透過 Wi-Fi 送指令——這正是 bridge 既有 TCP JSON 協定的真機版：同一份結構化指令，後端從 sim 換成 Tello。先在最便宜、摔了不心疼的真機上把「指令真的讓東西飛起來」跑通，建立信心與 sim-to-real 直覺，再進階到 Crazyflie 離線板載。**誠實標注**：Tello 的 AI 在機外、非離線，不是課程最終目標，它是「協定可攜性」的證明與安全的真機第一步。codebase 目前完全無 Tello 程式，這是真正的新內容。

**概念**：Wi-Fi 連線真機、把 bridge/protocol 的高階 action（takeoff/forward/turn_left/land/emergency）映射到 DJITelloPy 的 `takeoff()`/`move_forward(cm)`/`rotate_ccw(deg)`/`land()`/`emergency()`、單位換算（協定用公尺、Tello 用公分／度）、真機雙層架構對應（你的 AI 送高階指令，Tello 內建飛控穩定，AI 不碰馬達——與 sim 的 DSLPIDControl 角色相同）、真機 failsafe 落地。**本課把散落的 failsafe 抽成體系**：新增 `nanodrone/safety.py`（純函式：`battery_gate(vbat/pct)`、`geofence_clip(target)`（從 bridge 抽出）、`link_watchdog(last_cmd_t, now)`、`decide_failsafe(...)` 回傳 `'ok'/'low_batt'/'lost_link'/'out_of_bounds'/'estop'`），供 Tello、Crazyflie、Apple Phase 4、L26 SOP 共用，並可在 sim 注入合成故障測試（真機你不敢把電池放到 3.5V，sim 可以）。這把 L11 內建的 `Failsafe` 語意抽成可單元測試、可注入故障的共用模組，而非另起一門狀態機課。

**動手做（交付物）**：
- `nanodrone/safety.py`（純函式 safety 層 + `--inject low_batt|lost_link|out_of_bounds` 在 sim 注入故障的測試）。
- `lessons/24_tello/tello_backend.py`：`class TelloBackend: apply_command(cmd)` 把 13 種 action 翻成 DJITelloPy 呼叫，與 `sim_server.py` 的 `apply_command` 同介面。
- `lessons/24_tello/fly_tello.py`：接 bridge TCP server 或讀指令清單驅動真 Tello，掛上 `nanodrone/safety.py`。
- `--selftest`（不連硬體，用 FakeTello 記錄收到的呼叫）印 `TELLO OK: mapped 13/13 actions to Tello calls (1.0 m forward -> move_forward(100cm), 90 deg -> rotate_ccw(90)), unit conversion verified; safety 4/4 faults triggered correct response`。assert 每個 action 映射到正確 DJITelloPy 呼叫與單位、未連線不真的起飛、四種注入故障觸發預期狀態。

**驗收 ✅**：`TELLO OK` 綠燈（含 safety 注入測試）。

**延伸**：同一協定換 Crazyflie controller（DroneVoice Phase 5b）；指向 L25 用 Tello 相機錄影量 sim-to-real 落差。

**重用**：`TelloBackend.apply_command` 與 L27 `protocol.step_target` 共用同一組 action 名稱、distance/degrees 預設（0.5m/30°）與 body-frame 語意；`geofence_clip` 直接搬 `sim_server.py` 末尾的 `np.clip(±BOX_XY, BOX_Z)`；`battery_gate` 把 `fly_crazyflie.py` 的 `MIN_TAKEOFF_VOLTAGE` 閘一般化；emergency/freeze 與 land 緩降沿用 `sim_server.py` 的 `mode=='emergency'`/`landing(z-=0.4*dt)`；FakeTello stub 沿用 `input.py` `SelftestInput` 的「腳本化假後端供 CI」樣板。

---

### [Lesson 25] 把 sim 訓練的模型搬上真機，誠實量測 sim-to-real 落差（Track E）

- **成本** $0 可跑（用內附樣本影片 + sim）；要拍自己的真機落差需 L24 的 Tello（約 US$100）｜**難度** 進階｜**前置** L8（或 L3）的訓練模型、L18（理解真機感測不完美）、L24（取得真機影像，選用）

**為什麼**：整套課程的反覆主題是「用自己的資料訓小模型」（L3/L8/L10），但這些模型都只在 sim 驗過。落地的關鍵一步是：把 sim 訓的偵測／避障模型放到真機畫面上跑，量它掉多少分，並理解為什麼（光照、材質、相機雜訊、運動模糊——sim 全沒有）。這課把「sim 完美 vs 真機髒」的落差變成可量測的數字，而非空談，並直接引出 L20 域隨機化為何重要、是否值得用真機資料 fine-tune。

**概念**：sim-to-real gap 的來源（域偏移）、用同一模型在 sim 影像與真機影像上跑並比對偵測準確率／bearing 誤差、在 sim 影像加合成劣化（高斯噪音、亮度抖動、模糊）近似真機作為輕量 domain randomization、決定「要不要用真機資料 fine-tune」。誠實面對：純 sim 模型上真機通常會掉分。

**動手做（交付物）**：
- `lessons/25_sim2real/measure_gap.py`：同一份 L8（或 L3）的 CNN／偵測器，分別吃 sim 影像與真機／錄影影像，輸出 bearing 誤差與偵測率對照表。
- `nanodrone/degrade.py`：`add_noise`/`jitter_brightness`/`blur` 純函式，給 sim 影像加真機味。
- 可用 L24 Tello 錄的影片當真機輸入，無 Tello 則用內附樣本影片。
- `--selftest` 印 `SIM2REAL OK: sim bearing-err=… deg, degraded bearing-err=… deg, gap=… deg measured over N frames`。assert 量得出非零 gap 且 pipeline 跑通；**不 assert 模型一定準**，誠實呈現落差。

**驗收 ✅**：`SIM2REAL OK` 綠燈（量到非零 gap）。

**延伸**：把量到的 gap 當 L20 DR 訓練的成效基準（DR 模型 gap 應更小）；討論真機資料 fine-tune 的成本／收益。L20 在 sim 端「訓練時隨機化以求穩健」，L25 在「拿真機影像量實際掉了多少分」，兩者一推一驗、互補；`degrade.py` 與 L20 `randomize.py` 共用噪音／模糊原語。

**重用**：偵測器直接載入 L8 `train_person_cnn.py` 的模型與 `follow_real.py` 的 `cnn_bearing`/`depth_at_bearing`/`true_bearing_deg` 量測手法（已是「估計 vs 真值」比對）；或 L3 `train_cnn.py` 避障 CNN。sim 端影像沿用 `_getDroneImages`，真機端沿用 L24 Tello 影格。`degrade.py` 與 L20 `randomize.py` 共用噪音／模糊原語（避免重造）。

---

### [Lesson 26] 實地測試 SOP 與台灣法規：把「會飛」變成「合法且安全地飛」（Track E 收束）

- **成本** $0（pre-flight 檢查可對 sim 或無硬體跑；對真機跑需 L24 Tello）｜**難度** 中等｜**前置** L23（log）、L11/L24（`nanodrone/safety.py`）、L24（真機目標，選用）

**為什麼**：真機落地的最後一哩不是程式，是流程與合規。新手最容易忽略：起飛前檢查、誰是安全員、出事怎麼辦，以及台灣民航局（CAA）對遙控無人機的註冊／標示／禁航區／重量分級規定。Tello/Crazyflie 雖輕，仍要養成 SOP 習慣，避免一上手大機就出事。這課把 L11/L24 的 failsafe 與 L23 的 log 串成可執行的飛行前／中／後檢查清單，並把「可自動檢查的項目」自動化。

**概念**：飛行前／中／後 SOP（電池、螺旋槳、空域、安全員、RC override、log 開啟）、台灣 CAA 遙控無人機規定要點（依重量分級的註冊與操作規定、禁航／限航區——**課程提供查核清單而非法律建議，並提醒自行查最新官方公告**）、把可程式化的 pre-flight 檢查自動化。解釋為何即使玩具機也要 SOP：習慣養成決定你飛大機時會不會出事。

**動手做（交付物）**：
- `lessons/26_field_test/preflight_check.py`：讀真機／sim 狀態，跑可自動化的 pre-flight gate（電池 > 閾值、`logs/` 可寫、geofence 與起飛高度合理、`nanodrone/safety.py` 可載入），全過才回 GO。
- docs 內附 en + zh-TW 的「實地測試 SOP 清單」與「台灣 CAA 查核清單（附官方來源連結，提醒自行確認最新版）」。
- `--selftest` 印 `PREFLIGHT OK: 5/5 automated checks pass (battery/log-writable/geofence/takeoff-height/failsafe-importable), GO`。assert 全項通過才 GO，任一失敗回 NO-GO 並列出原因。

**驗收 ✅**：`PREFLIGHT OK` 綠燈（或 NO-GO 且原因清楚）。

**延伸**：把 SOP 接到 DroneVoice Phase 4 的 app 端「起飛前確認頁」；指向飛大機的進階法規（不在本課範圍）。

**重用**：`battery_gate` 重用 L24 `nanodrone/safety.py`（源自 `fly_crazyflie.py`）；geofence 合理性檢查重用 safety.py 參數；log 可寫檢查重用 L23 `nanodrone/telemetry.py` `FlightLogger`；失聯／急停 SOP 對應 L11/L24 狀態機；雙語 docs 走既有 `tools/gen_docs.py` 的 en 來源 + zh-TW 流程。

---

### [Lesson 27] 把飛行協定抽成 `nanodrone.protocol`：一個 schema，到處重用（Track C 前置技術債）

- **成本** $0（純 sim/CPU、無新套件）｜**難度** 入門｜**前置** bridge phase 1（已完成）

**為什麼**：`bridge/sim_server.py` 的 `apply_command` 把「協定定義（哪些 action、distance/degrees 預設、body-frame 數學、geofence）」和「PyBullet 飛行迴圈」綁在同一個檔案。DroneVoice Phase 2/3/4、Tello(L24)、Crazyflie 每個都要解析同一份 JSON——若不先抽出單一可測的 schema，各端會各自硬編 action 清單與預設值，協定必然漂移。這是整條 Apple 產品線與真機線最大的技術債，必須先還。這也呼應設計原則一（先償還技術債），並示範什麼叫「把契約從實作裡解放出來」。**建議與 L11 同期償還**（L11 抽 mission while 迴圈、L27 抽協定，兩者正交、互不干擾）。

**概念**：契約優先（contract-first）：把 13 種 action 的合法值、欄位（`distance` 預設 0.5m / `degrees` 預設 30°）、body-frame→world 旋轉、geofence(±3m, 0.3–2.5m) 定義成一個與模擬器無關的純資料 + 純函式模組，並產出一份機器可讀 JSON Schema 給未來 Apple guided generation 直接吃。

**動手做（交付物）**：
- `nanodrone/protocol.py`：(a) `ACTIONS` 常數表 + `DEFAULT_DIST=0.5` / `DEFAULT_DEG=30`；(b) `validate(cmd)->(ok, reason)` 純函式（擋未知 action、負距離、NaN）；(c) 把 `sim_server.py` 現有 `apply_command(cmd, target, yaw)` 原封不動搬進來成 `step_target(cmd, target, yaw)->(yaw, mode)`；(d) `schema()->dict` 吐 JSON Schema。
- 改寫 `bridge/sim_server.py` 改 import 這支（行為不變）；`send.py` 的 `TURNS` 集合改 import protocol。
- `--selftest` 印 `PROTOCOL OK: 13 actions, validate rejects 4 bad cmds, schema valid, sim_server behaviour unchanged`。assert 合法／非法判定正確、schema 自洽。

**驗收 ✅**：`PROTOCOL OK` 綠燈、`sim_server` 行為回歸測試通過。

**延伸**：JSON Schema 直接生成 DroneVoice 的 Swift 端契約文件（Phase 2/3）。

**重用**：直接搬 `sim_server.py` 的 `apply_command`（含 `c,s=cos/sin yaw` 的 body→world 數學、`np.clip` 的 `BOX_XY=3.0`/`BOX_Z=(0.3,2.5)` geofence、land/emergency 的 mode 回傳）；常數 `START`/`DEFAULT_DIST`/`DEFAULT_DEG`/`BOX_XY`/`BOX_Z` 從 `sim_server.py` 搬出。誠實標示：此前協定沒有獨立可測 schema 模組，這是真正的新模組。

---

### [Lesson 28] 招牌反例對照組的量化擂台：自訓小模型 vs 通用大模型 + 結構化約束（Track C）

- **成本** $0 可完課（A/B backend 純 CPU）；選配本地 instruct 模型 backend C 需額外下載（標註選配，非完課必要）｜**難度** 中等｜**前置** L27、L12（adapter 概念）、L10（KWS 固定詞表）

**為什麼**：DroneVoice Phase 3 被定位為招牌主題的「反例對照組」。**這課把它做成可量化、離線、$0、CI 可跑的擂台**，讓數據說話，而不是只用嘴講。前面 L3/L8/L10/L13/L17 都在講「通用不夠好→自訓小模型」；這課反過來逼問：當任務是「把彈性自然語句轉成結構化指令」時，自訓固定詞表 KWS（L10）反而是錯的工具，通用大模型 + guided generation（強制吐合法 schema）才是對的。Apple Foundation Model 只是這擂台的其中一個 backend；沒 iPhone 的人用 Python backend 就能跑完整堂課。這也先於、並支撐 Phase 3。

**概念**：用「意圖解析準確率 + schema 合法率 + 涵蓋率 + 硬體／離線成本」四軸做對照表。backend 介面統一成 `parse(text)->cmd|None`：backend A = 規則解析（雙語關鍵字 + 數量詞抽取，沿用 L9 `_CMDS` 思路；「往前兩公尺」→`{action:forward,distance:2.0}`）、backend B = L10 KWS 風格固定詞表分類器、backend C = guided-generation（Python 端用本地小型 instruct 模型或 stub 約束解碼示範「強制吐合法 JSON」的概念，Apple 端對應 `@Generable`）。重點教學：guided generation 為何能保證 schema 永遠合法（解碼時只允許 grammar 內 token）。本課也把「規則解析器」收進來當 backend A，放進「vs 通用大模型」的對照脈絡裡，而非單獨成課。

**動手做（交付物）**：
- `bridge/parse_text.py`：`parse_text(s)->cmd|None`（雙語、抽數字 + 單位 公尺／米／度／degree）當 backend A。
- `bridge/send_text.py`：把一句話解析成 JSON 再走既有 socket 送出（沒 iPhone 的人的「語音替身」，也是 Phase 2 的無 iPhone 等價驗收工具）。
- `bridge/golden_intents.jsonl`：約 40 句中英混（含複合／同義／數量詞）黃金測資。
- `bridge/eval_parsers.py`：對每個 backend 算四軸分數印對照表。
- `--selftest` 用 A、B 兩個離線 backend（C 在沒模型時自動 SKIP），印 `EVAL OK: ruleA acc=0.78 schema=1.00 | kwsB acc=0.55 | covered 40 phrases`。assert「B 固定詞表在彈性句上的 acc 明顯低於 A」「所有產出都過 `protocol.validate`」。

**驗收 ✅**：`EVAL OK` 綠燈（B<A 的 acc 差距 assert 通過）。

**延伸**：backend C 換成 Apple Foundation Model 即 Phase 3；對照表直接當 Phase 3 docs 的反例證據。

**重用**：L27 `protocol.validate` 當所有 backend 的合法性裁判；L9 `voice.py` 的 `_CMDS` 雙語關鍵字表與「longer/turn/land 先比對」順序當 backend A 基底（加數量詞抽取）；L10 `kws.py` 的 `make_net` + `LABELS/COMMANDS`「固定詞表分類器」概念當 backend B（用文字 token 而非 MFCC，沿用「固定類別 + argmax + 信心門檻」思路）；`bridge/send.py` 的 `socket.create_connection` 送出邏輯。

---

### [DroneVoice Phase 2]（並行選修支線）iPhone 語音入口：App Intents + on-device 聽寫送 JSON（Track C）

- **成本** 軟體 $0｜**需硬體／環境**：支援 Apple Intelligence 的 iPhone（A17 Pro 以上）或 iOS 26 模擬器 ＋ Mac 上 Xcode；無需買無人機（仍打 sim）；無 iPhone 者用 L28 `send_text.py` 等價驗收｜**前置** L27（協定）、L9（雙語關鍵字解析）

**為什麼**：phase 1 已完成 sim server，但目前只能用 `send.py` 假裝成 app。產品故事下一步是真的從 iPhone 講話。這課對應「Apple 版的 L9」：麥克風→文字→關鍵字最簡解析→送既有 JSON 協定，讓使用者第一次「對 iPhone 講話、看 sim 裡的無人機照做」。JSON 協定是穩定 contract，server 完全不改。

**概念**：iOS 端用 `SpeechAnalyzer`/`DictationTranscriber`（iOS 26 on-device，短指令最合適、中英；舊裝置退回 `SFSpeechRecognizer`）做語音轉文字，用一張對照表（移植 L9 `parse_command` 雙語關鍵字思路與 `background` 拒絕類別防誤觸發）把文字映成 13 種 action 之一，序列化成 bridge 的 newline JSON 經 TCP 送出。action enum 與欄位以 L27 `protocol.schema()` 為單一事實來源（而非硬抄 `sim_server.py`）。定義 App Intents（`TakeoffIntent` 等）讓 Siri／捷徑也能觸發。

**動手做（交付物）**：`DroneVoice/` iOS 專案：麥克風→文字→JSON 送到 `sim_server`。驗收器改用 L27 `protocol.validate` / `protocol.schema()` 當單一事實來源：app 送出的位元組需與 `send.py`（或 L28 `send_text.py`）對同句指令的 JSON 逐欄相符。新增 `bridge/validate_protocol.py --selftest` 餵 app 錄下的指令序列進 `protocol.validate`，印 `PROTOCOL OK: 12/12 app commands parsed, schema valid, matched send.py`。assert 全數合法。

**驗收 ✅**：`PROTOCOL OK` 綠燈；app 輸出與 `send.py` 逐欄一致。無 iPhone 者以 `send_text.py` 等價驗收。

**延伸**：預告 Phase 3 自然語句解析。

**重用**：`bridge/sim_server.py` 的 `serve()` wire 協定（不改）與 L27 `protocol` 模組；`bridge/send.py` 當協定對照組與回歸基準；L9 `parse_command` 雙語關鍵字表當 app 端詞庫與 fallback；L10 `background` 拒絕類別思路防語音誤觸發。

---

### [DroneVoice Phase 3]（並行選修支線）on-device LLM 解析自然語句：Foundation Models guided generation（招牌主題的反例對照組）（Track C）

- **成本** 軟體 $0｜**需硬體／環境**：同 Phase 2；Foundation Models 需 iOS 26 且裝置支援 Apple Intelligence｜**前置** DroneVoice Phase 2、L27、L28

**為什麼**：Phase 2 關鍵字解析只能聽懂固定詞；產品真正想要的是「往前飛兩公尺再左轉九十度」這種自然語句。**這課在 docs 裡明確定位為課程招牌主題的「反例對照組」**：與 L8/L10/L13「訓你自己的小模型」並排對比——這次不必自訓，改用 Apple on-device ~3B Foundation Model ＋ guided generation，靠 constrained decoding 保證直接吐 schema 正確的結構化指令。教學點是判斷力：**何時該訓自己的小模型（資料專屬、邊緣部署、要塞進 GAP8），何時通用大模型＋結構化約束就夠（自然語言解析、有現成 on-device 框架）**。若沒框成對照組，會被讀成「其實不用訓模型」而稀釋整門課論點，故 README 須明說這個對比。

**概念**：用 Foundation Models framework 定義 `@Generable struct DroneCommand { action: enum(13 種，對齊 bridge); distance: Double?; degrees: Double? }`，`LanguageModelSession` 把自然語句 guided-generate 成保證落在 enum 內、型別正確的物件，序列化成 bridge JSON。`@Generable` 的 enum 與欄位由 L27 `protocol.schema()` 生成而非手抄。保留 Phase 2 的 L9 關鍵字表當 LLM 不可用／解析失敗時的 fallback（呼應 L9/L10 拒絕類別精神：不確定就不亂飛）。

**動手做（交付物）**：DroneVoice app 升級：自然語句→`@Generable DroneCommand`→JSON。驗收以 bridge 為真理：把一組自然語句測例（含多步、中英）跑出的 JSON 餵進擴充後的 `bridge/validate_protocol.py --selftest`，印 `NL-PARSE OK: N/N phrases -> valid commands, all actions in 13-enum, distances within geofence`。assert 全部 schema 合法且落在 geofence。本 Phase 的量化證據直接引用 L28 `eval_parsers.py` 的對照表（backend C = Foundation Model）。

**驗收 ✅**：`NL-PARSE OK` 綠燈。**注意**：CI 只能驗 JSON schema 正確性，無法驗 on-device LLM 行為品質——後者需在實機人工抽驗。

**延伸**：Phase 4（SwiftUI + 雙向遙測 + app 端 failsafe / 危險指令確認 / geofence UI 預視）、Phase 5（sim→真機，Tello DJITelloPy 先、Crazyflie cflib 收束）。

**重用**：Phase 2 的 app 與送 JSON 管線；L27 `protocol.schema()` 的 13-action schema 當 `@Generable` enum 來源與驗證標準；L9 `parse_command` 當 LLM fallback；`bridge/validate_protocol.py` 驗收器（Phase 2 建立）；L28 `eval_parsers.py` 對照表當反例證據。

---

### [DroneVoice Phase 4]（並行選修支線）SwiftUI App：連線設定、指令記錄、緊急停止、雙向遙測、app 端 failsafe（Track C）

- **成本** 軟體 $0（無 iPhone 路線驗收 server 端遙測／急停／確認協定）｜**需硬體／環境**：iPhone + Mac + Xcode（有 iPhone 路線）｜**難度** 進階｜**前置** L27（協定）、Phase 3、L23（遙測格式）、L4/L24（failsafe 概念與 `nanodrone/safety.py`）

**為什麼**：把語音入口包成真正能用的 app：人要看得到無人機在哪（遙測）、要能一鍵急停、要在危險指令前被攔下確認、要看到 geofence。這課把 L4 真機 bring-up 的三段 failsafe 哲學（電量門檻、geofence、例外即降落）與 L24 抽出的 `nanodrone/safety.py` 搬到 app UI 層，並讓 sim_server 回傳遙測。沒 iPhone 的人驗收的是「server 端新增的遙測 + 危險指令確認協定」，用 `send.py` 就能戳。教學點：**UI 不是裝飾，是 failsafe 的一部分。**

**概念**：人機安全介面：(a) 雙向協定——server 在每次指令後回傳一行 telemetry JSON（x/y/z/yaw/是否觸 geofence 邊），格式沿用 L23 `nanodrone/telemetry.py`；(b) app 端 failsafe——`emergency_stop` 鈕直送 `{action:emergency_stop}`，land/down 等危險指令前彈確認；(c) geofence 視覺化。server 端對「無 takeoff 就 forward」之類不安全序列回拒絕回應（用 L27 `protocol.validate` 當裁判）。

**動手做（交付物）**：
- 擴充 `bridge/sim_server.py`：每處理一條指令後回傳 telemetry JSON（沿用 `env._getDroneStateVector(0)`，並接 L23 `FlightLogger` 格式），新增對不安全序列的拒絕回應。
- 新增 SwiftUI app：連線設定頁 / 指令 log（接 L23 jsonl 概念）/ 紅色 EMERGENCY STOP 鈕 / 遙測讀數 / geofence 框。
- `--selftest`（在 sim_server）擴充後印 `BRIDGE OK: telemetry sent N frames, refused 1 unsafe cmd, emergency froze drone`。assert 急停後位置不再變、遙測幀數 >0、不安全指令被拒。

**驗收 ✅**：`BRIDGE OK`（含遙測幀數、拒絕、急停凍結三項 assert）綠燈。無 iPhone 者以此為等價驗收。

**延伸**：把 app 端 pre-flight 確認頁接 L26 `preflight_check.py`；遙測讀數接 L23 回放做「飛後檢討」。

**重用**：`sim_server.py` 的 `env._getDroneStateVector(0)[0:3]` 取狀態當遙測來源、緩降 land 邏輯；L4 `fly_crazyflie.py` 的三段 failsafe 思想（battery gate→危險指令確認、geofence→已在 L27、exception→emergency）對映到 app；L24 `nanodrone/safety.py` 的 `decide_failsafe` 當 server 端安全裁判；L27 `protocol.validate` 當拒絕不安全指令的裁判；L23 `telemetry.py` 的 JSON 格式當遙測 wire 格式。

---

### [DroneVoice Phase 5a]（並行選修支線）Tello over Wi-Fi：AI 機外、非離線（Track C）

> Phase 5 分兩棒：**5a Tello（先，最低風險）→ 5b Crazyflie（收束，回到課程終點）**。兩者協定（L27）、語音（Phase 2/3）、app（Phase 4）一個字都不改，只換 controller 後端。

- **成本** **硬體：DJI Tello 約 US$100** + 一台能連 Tello Wi-Fi 的電腦（無 Apple Intelligence/A17 需求）；無硬體 $0（FakeTello selftest 全程可跑）｜**難度** 進階｜**前置** L27、Phase 4、**L24（直接重用 `TelloBackend`）**｜新套件 `djitellopy`

**為什麼**：phase 5 第一棒。Tello 最便宜、Wi-Fi、DJITelloPy 成熟，是「同一份 JSON 協定、只換 controller 後端」最低風險的真機示範。重點教學：你前面所有課（L27 協定、Phase 2 語音、Phase 4 app）一個字不用改，只把 sim_server 的「PyBullet 後端」換成「Tello 後端」。**誠實標注**：Tello 的 AI 在機外、非離線，不是最終目標——它是「協定可攜性」的證明與安全的真機第一步。

**概念**：後端抽換（backend swap）：把 L27 `step_target` 語意對映到 DJITelloPy 的 `takeoff`/`move_forward`/`rotate_clockwise`/`land`；body-frame 與 geofence 規則沿用 L27；Tello 專屬 failsafe（電量 % 門檻、低電拒飛、連線丟失自動 land）走 L24 `nanodrone/safety.py`。**本 Phase 與 L24 的分工**：L24 已建 `TelloBackend` 與 safety；Phase 5a 是把它接到 9000 埠的 TCP server，讓 Apple app（Phase 4）直接驅動真 Tello——也就是「app→真機」端到端串通。

**動手做（交付物）**：
- `hardware/tello_server.py`：監聽同一個 9000 埠、收同一份 newline-JSON，用 L24 `TelloBackend` + `djitellopy` 飛真機；`distance(m)→cm`、`degrees→rotate`。
- `--selftest`（無 Tello 時用 FakeTello stub）印 `TELLO-SERVER OK: served N protocol cmds -> [takeoff, forward 100cm, cw 90, up 50cm, land], battery-gate enforced, app-equivalent`。assert 每條 protocol 指令映射到合法 Tello 呼叫、未連線不真起飛、與 Phase 4 app 送的位元組一致。

**驗收 ✅**：`TELLO-SERVER OK` 綠燈；端到端（app→tello_server→FakeTello）一致性 assert 通過。

**延伸**：換 controller 即 Phase 5b Crazyflie。

**重用**：`bridge/sim_server.py` 的 `serve()` socket/newline 拆解迴圈整段（協定接收層完全不動）；L24 `TelloBackend` 與 `nanodrone/safety.py`；L27 `protocol.validate` + `ACTIONS` + body-frame 數學決定對 Tello 下什麼；FakeTello stub 沿用 `SelftestInput` 樣板。

---

### [DroneVoice Phase 5b]（並行選修支線）Crazyflie 離線自飛：回到課程終點（Track C）

- **成本** **硬體：Crazyflie 2.x + Crazyradio（+ 選配 AI-deck）≈ 課程既有約 US$545 bundle 內**；需室內淨空飛行場；無硬體 $0（FakeCrazyflie selftest）｜**難度** 進階（全線最高）｜**前置** L27、Phase 4、L4（cflib/MotionCommander/三段 failsafe）、L22（板上 reflex 敘事，選用）｜新套件 `cflib`

**為什麼**：phase 5 收束，也是整個 nanodrone-ai 的終點呼應：離線、板載、<512KB int8 的真實 Crazyflie。把 DroneVoice 產品線與課程主線（L3 自訓 CNN→L4 GAP8 量化→L17–L22 板載深化）接回來——語音／app 是「高階指令入口」，但真正的離線自主（避障）仍是跑在機上的小模型。Crazyflie 走 cflib，協定同樣不變。**誠實標注**：這是全線最高難度、需最完整硬體與飛行場地。

**概念**：雙層架構的最終形：app／語音送高階 setpoint（L27 協定）→ host 端 cflib 把 setpoint 餵給 Crazyflie 板上 PID（馬達混控）；同時板上 GAP8 跑量化後的避障 CNN（L4 量化 / L22 統一策略）做離線 reflex。教學點：兩條控制路徑（人類高階意圖 vs 板上即時 reflex）如何安全共存與優先序（reflex 永遠優先於高階意圖，呼應 L13 的事件優先序表）。

**動手做（交付物）**：
- `hardware/crazyflie_server.py`：同 9000 埠、同 JSON，用 cflib `SyncCrazyflie` + `MotionCommander` 飛真機，safety 沿用 L4 + `nanodrone/safety.py`。
- `--selftest`（無硬體用 FakeCrazyflie stub）印 `CF-SERVER OK: mapped protocol cmds -> motion_commander calls, battery-gate + commander-always-lands enforced`。assert 例外路徑一定觸發 land、未連線不起飛。
- README 一段說明如何與 L4 GAP8 板載避障模型（或 L22 統一策略）併行：高階 setpoint vs 板上 reflex 優先序。

**驗收 ✅**：`CF-SERVER OK` 綠燈；例外必降落、未連線不起飛 assert 通過。

**延伸**：把 L22 統一 int8 策略燒進 AI-deck 當板上 reflex，達成「app 高階意圖 + 板上離線自主」的最終 demo——整個課程在此收束。

**重用**：L4 `fly_crazyflie.py` 整支的 cflib 連線／`read_battery`/MotionCommander「進入即起飛、退出／例外必降落」三段 failsafe 當 controller 基底；`sim_server.py` `serve()` 接收層；L27 protocol 把 JSON 對映成 `MotionCommander.forward/turn/up/land`；L4 `quantize_cnn.py`（或 L22）產出的 <512KB ONNX 當「板上 reflex」敘事（不重做量化，只接回來）；`nanodrone/safety.py`；FakeCrazyflie stub 沿用 `SelftestInput`。

---

## 五、總表

> **必修／選修標示**：★ = 核心必修主線；◆ = 進階分支（對「想真的上板／落地」是核心，對只想跑完 sim 主線者選修）；○ = 並行選修（需特定硬體／平台）。

| 編號 | 標題 | 軌道 | 類別 | 成本 | 難度 | 依賴 |
|---|---|---|---|---|---|---|
| L11 | 任務編排骨幹：飛行迴圈→狀態機 + Failsafe | A 編排 | ★ | $0 | 中等 | L5、bridge phase 1 |
| L12 | 語音驅動狀態轉移（source→event adapter） | A 編排 | ★ | $0 | 中等 | L11、L9、L10 |
| L13 | 多模態 mini-capstone：找人→跟隨→land（含再訓確認分類器） | A 編排 | ★ | $0 | 進階 | L11、L12、L8 |
| L14a | 簡單建圖與自主巡邏（`nanodrone.map`） | B 板載／感知 | ★ | $0 | 進階 | L11、L2 |
| L14b | 板載預算下的感知排程與量化（縫回 GAP8） | B 板載／感知 | ★ | $0（真機選配 ~US$545） | 進階 | L14a、L4、L13 |
| L16 | 畢業專題與評分標準（host-side capstone） | A 編排 | ★ | $0（真機選配） | 進階 | L11、L12、L13、L14a、L14b |
| L17 | 單目深度估計 CNN（第一次訓 dense 模型） | B 板載／感知 | ◆ | $0 | 中等 | L2、L3、L4 |
| L18 | 光流 / 視覺里程計：無 GPS 自估狀態 | B 板載／感知 | ◆ | $0（真機選配 Flow deck ~US$45） | 中等 | L1、L3、L8、L4 |
| L19 | 多障礙 RL 賽道（餵感知、會泛化） | B 板載／感知 | ◆ | $0 | 進階 | L3、L17 |
| L20 | 域隨機化：縮小 sim-to-real 落差 | B 板載／感知 | ◆ | $0 | 中等 | L17、L2 |
| L21 | 知識蒸餾 + 模型壓縮（延伸 L4 量化） | B 板載／感知 | ◆ | $0（硬體沿用 L4，不重計） | 進階 | L4、L17、L20、L3 |
| L22 | 多能力蒸餾成單一板載策略（板載 capstone） | B 板載／感知 | ◆ | $0 | 進階 | L8、L19、L21、L4 |
| L23 | 飛行黑盒子：遙測記錄與離線回放 | E 真機落地 | ◆ | $0 | 入門 | L1、bridge phase 1 |
| L24 | 平價 Tello 真機踏腳石（抽出 `nanodrone/safety.py`） | E 真機落地 | ◆ | 需 Tello ~US$100（FakeTello CI $0） | 進階 | L23、L11、bridge phase 1 |
| L25 | sim-to-real 落差量測 | E 真機落地 | ◆ | $0（拍真機需 L24 Tello） | 進階 | L8/L3、L18、L24 |
| L26 | 實地測試 SOP + 台灣法規 | E 真機落地 | ◆ | $0（真機選配） | 中等 | L23、L11/L24、L24 |
| L27 | 協定抽取 `nanodrone.protocol`（償還協定債） | C Apple | ◆ | $0 | 入門 | bridge phase 1 |
| L28 | 解析評測擂台（反例對照組量化地基） | C Apple | ◆ | $0（backend C 選配） | 中等 | L27、L12、L10 |
| DroneVoice Phase 2 | iPhone 語音入口（App Intents + 聽寫→JSON） | C Apple | ○ | 軟體 $0（需 iPhone/Xcode） | 中等 | L27、L9 |
| DroneVoice Phase 3 | on-device LLM 解析（反例對照組） | C Apple | ○ | 軟體 $0（需 iOS 26 + Apple Intelligence） | 進階 | Phase 2、L27、L28 |
| DroneVoice Phase 4 | SwiftUI app + 雙向遙測 + app failsafe | C Apple | ○ | 軟體 $0（需 iPhone/Xcode） | 進階 | L27、Phase 3、L23、L4/L24 |
| DroneVoice Phase 5a | Tello over Wi-Fi（AI 機外，協定不變換 controller） | C Apple | ○ | 硬體 ~US$100（FakeTello CI $0） | 進階 | L27、Phase 4、L24 |
| DroneVoice Phase 5b | Crazyflie 離線自飛（回到課程終點） | C Apple | ○ | 硬體 ≈ L4 ~US$545（FakeCrazyflie CI $0） | 進階 | L27、Phase 4、L4、L22 |

### 編號邏輯說明

- L11–L16 主幹維持原排序與依賴圖；**L15 刻意空號**（swarm 已降級為 Track D 純文件 going-further，不佔課程編號，亦不復用此號以免與「被砍的 swarm」混淆）。L14 拆成 L14a（建圖）/ L14b（板載收斂）兩課以容納補上的板載缺口。L16 維持畢業專題的「最後一課」象徵編號。
- 感知深化、真機落地、Apple 產品線三條深化線一律用 **L17 起的連續新號段**，不插號進 L11–L16（避免擾動已穩定的依賴圖）。
- Phase 4/5 維持「Phase」命名（與 phase 1–3 一致，標示為 bridge 支線而非主線 Lesson）。

## 六、設計取捨：哪些點子合併、為何砍掉 swarm

1. **Failsafe 不另開課，抽成 `nanodrone/safety.py`**。L11 已內建 `Failsafe` 狀態（先 Hover、逾時 Land），且全程貫穿、被 L16 rubric 列為硬門檻。處理方式是在 **L24（第一次碰真機、failsafe 第一次真正攸關安全）把 L11 的 Failsafe 抽成可單元測試、可注入故障的 `nanodrone/safety.py`**，並被 L26、Phase 4、Phase 5 共用——既滿足「failsafe 要能在 sim 注入故障驗證」的訴求，又不和 L11 重複造一門狀態機課。

2. **規則解析器不另開課，併入 L28 評測擂台當 backend A**。L12 已建 source→event adapter（鍵盤／語音／KWS→事件）。把「規則解析器」放進 **L28「vs 通用大模型」的對照脈絡**裡，比單獨成課更有教學張力；無 iPhone 等價驗收工具 `send_text.py` 附在 L28 交付物。

3. **兩條光流提案合併成單一 L18**。古典光流（cv2，講原理 + 真機需 Flow deck）與「訓小 CNN 回歸速度」兩個角度合而為一：以「訓你自己的小 CNN（特權標籤）」為主線（符合招牌主題），同時納入古典光流原理對照與「真機需 Flow deck v2 ~US$45、會漂移」的誠實標注。不開兩門光流課。

4. **多障礙 RL（L19）不重造場景**。L14a 已為建圖巡邏自帶多柱場景 builder（並如實標為新增、非復用 L3）。L19 **直接復用 L14a 的多柱 `scene.py`**，只新增「把感知（L17 depth）併入 RL 觀測 + curriculum」這層——這是 L14a 沒做、且 `avoid_aviary` 註解明確點名的真缺口。

5. **三個 capstone 分工清楚、不重複**：**L16** 是 host-side「用 mission 積木編排」的畢業專題；**L22** 是「把多能力壓成單一 int8 網路」的板載技術 capstone；**Phase 5b** 是「app 高階意圖 + 板上離線 reflex」的產品線收束。三條主線各自的終點，互為延伸而非重複。

6. **砍掉 swarm（原 L15 提案）**。雙機 swarm 與終極「單機板載自主」關聯最弱、重構面最大、維護成本最高、對招牌主題零貢獻，**降級為純文件型 going-further（Track D），不成課、不佔編號**。它若回頭拆 L11 地基或拖累畢業節奏，代價不值。為保留延伸彈性，L11 `mission runner` 仍**不寫死 `num_drones`**，但不為它開課。

7. **修正浮誇 reuse**。建圖巡邏（L14a）的 occupancy-grid 與多障礙場景 builder 如實標為**新增能力**（L3 只有一根柱子且綁在 RL 專用 `AvoidAviary`，不可重用），並抽到 `nanodrone.map` 供後續共用。所有新增深度／光流／DR 課的「上採樣 head、scale-invariant loss、整張影像運算、噪音／randomization」等都逐一標明是 sim 第一次用到，不假裝沿用。

## 七、風險與取捨備註

**Jan 2026 後有變動風險的技術（全集中在 Track C Apple）**：

- **Apple Foundation Models framework**（Phase 3）：需 iOS 26 + Apple Intelligence + A17 Pro/M 系列。API 仍在演進，`@Generable` 對「大 enum + 多語自然語句」的解析穩定度需實機實測；GA 狀態、硬體門檻清單、繁中 on-device 模型支援廣度都可能隨新機種／新 OS 更新。**動工前務必再上 Apple Developer 文件核對。**
- **SpeechAnalyzer / DictationTranscriber**（Phase 2）：iOS 26 新 API，繁中 on-device 模型的離線下載狀態需查證；舊裝置退回 `SFSpeechRecognizer` 的雙路徑要測。
- **iOS 27 / 2026 WWDC** 可能再調整這些 API 名稱或新增 streaming/tool-use 能力。
- **風險隔離**：L27 把協定抽成單一事實來源後，Apple API 風險被進一步隔離在「換語言重跑同一份 schema／黃金測資」這一層——L28 的 Python backend 與 `send_text.py` 讓沒 iPhone 的人 100% 等價完課，Apple 端任何 API 變動都不影響「課程能否完成」。

**硬體成本（全部誠實標注、CI 皆 $0 可跑）**：

- 核心主線 Track A 與 Track B（含 L17–L22）的 sim 部分**全程 $0、純 sim、CI 不需任何硬體**（含麥克風——L12/L13 與所有真機課用腳本化事件／FakeXxx stub 注入）。
- **L24 / Phase 5a：DJI Tello 約 US$100**（DJITelloPy/Wi-Fi、AI 在機外、非離線——最快出真機 demo，但**明說不是課程終點**）。FakeTello stub 讓 CI $0。
- **L18 真機光流：Crazyflie Flow deck v2 約 US$45**（非本課強制，純 sim 學原理）。
- **L14b / L21：沿用 L4 既標約 US$545 AI bundle，不重複計費。**
- **Phase 5b：Crazyflie ≈ L4 ~US$545 bundle 內**（全線最高硬體 + 場地門檻）。FakeCrazyflie stub 讓 CI $0。
- L25 拍自己的真機落差需 L24 Tello，無 Tello 用內附樣本影片仍可完課。
- Track C 另需一台支援 Apple Intelligence 的 iPhone（A17 Pro 以上）或 iOS 26 模擬器 + Mac/Xcode。

**維護成本**：

- Track C 整體維護成本最高——依賴 Apple 平台版本、CI 無法真正驗 on-device LLM 行為（只能驗 JSON schema）。**因此標為並行選修、與主線完全解耦**：JSON 協定是穩定 contract，Track A/B 不受 Apple API 變動影響。L27 協定抽取 + L28 評測擂台把風險再壓低一層。
- **L11 `nanodrone/mission.py` 與 L27 `nanodrone/protocol.py` 一旦成為地基，任何 API 變動都可能悄悄弄壞下游**（mission 影響 L12–L16/L23；protocol 影響 L24/Phase 2–5）。**必須在 `.github` 建一個跨課整合 CI**（不只各課自己的 `--selftest`），覆蓋 `mission`/`protocol`/`safety`/`telemetry` 四個共用模組，在 API 變動時即時抓出回歸。
- Track B 新課全部 sim 自產資料、`--selftest` 收斂，維護成本低；唯 L19 RL 與 L21/L22 蒸餾訓練時間較長，CI 用少步數冒煙測試（不在 CI 跑完整訓練）。

**最關鍵的策略取捨**：把課程從「更聰明的桌面模擬編排」拉回「板載／離線／真機自主」招牌，靠這幾條主線完成：(1) **L14b** 把編排能力縫回 GAP8/int8/<512KB；(2) **L13** 強制再訓一個確認分類器，讓「訓你自己的模型」主題在 capstone 前再現；(3) **L11 內建 Failsafe**、**L16 把板載考量與 failsafe 列入 rubric 硬門檻**，並在 docs 顯式交代主題轉折弧與 Phase 3 反例對照；(4) **Track B 的 L17→L18→L20→L21→L22** 把「模擬器閒置能力 → 自訓 dense／光流小模型 → 抗 sim-to-real → 壓進 512KB → 多能力合一上板」走完整條，讓「訓你自己的小模型」主題從「再現一次」升級為「貫穿到底」；(5) **新增 Track E（L23–L26）** 把「sim-first 基礎設施 → 平價真機踏腳石 → 量測落差 → 合法安全飛」做實，正面回應「誠實對待 sim-to-real」原則。**砍掉的 swarm 維持降級**，不復用其編號、不回頭拆地基。

---

相關既有程式路徑：`bridge/sim_server.py`、`bridge/send.py`、`nanodrone/{detect,input,view}.py`、`lessons/0[1-9]_*` 與 `lessons/10_*`。Track A 新增模組落在 `nanodrone/{mission,mission_events,map}.py`。其餘新增模組建議落在 `nanodrone/{protocol,telemetry,safety,degrade}.py`、`lessons/{17_depth,18_flow,19_multi_avoid,20_domain_rand,21_distill,22_unified,23_telemetry,24_tello,25_sim2real,26_field_test}/`、`bridge/{parse_text,send_text,eval_parsers,golden_intents.jsonl}`、`hardware/{tello_server,crazyflie_server}.py`、`apple/DroneVoice/`。

---

## 附錄 A — Track A 開工規格（對齊已實作的 `nanodrone.mission`）

> L11 **已實作並通過驗收**（`lessons/11_mission/mission_demo.py --selftest` 印出
> `MISSION OK …` 與 `FAILSAFE OK …`，已寫進 CI）。本附錄把 Track A 後續課的 outline
> **下沉到「對著真實 API 開工」的深度**，所有簽名以 `nanodrone/mission.py` 實際落地的版本為準
> （與前面 outline 的描述若有出入，以這裡為準）。

### A.0 已實作的 `nanodrone.mission` API（L12–L16 的地基）

```python
from nanodrone.mission import (
    State, Mission, Takeoff, Hover, GoTo, Land, Failsafe,
    in_fence, clip_to_fence,            # geofence 純函式
    FENCE_XY, FENCE_Z, HOVER_HEIGHT, LAND_HEIGHT,   # 常數
)
```

- **`State`**（子類化即可擴充）：`on_enter(m)` 進入時呼叫一次（常設 `m.target`）；
  `step(m) -> (target_pos, yaw)` 每幀回傳想要的高階 setpoint；`is_done(m) -> bool` 何時換下一階段。
  狀態從 `m` 讀即時狀態，**不碰馬達**。
- **`Mission(states, *, start=(0,0,0.1), gui=False, fence_xy=FENCE_XY, fence_z=FENCE_Z, failsafe=None)`**：
  - `.run(max_seconds=20.0) -> dict`，dict 欄位：`history`(進入過的狀態名 list)、`steps`、
    `moved`(起點到終點水平位移)、`final_z`、`in_failsafe`、`failsafe_reason`、`landed`。
  - `.request_failsafe(reason: str)`：任何時候丟進 Failsafe（失聯／越界／感知逾時）。
  - 迴圈每幀自動做 geofence watchdog：任何狀態想離開安全框 → 自動 `request_failsafe("geofence")`。
  - 即時屬性供狀態讀：`m.pos`(np3)、`m.yaw_now`、`m.target`、`m.yaw`、`m.dt`。runner 索引 `obs[0]` 但未把 `num_drones` 寫死進迴圈本體。
- 內建狀態：`Takeoff(height=1.0)`、`Hover(seconds=1.0)`、`GoTo(xyz, face=False, tol=0.12, safe=True)`、
  `Land()`、`Failsafe(hover_seconds=0.5)`。`GoTo(..., safe=False)` 可故意請求越界點以演示 watchdog。

> **L12–L16 對地基的小幅擴充（建議一次補齊）**：新增公開方法
> `Mission.go(state)`（立刻進入任意 State，供事件驅動跳轉，內部即 `_enter`），
> 以及在 `run()` 接受一個可選的 `event_source`（每幀 `poll() -> event|None`）。
> 這兩點讓 L12 的「事件→轉移」與 L13 的「感知丟失→重捕」不必再抄迴圈。

### A.1 [Lesson 12] 語音驅動狀態轉移 — 開工規格

- **新檔 `nanodrone/mission_events.py`**：一層 source→event adapter（三個來源輸出型別不同，必須轉接）：

  | 來源 | 原始輸出 | adapter | mission event |
  |---|---|---|---|
  | L9 `voice.parse_command` | `(fwd,strafe,up,yaw)` / `'land'` / `None` | `'land'`→land；全零/None→（不發） | `takeoff`/`land`/`stop`… |
  | L10 `kws_fly.KwsListener.poll()` | `(label, conf)` | `conf>0.6` 才採信；`background`→不發 | 離散 label→event |
  | bridge `protocol.step_target`（L27 後） | mode | `'land'`→land、`'emergency'`→stop | `land`/`stop` |

  並含一張 `EVENT_TO_STATE = {"takeoff": Takeoff, "hover": Hover, "land": Land, ...}` 表
  （沿用 L9 `_CMDS` 的「長詞優先」與 L10 `background` 拒絕思路）。
- **新檔 `lessons/12_voice_mission/voice_mission.py`**：用 `Mission` + `event_source`，事件到就 `m.go(EVENT_TO_STATE[ev]())`；`emergency`/`land` 走最高優先。語音線程用 `KwsListener.poll()` 非阻塞。
- **`--selftest`**（無麥克風，注入時間戳事件序列，復用 L9 `ScriptedVoice` 手法）印：
  `VOICE-MISSION OK: events=[takeoff,hover,land] transitions=3, ended in Land, landed, 1 noise-event rejected`。
  assert：轉移次數正確、終態 Land、`landed`、且注入的 `background`/低 conf 雜訊事件**未**觸發轉移。
- **重用**：L11 `Mission`/`Takeoff`/`Hover`/`Land`/`go()`；L9 `parse_command`/`ScriptedVoice`；L10 `KwsListener.poll()` + `conf>0.6` 門檻 + `background` 拒絕類別。

### A.2 [Lesson 13] 多模態 mini-capstone（找人→跟隨→land）— 開工規格

- **新檔 `lessons/13_find_follow_land/train_confirm.py`**：sim 自產「目標人 vs 背景」資料 + 訓 tiny CNN 確認器（沿用 L8 `gen_person_dataset`/`train_person_cnn` 套路）。`--selftest` 印 `CONFIRM-CNN OK: trained N samples, val acc>0.9`。
- **新增兩個 `State` 子類**（放在 lesson 內或 `nanodrone/mission.py`）：
  - `Search(State)`：`step` 緩慢遞增 `m.yaw`、保持高度；每 `PERCEPTION_EVERY` 幀跑 L8 `cnn_bearing`；
    `is_done` = 偵測命中 **且** 距離`<MAX_RANGE` **且** 確認 CNN 判定=人。逾時 `T_search` 則 `m.request_failsafe("search_timeout")`。
  - `Follow(State)`：`step` 用 L8 `world_point`/`depth_at_bearing` 算 `target` 與 `m.yaw`（收斂到 `DESIRED_DIST`）；
    連續 `N=8` 幀丟失 → `m.go(Search())` 重捕。
- **事件優先序（硬規定）**：`land`(語音/emergency) > `Failsafe`(失聯/越界) > 視覺轉移(Search↔Follow) > 連續控制。
- **新檔 `lessons/13_find_follow_land/mission.py`**：`Takeoff → Search → Follow`，語音 `land` 事件最高優先打斷。
  `--headless` 用 L8 `scripted_person_xy` 走圓 + 第 ~12 秒注入 land 事件。`--selftest` 印
  `CAPSTONE-MINI OK: Search→Follow in Ns (confirm-cnn gated), tracked K frames mean bearing err X deg, land→landed z=0.40`。
  assert：(a) 經確認門完成 Search→Follow (b) Follow 期 mean `true_bearing_deg` 誤差<18° (c) land 後 `landed` (d) 注入假背景目標被確認門擋下、未誤轉 Follow。
- **重用**：L11 runner + `Takeoff`/`Land`/`Failsafe`/`go()`；L8 `follow_real.cnn_bearing`/`depth_at_bearing`/`world_point`/`true_bearing_deg`/`scripted_person_xy` + PersonCNN；L12 事件與優先序。

### A.3 L14a / L14b / L16 — 開工要點（接 A.0 API）

- **L14a 建圖巡邏**：新 `nanodrone/map.py`（occupancy grid + depth-column→world 投影）＋自帶多柱 `scene.py`（**非復用 L3**）。巡邏 = `Mission([Takeoff, GoTo(角1), …, GoTo(角4), Land])`，每到航點掃描更新地圖。`PATROL OK: visited 4/4 waypoints, mapped C cells`。
- **L14b 板載收斂**：沿用 L4 `quantize_cnn` 把 L13 確認 CNN 轉 int8，量 footprint(<512KB)/精度掉幅；注入 `INFER_LATENCY_MS` 跑 L13 mission 量「延遲↑→bearing err↑」。`QUANT OK …` + `LATENCY OK …`。
- **L16 畢業專題**：`lessons/16_capstone/` 提供 `template_mission.py`（用 `Mission` 積木自組任務）＋ `RUBRIC.md` ＋ `validate_mission.py`（檢查任務圖含 `Takeoff`+`Land`+`Failsafe`、所有轉移有觸發條件）。`CAPSTONE OK: graph valid …`。學員自訂任務也須各自 `--selftest` 綠燈。
