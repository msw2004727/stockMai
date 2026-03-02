## [2026-03-02 11:35] 專案現況盤點與起始建議
- 完成事項：確認專案已具備 FastAPI `/health`、`.env.example`、`docker-compose.yml`；確認 `AGENTS.md` 已建立並要求每回合更新工作日誌。
- 目前進度：Done（初始化骨架已存在）
- 下一步：先執行 `Copy-Item .env.example .env`，再啟動 PostgreSQL/Redis，最後跑 `uvicorn` 驗證 `/health`。
- 備註（可選）：若 Docker Desktop 尚未啟動，需先手動開啟。

## [2026-03-02 11:37] 實機啟動檢查
- 完成事項：已建立 `.env`；嘗試啟動容器與檢查 Python 環境。
- 目前進度：Blocked（環境缺少 `docker`、`python`、`pip` 指令）
- 下一步：先在本機安裝並確認 Docker Desktop 與 Python 3.11+ 可用，再重新執行啟動流程。
- 備註（可選）：專案程式本身已就緒，阻塞點在本機工具鏈。

## [2026-03-02 11:48] 基礎服務啟動驗證（第二輪）
- 完成事項：使用 `.venv` 成功安裝 `backend/requirements.txt`；FastAPI 可正常啟動，`/` 回傳 200；`/health` 回傳 `degraded`，錯誤明確指向 `localhost:5432`、`localhost:6379` 尚未連通。
- 目前進度：In Progress（API 就緒，資料庫/快取待啟動）
- 下一步：手動開啟 Docker Desktop，待引擎就緒後執行 `docker compose up -d`，再重測 `/health` 目標為 `status: ok`。
- 備註（可選）：shell 可透過絕對路徑執行 docker，但目前 Docker Engine named pipe 尚未可用。

## [2026-03-02 11:53] 三項初始化任務完成
- 完成事項：Docker Compose 已成功啟動 PostgreSQL 與 Redis；API `/health` 驗證通過，回傳 `status: ok`，PostgreSQL `latency_ms: 130`、Redis `latency_ms: 7`。
- 目前進度：Done（FastAPI/.env/docker 三件事全部可用）
- 下一步：以開發模式常駐啟動 `uvicorn backend.app.main:app --reload`，開始新增下一批 API 路由（如 `routes_stock.py`）。
- 備註（可選）：在此 shell 查詢 `docker compose ps` 需提升權限，但服務連通性已由埠與 `/health` 實測確認。

## [2026-03-02 11:47] 前端 H5 工具需求說明
- 完成事項：釐清 H5 前端開發是否需要 Python/FastAPI/PostgreSQL/Redis 與 Docker。
- 目前進度：Done（架構說明）
- 下一步：依開發階段採用對應模式：純前端先用 mock；串接 API 時啟動 FastAPI；驗證資料流時再開 PostgreSQL/Redis。
- 備註（可選）：本回合無程式碼變更。

## [2026-03-02 11:53] 前端 H5 骨架建立與驗證
- 完成事項：新增 `frontend`（Vue 3 + Vite）專案骨架；建立 `/health` 狀態面板；設定 Vite `/api` 代理；完成 `npm install`、`npm run build` 編譯成功，並驗證 `npm run dev` 可啟動於 `http://127.0.0.1:5173`。
- 目前進度：Done（前後端最小串接可用）
- 下一步：啟動後端 `uvicorn` 與前端 `npm run dev`，在瀏覽器確認 UI 顯示 `status: ok`。
- 備註（可選）：為避免 PowerShell policy 問題，前端命令採用 `npm.cmd`。

## [2026-03-02 12:01] 新增股票查詢 API 與前端查詢卡片
- 完成事項：後端新增 `GET /stocks/quote?symbol=xxxx`（TWSE 即時抓取，失敗時對 `2330/2317/0050` 自動 fallback demo）；前端新增股票查詢輸入與結果卡片（開高低收、漲跌、成交量、來源）；`npm run build` 成功；API 實測 `symbol=2330` 回 200。
- 目前進度：Done（前端已可查第一支股票 API）
- 下一步：把查詢結果加上 K 線或近 5 日趨勢資料，再接前端圖表元件。
- 備註（可選）：驗證時發現埠 `8000` 已有既有後端在跑，請避免重複啟動同埠服務。

