# Demo video script — nanodrone-ai v1.0 (2 min 30 s)

The silent cut (`nanodrone-v1.0-demo.mp4`, attached to the v1.0.0 release)
follows this storyboard exactly; record the narration over it, or read the
captions as chapter cards. One journey, seven stops: hover → see → decide →
follow → voice → map → world model.

| # | 秒數 | 畫面 | English narration | 中文旁白 |
|---|---|---|---|---|
| 0 | 0–8 | Title card: "nanodrone-ai — teach a 27 g drone to fly itself, from $0" | Thirty lessons. One sentence: teach a 27-gram drone to fly itself — offline, on a 512-kilobyte chip — starting from zero dollars in a simulator. | 三十課、一句話：教會一台 27 克的無人機自己飛——離線、跑在 512 KB 的晶片上——從 $0 的模擬器出發。 |
| 1 | 8–24 | `lesson1.gif` (hover) | Lesson one is a hover. It looks trivial — but the split on screen is the whole course: your AI sends setpoints; a flight controller keeps the aircraft alive. The AI never touches the motors. | 第一課是懸停。看起來平凡——但畫面裡的分工就是整門課：你的 AI 送 setpoint，飛控保住飛機。AI 從不碰馬達。 |
| 2 | 24–40 | `lesson2.gif` (perception) | Lesson two, the drone sees. A colour mask, a contour, one number out: the bearing to the target. Simple vision, honest limits. | 第二課，它看見了。一個顏色遮罩、一個輪廓、輸出一個數字：目標的方位角。簡單的視覺、誠實的極限。 |
| 3 | 40–56 | `lesson3.gif` (RL avoidance) | Lesson three, it decides. The simulator hands out labels for free, so you train your own tiny models — the signature move the course never abandons. | 第三課，它會決定了。模擬器免費把標籤交給你，所以你訓練自己的小模型——這個招牌動作之後再也沒離開。 |
| 4 | 56–72 | `lesson6.gif` (follow-me) | Skills compose: find, follow, land. By the mission lessons these become guarded state machines with a real failsafe. | 技能開始組合：尋找、跟隨、降落。到任務課它們變成有守衛的狀態機，帶著真正的 failsafe。 |
| 5 | 72–88 | `lesson09.gif` (voice) | Say it in two languages and it flies. The same 13-action contract will later drive a Tello, a Crazyflie, and an iPhone app — one protocol, no drift. | 兩種語言開口，它就飛。同一份 13 動作合約之後會驅動 Tello、Crazyflie 和 iPhone app——一份協議、不漂移。 |
| 6 | 88–104 | `map.png` (L14a occupancy grid, slow zoom) | The drone builds its own map from depth alone — and everything from here on is squeezed toward one number: 512 kilobytes, on-board. | 無人機只靠深度自己把地圖蓋出來——從這裡開始，一切都往一個數字壓：512 KB、板載。 |
| 7 | 104–128 | `wm_closed_loop.png` then `speed_sweep.png` (stills) | The crown: a nano world model. It predicts the future in latent space — never pixels — and dodges before the obstacle is close. Reaction pays a distance; anticipation pays time: raise the speed, and only one of them survives. | 皇冠：nano 世界模型。它在隱空間預測未來——絕不生成像素——在障礙靠近之前就閃開。反應付的是距離、預判付的是時間：把速度拉高，只有一邊活下來。 |
| 8 | 128–150 | Closing card: numbers + links | Every number you just saw prints from a selftest you can rerun. The course is complete — and the research continues in microdrone-world-model. Go fly. | 你剛看到的每個數字，都來自一支你能重跑的 selftest。課程已完結——研究在 microdrone-world-model 繼續。去飛吧。 |

**Closing-card text**: veer-ranking 1.00 · learned policy 0 % crashes
(150 courses, strong draw) · 137.3 KB < 512 KB · github.com/csinghans/nanodrone-ai ·
github.com/csinghans/microdrone-world-model

**Editing notes**: GIFs loop 2–3×每段補滿秒數；stills 用 3–4 s 緩慢放大；
字卡黑底白字置中；無 BGM（配音後再上）。
