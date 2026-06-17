# 參與貢獻 nanodrone-ai

🌐 [English](CONTRIBUTING.md) · **繁體中文**

感謝你幫忙讓「邊緣 AI 無人機」對新手更友善！這是一個**教學型** repo，所以「清楚易懂」和「正確無誤」同樣重要。

## 你可以怎麼貢獻

- **修正或改進課程** — 更清楚的說明、更好的圖、能跑的程式碼。
- **校對翻譯** — 指出繁中版與英文來源（或反之）不一致的地方。
- **回報問題** — 若某個指令、安裝步驟或腳本在你的機器上不能跑，請開 issue（附上你的 macOS 版本與晶片）。
- **新增課程** — 請先開 issue 討論範圍與排序，再動手。

## 雙語規則（重要）

每篇文件與課程都有**兩種語言**：

- **英文是來源語言。** 先寫或改英文版。
- **繁體中文（`zh-TW`）** 版跟進。當你改動英文檔，請在同一個 PR 一起更新對應的 `zh-TW` 檔；若無法，請加上 `needs-translation` 標籤讓校對者處理。
- 檔案對應慣例：
  - `README.md` ↔ `README.zh-TW.md`
  - `docs/en/NN-topic.md` ↔ `docs/zh-TW/NN-topic.md`（相同編號 + slug）
  - `lessons/<name>/README.md` 內含雙語，英文段落在前。

CI 會檢查每個 `docs/en/*.md` 都有對應的 `docs/zh-TW/*.md`。

## 課程結構

請維持五段式，讓課程對新手保持可預期：

1. **為什麼** — 這一課解決什麼問題、為何重要。
2. **概念** — 把觀念講給第一次接觸的人聽。
3. **動手做** — 完整、可直接跑的程式（不要留「自行練習」的空白）。
4. **驗收** — 具體、可觀察的成功條件。
5. **延伸閱讀** — 選讀連結與挑戰。

## 新增一課

先用 scaffold 生骨架再填內容 —— 讓每一課保持一致、CI 保持綠燈：

1. `python tools/new_lesson.py NN slug "Title"` —— 生出課程資料夾（含可跑的懸停骨架）、雙語 README、兩語 docs 頁。
2. 在 `lessons/NN_slug/<slug>.py` 實作課程（保持 `--headless` 可用，CI 才能煙霧測試）。
3. 填雙語五段式 README（英文先、繁中跟進）。
4. 填 `docs/en/NN-slug.md` 與 `docs/zh-TW/NN-slug.md`。
5. **加 demo GIF**（每課都要有）：在 `tools/render_media.py` 加一個 render 函式產生
   `assets/lessonNN.gif`，跑 `python tools/render_media.py`，確認 README 嵌入的 GIF 正常。
6. 貼上 scaffold 印出的三個片段：
   - `mkdocs.yml` 的 `nav:` 一列，
   - **兩個** README（`README.md` 與 `README.zh-TW.md`）的學習路線列，
   - `.github/workflows/ci.yml` smoke job 一步（若可 headless 跑）。
7. 本機驗證：`ruff check . && black --check .`、`mkdocs build --strict`、`python lessons/NN_slug/<slug>.py --headless`。
8. commit / push；觸發 CI 確認 lint + docs-parity + smoke 全綠。

優先**重用 `nanodrone` 共用核心**而非複製 —— 裡面有色彩偵測 + 像素轉世界座標
（`detect_blob`、`world_point`）、手把/鍵盤後端（`make_input`）、GUI 外觀
（`setup_view`、`chase_cam`）。因為環境用 editable 安裝（`pip install -e .`），
直接 `import nanodrone` 即可。

## 程式風格

- Python：用 `black` 格式化、`ruff` lint。命名清楚優先於炫技。
- 註解解釋「**為什麼**」，不是「做了什麼」。假設讀者是機器人領域新手。
- 腳本要能單獨執行（新手應能直接 `python lessons/<x>/<script>.py`）。

## Pull Request 流程

1. Fork 並開分支（`git checkout -b lesson-2-fix`）。
2. 先改英文，再改 `zh-TW`。
3. 本機跑 `ruff check . && black --check .`。
4. 開 PR 說明**改了什麼**、**為什麼**，以及翻譯是否同步。

## 行為準則

本專案遵循 [Contributor Covenant](CODE_OF_CONDUCT.md)。請保持友善 — 很多讀者正在學習。