## [2026-03-02 12:06] 新增近 5 日走勢 API 與前端趨勢圖
- 完成事項：後端新增 `GET /stocks/history?symbol=xxxx&days=5`；支援 TWSE 月資料彙整與 demo fallback；前端新增走勢 API 串接與 `PriceTrendChart` SVG 圖表元件；`npm run build` 成功；後端實測 `quote/history` 皆回 200。
- 目前進度：Done（查詢已含文字資料 + 趨勢可視化）
- 下一步：新增 K 線資料結構（OHLC array）與前端可切換 `5D / 20D` 週期。
- 備註（可選）：本執行環境對外網路受限，TWSE 測試時多使用 fallback 路徑驗證。

## [2026-03-02 12:11] 完成 5D/20D 切換與 K 線資料格式
- 完成事項：後端 `history` 回傳新增 `ohlc`（`[date, open, high, low, close, volume]`）；前端新增 `5D/20D` 切換按鈕，切換即重查資料；新增 `KLineChart` 元件顯示蠟燭圖；`npm run build` 成功。
- 目前進度：Done（可切換週期且同時顯示收盤趨勢 + K 線圖）
- 下一步：加入成交量長條圖與 K 線 hover tooltip（顯示 OHLC/Volume）。
- 備註（可選）：API 實測 `days=20` 回傳 `ohlc` 長度 20、每筆欄位長度 6，格式符合規劃。

## [2026-03-02 12:16] K 線圖升級：成交量 + Hover Tooltip
- 完成事項：`KLineChart` 新增下方成交量柱狀圖、滑鼠 hover 十字線與 tooltip（日期、OHLC、Volume）；前端 `npm run build` 驗證成功。
- 目前進度：Done（K 線可讀性與互動完成）
- 下一步：新增 tooltip 固定模式（點擊鎖定）與 x 軸日期刻度，提升 20D 觀看體驗。
- 備註（可選）：本回合無後端資料結構變更，僅前端圖表互動強化。

## [2026-03-02 12:18] K 線圖升級：點擊鎖定 + 價格/日期刻度
- 完成事項：`KLineChart` 新增 tooltip 點擊鎖定/解除、左側價格刻度線、底部日期刻度（首/中/末）；保留成交量長條與十字線互動；前端 `npm run build` 驗證成功。
- 目前進度：Done（20D 觀看與讀值體驗完成）
- 下一步：可加上「顯示 MA5/MA20」與「成交量均量線」提升分析性。
- 備註（可選）：本回合僅前端圖表元件調整，API 結構未變更。

## [2026-03-02 12:19] K 線圖升級：MA5/MA20 + 成交量均量線
- 完成事項：`KLineChart` 新增收盤 MA5 實線、MA20 虛線、成交量 MA5 線；tooltip 額外顯示 MA5/MA20/V-MA5；新增圖例說明；前端 `npm run build` 驗證成功。
- 目前進度：Done（基礎技術分析視圖完成）
- 下一步：加入 MA 線顯示開關（toggle）與成交量區塊縮放比例調整選項。
- 備註（可選）：成交量均量線使用橘色避免整體視覺偏紫。

## [2026-03-02 12:22] 模組化程度檢視
- 完成事項：檢查目前模組邊界與檔案體積；確認已有基本分層（`backend routes/config/health`、`frontend api/components`），但 `backend/app/stocks.py`（231 行）、`frontend/src/App.vue`（198 行）、`frontend/src/components/KLineChart.vue`（525 行）已偏大，建議再拆分。
- 目前進度：In Progress（可用但仍有中大型檔案）
- 下一步：優先將 `stocks.py` 拆成 `service/parser/provider`，並將 `KLineChart` 的計算邏輯抽到 composable（如 `useKlineSeries.js`）。
- 備註（可選）：本回合無功能變更，屬架構評估。

## [2026-03-02 12:28] 後端 stocks 模組化重構 + 自我驗收
- 完成事項：將 `backend/app/stocks.py` 拆分為 `backend/app/stocks/` package（`routes.py`, `service.py`, `provider.py`, `parsers.py`, `constants.py`, `__init__.py`）；更新 `AGENTS.md` 增加模組化規則與重構後驗收規範。
- 目前進度：Done（路由不變、分層完成）
- 下一步：第二波重構可拆前端 `App.vue` 為 `HealthPanel`、`QuotePanel` 與 `useQuoteHistory` composable。
- 備註（可選）：自我驗收通過：`/health` 200、`/stocks/quote?symbol=2330` 200、`/stocks/history?symbol=2330&days=20` 200（`ohlc` 每筆 6 欄）、`/stocks/quote?symbol=9999` 404、`frontend npm run build` 成功。

## [2026-03-02 12:32] 第二波模組化完成（前端 App 拆分）
- 完成事項：將 `App.vue` 拆分為 `HealthPanel.vue`、`QuotePanel.vue`，並新增 `useHealthStatus.js`、`useQuoteHistory.js` 兩個 composable 與 `formatters.js`；`App.vue` 降至 59 行，改為頁面組裝層。
- 目前進度：Done（前端狀態管理與視圖責任已分離）
- 下一步：第三波可把 `KLineChart` 內運算抽成 `useKlineSeries`，讓圖表元件更易測試。
- 備註（可選）：拆分後自我驗收通過：`frontend npm run build` 成功；`/health`、`/stocks/quote`、`/stocks/history` 皆回 200；`symbol=9999` 回 404（符合預期）。

## [2026-03-02 12:36] 第三波模組化完成（KLine 計算抽離）
- 完成事項：新增 `frontend/src/composables/useKlineSeries.js`，將 `KLineChart` 的資料正規化、均線計算、座標映射、tooltip 互動與刻度計算全部抽離；`KLineChart.vue` 改為以 composable 回傳資料進行渲染。
- 目前進度：Done（圖表邏輯與視圖分離）
- 下一步：可再拆分 `KLineChart` 的 template 為 `KlineSvgLayer`、`KlineLegend` 子元件，進一步縮短單檔大小。
- 備註（可選）：重構後自我驗收通過：`frontend npm run build` 成功、`/stocks/quote?symbol=2330` 200、`/stocks/quote?symbol=9999` 404；無行為回歸。

## [2026-03-02 12:44] 第四與第五波完成 + 提交 commit
- 完成事項：完成第 4 波（`KLineChart` 再拆分為 `KlineSvgLayer`、`KlineLegend`、`KlineMeta`）；完成第 5 波（新增 backend unittest、`scripts/smoke-check.ps1`、README 模組化與驗收章節）；修正 smoke 腳本以嚴格檢查外部命令 exit code；完成 git commit `ac0b7d7`。
- 目前進度：Done（五波模組化與驗收閉環完成）
- 下一步：將 log/docx 類暫存檔加入 `.gitignore` 或移出 repo，保持工作樹乾淨。
- 備註（可選）：驗收通過：`python -m unittest discover` 8/8、frontend build 成功、API 成功/失敗案例符合預期。

## [2026-03-02 12:45] 清理工作樹 ignore 規則
- 完成事項：`.gitignore` 新增 `*.log`、`*.docx`、`台股AI平台_*.md`，清理本地執行 log 與規格文件類未追蹤檔。
- 目前進度：Done（工作樹清理中）
- 下一步：提交 `.gitignore` 與 `WORKLOG.md`，確認 `git status` 為乾淨。
- 備註（可選）：本回合未改動程式行為。

## [2026-03-02 12:36] 模組化波次確認
- 完成事項：確認目前已完成第 1~3 波，整理剩餘波次規劃。
- 目前進度：In Progress（收斂中）
- 下一步：執行第 4 波（KLine 視圖拆分）與第 5 波（測試/規範收尾）。
- 備註（可選）：本回合無程式功能變更。
## [2026-03-02 12:49] 檢查規格書並評估下一步與完成度
- 做了什麼：逐條檢視《台股AI平台_專案規格書_v3.0.md》的 Phase 0~7、P0/P1/P2，並對照目前實作檔案與 README/WORKLOG。
- 目前狀態：In Progress（規格完成度評估已完成，待執行下一個開發階段）。
- 下一步：優先啟動 Phase 1（FinMind 數據管道）補齊 provider/client + 清洗與缺失值處理，再銜接 Phase 5 的 JWT/速率限制基礎。
- 風險與備註：目前有 stocks MVP 與前端 K 線圖，但尚未落地 ai_gateway、TA-Lib、Backtrader、JWT、NLP/預測主流程。
## [2026-03-02 12:54] 完成 FinMind data_pipeline 模組化與 service 串接
- 做了什麼：新增 ackend/modules/data_pipeline/{finmind_client.py, normalizer.py, repository.py}，並在 ackend/app/stocks/service.py 實作 FinMind 優先、TWSE 次之、demo 最後 fallback。同步補齊 ackend/tests/test_stock_service.py 與新增 ackend/tests/test_data_pipeline.py。
- 目前狀態：Done（建置 + 串接 + 測試皆完成）。
- 下一步：若你同意，下一階段可接著做 Phase 5 的 JWT + rate limit 基礎骨架，讓 API 進入可控存取。
- 驗收結果：python -m unittest discover -s backend/tests -p "test_*.py" 共 16/16 通過，未發現拆分造成的回歸 bug。
## [2026-03-02 12:59] 啟動 Phase 5：JWT 驗證 + 每日速率限制骨架
- 做了什麼：新增 ackend/app/auth.py（JWT 簽發/驗證、get_current_user、Redis 每日 quota、/auth/token），並把 /stocks/quote、/stocks/history 接上 enforce_rate_limit 依賴。同步更新 ackend/app/main.py、ackend/app/config.py、.env.example、README.md。
- 目前狀態：Done（保護層已啟用）。
- 下一步：前端若要串接受保護 API，需先呼叫 /auth/token 取得 bearer token，再帶 Authorization header。
- 驗收結果：python -m unittest discover -s backend/tests -p "test_*.py" 共 22/22 通過。
## [2026-03-02 13:02] 前端接入 JWT 自動取 token 與授權 header
- 做了什麼：重構 rontend/src/api.js，加入 token 快取/自動更新/401 重試邏輯，/stocks/quote 與 /stocks/history 改為受保護呼叫。補充 rontend/.env.example 新增 VITE_API_USER_ID 與 VITE_API_TOKEN_EXPIRES_MINUTES，並更新 README 前端認證行為說明。
- 目前狀態：Done（前端已可自動走 auth token，不需手動貼 header）。
- 下一步：可進入「多角色/真實登入對接」或先做「JWT + rate limit 的 API 整合測試（含 401/429）」。
- 驗收結果：scripts/smoke-check.ps1 通過（backend 22/22 tests + frontend build success）。
## [2026-03-02 13:04] 提供 GitHub 部署（推送）步驟
- 做了什麼：檢查本機 git 狀態與遠端設定，確認目前分支為 master、尚未設定 origin、且有未提交變更。
- 目前狀態：In Progress（待使用者執行 add/commit/remote/push）。
- 下一步：依序執行 git add .、git commit、git branch -M main、git remote add origin ...、git push -u origin main。
- 備註：若遠端已存在提交，先 git pull --rebase origin main 再 push。
## [2026-03-02 13:06] 執行 commit + push
- 做了什麼：檢查 git 狀態、確認分支 main 與遠端 origin，執行 git push origin main。
- 目前狀態：Done（遠端回應 Everything up-to-date）。
- 下一步：若有新變更，再次 git add/commit/push。
- 備註：本次無新程式變更，僅補工作日誌紀錄。
