## [2026-03-02 11:35] 專案初始化
- 完成 FastAPI /health、.env.example、docker-compose（PostgreSQL + Redis）。
- 前後端本機可啟動，基本 smoke 測試通過。

## [2026-03-02 12:45] 第一波模組化
- 後端拆分 stocks routes/service/provider/parsers/constants。
- 前端拆分 chart 與 composables，建立 K 線與走勢元件。

## [2026-03-02 13:30] API 安全與整合
- 加入 JWT token 發行、驗證與每日限流。
- 補 API integration tests（401/429/成功路徑）。

## [2026-03-02 13:57] AI Gateway 基礎完成
- 完成 /ai/analyze、多 provider client、retry/fallback。
- 前端 AI 面板接通 API。

## [2026-03-02 14:20] Step 4 完成
- 加權共識與成本追蹤（cost tracker v1）接入主流程。
- 設定檔與測試補齊，backend tests 全綠。

## [2026-03-02 14:26] UI 大調整驗收
- 驗證 backend tests、frontend build、smoke-check 均通過。
- 完成整批 commit/push。

## [2026-03-02 14:33] AI 面板中文化
- AI 分析介面文案改為中文，API 錯誤訊息中文化。
- 前端 build 驗證通過。

## [2026-03-02 15:14] Phase 1 收尾
- 建立 Alembic 與 stock_daily_prices migration。
- 接入 PostgreSQL 快取讀取與 upsert 回寫，新增 backfill 腳本。
- backend tests 與 smoke-check 通過。

## [2026-03-02 15:22] 真實資料回填
- FinMind 回填 2330 / 2317 / 0050 各 180 筆到 PostgreSQL。
- 服務層查詢可回傳 source=postgres。

## [2026-03-02 16:00] Phase 2 進度
- 完成 feature_engineering（SMA5/SMA20/RSI14/MACD）。
- 新增 /stocks/indicators API。
- /ai/analyze prompt 已接入 indicator_context。
- 前端 Market/AI 顯示技術指標與成本摘要。
## [2026-03-02 16:13] 下一步計劃執行：建立 GitHub Actions CI 最小集
- 完成內容：新增 `.github/workflows/ci.yml`，在 push/PR(main) 自動執行 backend unittest、frontend build、WORKLOG UTF-8 檢查。
- 狀態：Done
- 驗收：本機 backend tests 73/73 pass；frontend build pass。
- 補充：README 新增 CI checks 說明。

## [2026-03-02 16:54] Phase 2 收尾：TA-Lib 優先與回傳引擎資訊
- 完成內容：`feature_engineering` 新增 `get_indicator_engine()` 匯出；`/stocks/indicators` 回傳 `indicator_engine`（`talib` 或 `python`）。
- 狀態：Done
- 驗收：補齊 `test_feature_engineering` 與 `test_stock_service` 對 `indicator_engine` 的斷言，並放大 MACD 測試資料長度避免長週期指標空值誤判。
- 補充：README 的 indicators endpoint 說明已同步新增 `indicator_engine` 欄位。

## [2026-03-02 16:32] 規格書對齊檢視與下一步規劃
- 完成內容：比對 `台股AI平台_專案規格書_v3.0.md` 與現行程式，整理已完成與待完成項目。
- 狀態：Done
- 驗收：確認目前主要缺口集中在 Phase 3/4（預測策略決策、情緒訊號接入）、P1（Backtrader 回測）、與動態權重自動更新。
- 補充：下一步建議先做「情緒訊號接入 /ai/analyze」最小可用版本，之後再接動態權重與回測。

## [2026-03-02 16:39] 差異化 Prompt 第 1 項完成
- 完成內容：`prompt_builder` 新增 per-provider 角色化 prompt（claude/gpt5/grok/gemini）；`/ai/analyze` 改為產生並傳遞 `provider_prompts`；gateway router 逐 provider 套用對應 prompt。
- 狀態：Done
- 驗收：新增/更新 `test_prompt_builder`、`test_ai_gateway_router`、`test_api_integration`；全量 backend tests `76/76` 通過。
- 補充：回應中保留原 `prompt`，並新增 `provider_prompts` 方便前端或除錯查看各 AI 實際提示詞。

## [2026-03-02 16:54] 下一步執行：情緒訊號接入 /ai/analyze（MVP）
- 完成內容：新增 `sentiment_analysis` 模組（price-action heuristic），產出 `sentiment_context`；`/ai/analyze` 回傳新增 `sentiment_context`，並將情緒區塊注入所有 provider prompt。
- 狀態：Done
- 驗收：新增 `test_sentiment_analysis`，並更新 `test_prompt_builder`、`test_api_integration`；全量 backend tests `80/80` 通過。
- 補充：目前情緒來源為行情推導，後續可無痛替換為新聞/社群來源並沿用同一 context schema。

## [2026-03-02 17:19] 雲端優先規則補充與即時報價差距評估
- 完成事項：`AGENTS.md` 新增「作業模式規則（雲端優先）」；確認後續流程預設以 Render/GitHub 雲端作業為主。
- 目前進度：Done
- 下一步：針對台股代號格式（含 5 碼 ETF）與即時報價來源規格，實作正式版路線圖第 1 批修正。
- 備註（可選）：目前行情查詢仍以日線來源為主，尚未達成盤中即時報價。

## [2026-03-02 17:28] 正式化第 1 批：4~6 碼代號 + 關閉 demo fallback + freshness
- 完成事項：`/stocks/*` 與 `/ai/analyze` symbol 驗證放寬為 4~6 碼；行情流程移除 demo fallback，改為來源不可用回傳 503；quote/history/indicators 新增 `freshness` 欄位；前端查詢提示改為支援 `00878`。
- 目前進度：Done
- 下一步：接續正式化第 2 批（盤中即時來源接入與回傳欄位標準化，例如 quote_time / market_state）。
- 備註（可選）：驗收已通過：backend unittest `82/82`、frontend build pass。

## [2026-03-02 17:38] 正式化第 2 批（進行中）：即時報價 provider 鏈
- 完成事項：新增 `quote_provider`（TWSE 即時 -> FinMind 日線 -> TWSE 日線）鏈式架構；`get_quote` 改為走 provider 鏈並保留 `quote_time/market_state/is_realtime/source_priority` 等欄位；新增 `test_quote_provider` 並調整 `test_stock_service`。
- 目前進度：Done
- 下一步：把新欄位接到前端行情卡（顯示盤中/收盤狀態與報價時間），再做 Render 雲端 smoke 驗收。
- 備註（可選）：驗收已通過：backend unittest `86/86`、frontend build pass。

## [2026-03-02 17:39] 正式化第 2 批（續）：前端顯示即時狀態
- 完成事項：`QuotePanel` 顯示 `quote_time`、`market_state`、`is_realtime`；前端 build 驗收通過。
- 目前進度：Done
- 下一步：將這批 provider + UI 變更 commit/push，並在 Render 端做實際 API smoke。
- 備註（可選）：本機環境嘗試直接連線 Render API 時遇到網路連線限制，需在你端或 CI/Render shell 驗證最終 smoke。

## [2026-03-02 17:40] 即時報價第 2 批提交與下一步規劃
- 完成事項：整理即時 provider 鏈、service、測試、前端顯示與 README 文件，準備 commit/push。
- 目前進度：Done
- 下一步：進入第 3 批（Redis 短快取 + rate guard + 雲端 smoke 自動化）。
- 備註（可選）：此批本地驗收維持 backend `86/86` 通過、frontend build 通過。

## [2026-03-02 17:50] 正式即時報價第 3 批完成（短快取 + rate guard）
- 完成事項：新增 `quote_runtime`（Redis/記憶體短快取 + 速率防護）；`get_quote` 接入短快取與速率限制；quote 回傳新增 `provider_used`、`fetch_latency_ms`、`cache_hit`；補齊 `test_quote_runtime` 與整體測試。
- 目前進度：Done
- 下一步：執行第 4 批雲端 smoke 自動化與可觀測驗收（見下方詳細計劃）。
- 備註（可選）：驗收通過：backend unittest `91/91`、frontend build pass。

## [2026-03-02 17:50] 第 4 批計劃（雲端 smoke + 可觀測）
- 完成事項：完成 `scripts/cloud-smoke.ps1`（驗證 `/health`、`/auth/token`、`2330/00878` 與即時欄位）；新增 `.github/workflows/cloud-smoke.yml`（`workflow_dispatch` 手動輸入 backend URL 執行 smoke）；README 補齊「1 分鐘雲端驗收」流程。
- 目前進度：Done
- 下一步：進入第 5 批正式上線收尾（CORS 白名單、錯誤碼標準化、上線驗收清單）。
- 備註（可選）：本機沙箱對外網連線受限，無法直接連通 Render；可在你設備或 GitHub Actions 執行 smoke 並取得最終結果。

## [2026-03-02 17:50] 第 5 批計劃（正式上線收尾）
- 完成事項：Plan only（尚未實作）。
- 目前進度：Pending
- 下一步：
  1) CORS 收斂：由 `*` 改為前端正式網域白名單。
  2) 錯誤碼與訊息標準化：`404/429/503` 統一格式（含 error_code）。
  3) 安全與成本檢查：確認 API key 僅用 Render Secret；AI 與行情速率限制生效。
  4) 上線驗收清單：功能、效能、回歸測試結果整理進 README + WORKLOG。
- 備註（可選）：完成標準：可連續穩定查詢、錯誤可觀測、部署可重現。

## [2026-03-02 17:59] 第 5 批完成（正式上線收尾）
- 完成事項：新增全域錯誤處理（`error_code/message/detail/status_code/path`），涵蓋 `401/404/422/429/503`；保留 `detail` 相容既有前端。CORS 改為白名單策略，更新 `backend/app/config.py`、`.env.example`、`render.yaml`（Render 預設僅前端正式網域）。
- 目前進度：Done
- 下一步：在 Render/GitHub Actions 執行一次 Cloud Smoke，確認雲端環境錯誤碼與 CORS 設定符合預期，再進入規格書下一階段（策略與回測）。
- 備註（可選）：驗收通過：backend unittest `93/93`、frontend build pass。

## [2026-03-02 18:47] 進度確認：目前所在步驟
- 完成事項：讀取 WORKLOG 最新一筆並確認 git 狀態，判定目前停在第 5 批完成（正式上線收尾）。
- 目前進度：Done
- 下一步：在 Render 或 GitHub Actions 執行一次 Cloud Smoke，確認 CORS 與錯誤碼，之後再進入策略與回測（Phase 3/4）。
- 備註（可選）：目前 git status 顯示工作樹乾淨（main...origin/main，無未提交變更）。

## [2026-03-02 19:02] 雲端驗收啟動：本機通過、Cloud Smoke 卡住
- 完成事項：執行 backend unittest（93/93 pass）、frontend build（pass）；執行 scripts/cloud-smoke.ps1 驗證 Render。/health 與 /auth/token 成功，但 /stocks/quote、/stocks/history 對 2330/00878 皆回 404 not_found（No quote/history data found）。
- 目前進度：Blocked
- 下一步：在 Render 檢查行情來源可用性（FinMind token / TWSE 連線）並補一次資料（或確認 provider fallback），之後重跑 cloud smoke 直到 PASSED。
- 備註（可選）：本回合無程式碼變更，屬驗收與環境檢查；工作樹僅更新 WORKLOG。若要我可下一回合直接做「雲端資料可用性排查清單」。


## [2026-03-02 19:14] 雲端資料可用性排查：定位 TWSE TLS 問題並完成修補
- 完成事項：定位 Render 404 根因為 TWSE 上游在 Python urllib 出現 CERTIFICATE_VERIFY_FAILED (Missing Subject Key Identifier)，且 FINMIND_TOKEN 未設定時被誤判為 not_found。新增 backend/app/stocks/http_client.py（TWSE 專用 TLS fallback）、調整 quote_provider 依實際啟用 provider 計算失敗、調整 get_history 在 FinMind 未設定且 TWSE 失敗時回 503。補測試 test_stock_http_client、test_quote_provider、test_stock_service。
- 目前進度：In Progress
- 下一步：將本次修補部署到 Render（或 merge + 自動部署），再執行 scripts/cloud-smoke.ps1 -BackendBaseUrl https://stockmai-backend.onrender.com 驗證 /stocks/quote 與 /stocks/history 已恢復。
- 備註（可選）：本地驗證：backend unittest 98/98 pass；以修補後程式直接探測可取得 2330（twse_realtime）與 TWSE history。工作樹仍有既有 .tmp 權限殘留警告，不影響本次修補。

## [2026-03-02 19:16] 修補提交：TWSE TLS fallback 與錯誤碼修正
- 完成事項：完成雲端資料可用性修補（TWSE TLS fallback、provider 失敗判定、history 在資料源不可用時回 503）並補齊測試，準備 commit + push 到 main。
- 目前進度：Done
- 下一步：等待 Render 自動部署完成後，重新執行 cloud smoke 驗證 2330/00878。
- 備註（可選）：本地驗證 backend unittest 98/98 pass。

## [2026-03-02 19:18] 即時報價可用性確認（Render）
- 完成事項：重跑 cloud smoke 並通過；/stocks/quote 對 2330 與 00878 均成功回傳，source=twse_realtime、is_realtime=true。額外直測 2330 也回傳 market_state=trading、quote_time 正常。
- 目前進度：Done
- 下一步：持續觀察盤後時段回傳是否切換為 daily_close，並可補一個 nightly smoke 監控。
- 備註（可選）：本回合無程式碼變更，屬雲端驗收確認。

## [2026-03-02 19:21] 瀏覽器 404 排查：雲端即時報價目前可用
- 完成事項：針對 https://stockmai-backend.onrender.com 連續 5 次帶 token 查詢 2330，皆回 200 且 source=twse_realtime。補做 cloud-smoke 亦 PASS（2330/00878）；帶 Origin 的 CORS 檢查也回 200 且 AC-Allow-Origin 正常。
- 目前進度：Done
- 下一步：請在瀏覽器 hard refresh 後重試；若仍 404，回傳該請求的 response body（error_code/message）與發生時間，便可精準判斷是暫時上游無資料或前端狀態問題。
- 備註（可選）：目前前端部署 bundle 為 assets/index-Cb8b4_5j.js（與你提供 log 一致）。

## [2026-03-02 19:23] 下一步計劃規劃（Phase 3/4 啟動）
- 完成事項：依目前狀態（即時報價與雲端 smoke 已通過）規劃後續 5 個執行階段：可觀測監控、策略決策 MVP、回測 P1、動態權重、上線前驗收清單。
- 目前進度：In Progress
- 下一步：先執行第 1 階段最小動作：新增 nightly cloud smoke（排程）與失敗通知，確保即時報價穩定可觀測。
- 備註（可選）：本回合無程式變更，屬規劃與路線確認。

## [2026-03-02 19:26] 第 1 階段完成：nightly cloud smoke + 失敗通知
- 完成事項：更新 `.github/workflows/cloud-smoke.yml`，新增每日 08:30（台灣時間）排程執行；支援 repo variables（`CLOUD_SMOKE_BACKEND_BASE_URL`、`CLOUD_SMOKE_USER_ID`）；排程失敗時自動建立/更新 GitHub issue `[Cloud Smoke] Nightly check failed`。README 已同步補上操作說明。
- 目前進度：Done
- 下一步：在 GitHub Actions 手動觸發一次 `Cloud Smoke`，確認流程正常；再等待下一個排程點驗證 issue 通知行為。
- 備註（可選）：本回合未變更 backend API 邏輯，僅調整監控與文件。

## [2026-03-02 19:49] 驗收指引提供：第 1 階段（nightly cloud smoke）
- 完成事項：提供淺顯版驗收流程，涵蓋手動觸發、成功判定、排程確認與失敗通知驗證。
- 目前進度：Done
- 下一步：依指引在 GitHub Actions 手動跑一次 `Cloud Smoke`，確認後再決定是否 commit + push。
- 備註（可選）：本回合無程式變更，屬操作驗收指引。

## [2026-03-02 19:57] 第 1 階段驗收進度更新：手動驗收完成
- 完成事項：使用者回報第 1、2 項驗收已通過（手動觸發 workflow 與成功判定 OK），準備提交監控 workflow 與 README 說明更新。
- 目前進度：In Progress
- 下一步：commit + push 後，待明天驗證第 3 項（08:30 排程自動執行與失敗通知行為）。
- 備註（可選）：本次提交僅含監控與文件調整，不含 API 行為變更。

## [2026-03-02 19:58] 下一步計劃確認：進入第 2 階段（策略決策 MVP）
- 完成事項：確認第 1 階段已完成並已 push；第 3 項排程驗證待明天。檢視現有 `/ai/analyze` 與前端 AI 面板資料欄位後，制定第 2 階段可執行清單。
- 目前進度：In Progress
- 下一步：先做第 2 階段最小動作：新增 `/strategy/decision` API（輸入 symbol，輸出 action/confidence/reasons/risk），規則先以 indicators + sentiment + ai consensus 組合，並補成功/失敗測試。
- 備註（可選）：本回合無程式變更，屬計劃確認與拆解。

## [2026-03-02 20:10] 第 2 階段 API 骨架完成：/strategy/decision
- 完成事項：新增 `backend/app/strategy` 模組（`routes/service/provider/mapper/constants/schemas`），實作 `POST /strategy/decision`（JWT + quota 保護），整合 indicators + sentiment + AI consensus 產出 `action/confidence/risk_level/reasons`。`backend/app/main.py` 已掛載新 router；README 新增 endpoint 使用說明。補測試 `test_strategy_service` 並擴充 `test_api_integration` 的 strategy 成功/401/404/503 路徑。
- 目前進度：Done
- 下一步：前端新增 Strategy 卡片呼叫 `/strategy/decision`（先最小顯示 action/confidence/risk），並補一次 frontend build + cloud smoke 回歸。
- 備註（可選）：backend 全量測試 `105/105` pass。

## [2026-03-02 20:13] 第 2 階段延伸完成：前後端串接策略決策
- 完成事項：完成 `/strategy/decision` API 骨架並接到前端 AI 頁（新增 StrategyPanel 與 useStrategyDecision）。AI 頁按「分析」會同時刷新 AI 分析與策略決策；README 補 strategy endpoint 說明。驗收通過：backend unittest 105/105、frontend build pass。
- 目前進度：Done
- 下一步：在雲端手動驗證前端策略卡片顯示（action/confidence/risk/reasons）與錯誤情境，再評估是否加入策略歷史紀錄。
- 備註（可選）：本回合將進行 commit + push。

## [2026-03-02 20:15] 下一步計劃規劃：第 2 階段後續與第 3 階段啟動
- 完成事項：確認目前 `main` 已同步遠端，並整理下一步執行順序（雲端前端驗收 -> 策略結果可追蹤 -> 回測 P1）。
- 目前進度：In Progress
- 下一步：先做最小驗收動作：在 Render 前端實測策略卡片（2330/00878）與錯誤案例，確認顯示與錯誤訊息都正常。
- 備註（可選）：本回合無程式變更，屬規劃與驗收路線確認。

## [2026-03-02 20:17] 手動驗收清單確認（排除 08:30 監控）
- 完成事項：整理除排程監控外仍需由使用者端手動驗收的項目，包含前端策略卡片顯示、跨代號與錯誤情境。
- 目前進度：Done
- 下一步：依清單完成前端實測並回報結果（成功/失敗案例各一）。
- 備註（可選）：本回合無程式變更，屬驗收範圍確認。

## [2026-03-02 20:26] 規格書重檢與下一步計劃（以 v3.0 對齊紀錄為準）
- 完成事項：重新檢視既有對齊紀錄，確認目前已完成雲端可用性、策略決策 MVP 與前端串接；主要剩餘缺口仍是 Backtrader 回測 P1 與動態權重自動更新。註：repo 內未找到 `台股AI平台_專案規格書_v3.0.md` 檔本體，本次依 WORKLOG 舊紀錄重整。
- 目前進度：In Progress
- 下一步：啟動回測 P1 最小實作（`/strategy/backtest` API + 核心績效欄位 + 測試），完成後再接動態權重排程。
- 備註（可選）：本回合無程式變更，屬計劃規劃與範圍確認。

## [2026-03-02 20:41] 手機版 UI 優化與中文名詞註解補強
- 完成事項：已完成手機版不擠壓樣式（按鈕與欄位維持同列、避免按鈕換行、長提示字縮小並可水平滑動）；AI/策略區塊文案中文化，並補上 AI 共識、情緒判讀、SMA/RSI/MACD 等名詞用途說明。
- 目前進度：Done
- 下一步：請以手機實機驗收 2330/00878，重點確認查詢列不換行、模型按鈕可橫向滑動、文案皆為可讀中文。
- 備註（可選）：本回合已再補強 `StrategyPanel` 的名詞註解並通過 frontend build。

## [2026-03-02 20:43] 手機版 UI 優化提交與推送
- 完成事項：提交手機版查詢列防擠壓與不換行樣式、長提示字縮小、AI/策略文案中文化與名詞註解補強，並推送至遠端 main。
- 目前進度：Done
- 下一步：請在手機實機驗收按鈕不換行、模型列可橫向滑動、中文文案可讀性。
- 備註（可選）：本回合包含 commit + push。

## [2026-03-02 20:48] AI 真實性確認：未放 API key 時為 Mock fallback
- 完成事項：檢視 ai gateway 程式與設定，確認有接真實 provider client（Claude/OpenAI/Grok/Gemini），但 API key 為空時會自動改用 `MockAIClient`；並以本地腳本實證空 key 回傳 `Mock analysis for 2330 generated by ...`。
- 目前進度：Done
- 下一步：若要改為真 AI，請在部署環境設定 `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GROK_API_KEY` / `GEMINI_API_KEY`（至少一組），再重新觸發 `/ai/analyze` 驗證非 mock 回應。
- 備註（可選）：本回合無程式碼變更，屬規格與行為確認。

## [2026-03-02 20:52] AI 核心按鈕 2x2 置中與名稱簡化
- 完成事項：AIPanel 的模型按鈕改為每列 2 個、共 2 列，並且水平/垂直置中；按鈕文字改為純名稱（Claude、GPT-5、Grok、Gemini），移除括號解釋。
- 目前進度：Done
- 下一步：請在手機 AI 分析頁確認按鈕排版為 2x2 且可正常切換模型。
- 備註（可選）：frontend build 已通過。

## [2026-03-02 20:55] AI 按鈕版型提交與真實 LLM 金鑰安全規劃
- 完成事項：準備提交 AI 模型按鈕 2x2 置中與名稱簡化變更，並整理「API key 不進 GitHub」的最安全流程（本機 `.env` / Render Secret / GitHub Actions Secret 分流）。
- 目前進度：In Progress
- 下一步：commit + push 後，依安全流程在雲端設定金鑰並執行一次真實 LLM 驗收。
- 備註（可選）：本回合包含操作指引，不提交任何明碼金鑰。

## [2026-03-02 20:56] Commit/Push 完成並提供金鑰安全上線流程
- 完成事項：已完成 commit `d1d1d94` 並 push 到 `origin/main`；確認 repo 只追蹤 `.env.example`，未追蹤 `.env`；整理真實 LLM 上線的安全做法（Render Secret + 本機 `.env`，不進 GitHub）。
- 目前進度：Done
- 下一步：在 Render 設定至少一組後端金鑰（例如 `OPENAI_API_KEY`）後，重新部署並驗收 `/ai/analyze` 回應不再出現 `Mock analysis`。
- 備註（可選）：本回合無新增功能碼，重點為部署安全與操作流程。

## [2026-03-02 21:07] 全專案 AI provider：Gemini 改為 DeepSeek
- 完成事項：後端 provider 鏈、設定鍵、模型鍵、預設 provider、權重、Render/.env/README、測試與前端按鈕選項已由 `gemini` 全面改為 `deepseek`；並新增 `deepseek_client`、移除 `gemini_client` 與對應測試檔，改為 `test_deepseek_client`。
- 目前進度：Done
- 下一步：執行 commit + push，並在部署環境設定 `DEEPSEEK_API_KEY`、`DEEPSEEK_MODEL` 後驗收 `/ai/analyze` 與前端模型切換。
- 備註（可選）：frontend build 已通過；backend 全量測試在此機器因缺少 `fastapi/redis/psycopg` 套件無法完整執行，已改以 `py_compile` 檢查本次變更檔語法通過。

## [2026-03-02 21:12] DeepSeek 全量替換提交與推送
- 完成事項：將專案內 AI provider `gemini` 全面替換為 `deepseek`（後端 provider/client、設定鍵、環境變數、Render 設定、前端按鈕與選項、測試檔與文件），並完成提交與推送。
- 目前進度：Done
- 下一步：在部署環境設定 `DEEPSEEK_API_KEY` 後做一次 `/ai/analyze` 真實推論驗收。
- 備註（可選）：frontend build 已通過；本機 backend 全量測試受缺少套件限制，已以 py_compile 檢查本次變更檔語法。

## [2026-03-02 21:13] 真實 AI 金鑰安全接入指引（DeepSeek）
- 完成事項：提供雲端優先（Render）金鑰接入步驟，確保 `DEEPSEEK_API_KEY` 不進 GitHub 且可啟用真實 LLM 推論。
- 目前進度：Done
- 下一步：依指引在 Render 設定 `DEEPSEEK_API_KEY` / `DEEPSEEK_MODEL`，重新部署後驗收 `/ai/analyze` 非 mock 回應。
- 備註（可選）：本回合無程式碼變更，屬部署操作指引。

## [2026-03-02 21:21] 金鑰設定完成確認，進入真實 DeepSeek 驗收
- 完成事項：使用者回報已完成 Render 金鑰設定（DEEPSEEK_API_KEY / DEEPSEEK_MODEL）。
- 目前進度：In Progress
- 下一步：執行 `/auth/token` + `/ai/analyze` 驗證（providers 指定 deepseek），確認回應非 mock 且 provider=deepseek。
- 備註（可選）：本回合無程式碼變更，屬部署驗收指引。

## [2026-03-02 21:21] 擴充三個真實 LLM provider 接入指引
- 完成事項：提供在 Render 安全接入 Claude / GPT-5 / Grok 的步驟，並規劃四 provider 一次驗收流程。
- 目前進度：In Progress
- 下一步：在 Render 新增三組 API key，完成部署後執行多 provider 驗收指令，確認回應非 mock。
- 備註（可選）：本回合無程式碼變更，屬部署操作指引。

## [2026-03-02 21:28] 四 provider 驗收方式說明
- 完成事項：提供「一次驗收 claude/gpt5/grok/deepseek」的操作與判讀標準，說明如何判斷是否為真實 LLM 回應。
- 目前進度：Done
- 下一步：使用者執行驗收指令並回傳 `provider/ok/error/summary/fallback_used` 結果，進行逐項判讀。
- 備註（可選）：本回合無程式碼變更，屬驗收引導。

## [2026-03-02 21:31] 最簡化 AI 驗收指引（無指令版）
- 完成事項：將四 provider 驗收流程改為前端操作版（切模型 + 按分析 + 看成功/非 mock 文案），降低使用門檻。
- 目前進度：Done
- 下一步：使用者在前端依序驗收 Claude / GPT-5 / Grok / DeepSeek，回報是否有任何一個顯示失敗或出現 Mock 文案。
- 備註（可選）：本回合無程式碼變更，屬驗收引導。

## [2026-03-02 21:33] GPT-5 真實推論失敗修正（max_completion_tokens）
- 完成事項：修正 `backend/modules/ai_gateway/openai_client.py`，針對 `provider=gpt5` 改用 `max_completion_tokens`（其餘 OpenAI-compatible provider 維持 `max_tokens`），對應 OpenAI 回傳 400 的參數錯誤。
- 目前進度：Done
- 下一步：重新部署 backend 後，再次執行 GPT-5 模型驗收（AI 分析頁切 GPT-5 按執行）。
- 備註（可選）：已執行 `py_compile` 語法檢查通過；本機缺少完整後端依賴，未跑全量 unittest。

## [2026-03-02 21:40] GPT-5 參數修正提交與推送
- 完成事項：提交 `openai_client` 對 `gpt5` 改用 `max_completion_tokens` 的修正，並推送至 main。
- 目前進度：Done
- 下一步：等待雲端部署完成後，在前端 GPT-5 再測一次 AI 分析是否成功。
- 備註（可選）：本回合包含 commit + push。

## [2026-03-02 21:48] GPT-5 回應解析補強（修正 missing message content）
- 完成事項：修正 `backend/modules/ai_gateway/openai_client.py` 的 GPT-5 內容擷取邏輯，新增支援 `choices.message.content`、`output_text`、`output[].content` 等格式；並補上 `backend/tests/test_openai_compat_clients.py` 對新格式的測試案例。
- 目前進度：In Progress
- 下一步：部署後端最新版本後，前端切到 GPT-5 重新執行一次 AI 分析，確認不再出現 `response missing message content`。
- 備註（可選）：本機執行 unittest 受缺少 `redis` 套件限制未能完整跑通，已以 `py_compile` 檢查變更檔語法。

## [2026-03-02 21:50] GPT-5 解析補強提交與推送
- 完成事項：提交 GPT-5 回應解析相容性修正（含 `output_text` / `output[].content` 支援）與對應測試補強，並推送到 `origin/main`。
- 目前進度：Done
- 下一步：等待 Render 部署完成後，在前端用 GPT-5 再做一次 AI 分析驗收。
- 備註（可選）：本機 unittest 因缺少 `redis` 套件未完整執行，已以 `py_compile` 驗證語法。

## [2026-03-02 22:14] GPT-5 再失敗修正：優先改走 /responses
- 完成事項：針對 `gpt5 response missing message content` 再次修正 `openai_client`，`gpt5` 先呼叫 `/responses`（`input` + `max_output_tokens`），若空內容再 fallback `/chat/completions`；同時補上 fallback 路徑測試。
- 目前進度：In Progress
- 下一步：commit + push 後等待 Render 部署，前端再測 GPT-5 是否恢復成功。
- 備註（可選）：已用 `py_compile` 檢查語法；本機 unittest 仍受缺少 `redis` 套件限制。

## [2026-03-02 22:15] GPT-5 /responses 修正提交與推送
- 完成事項：提交 `gpt5` 優先走 `/responses` 並保留 `/chat/completions` fallback 的修正，連同測試補強一起推送到 `origin/main`。
- 目前進度：Done
- 下一步：等待 Render 部署完成後，前端以 GPT-5 再測一次 AI 分析。
- 備註（可選）：本機 `unittest` 受缺少 `redis` 套件限制，僅完成 `py_compile` 語法檢查。

## [2026-03-02 22:24] AI 回應去程式碼化：補 partial JSON 容錯解析
- 完成事項：修正 `response_normalizer`，當 LLM 回覆 JSON 被截斷時，仍可抽取 `summary/signal/confidence/key_points`，避免前端顯示整段 `{ "summary": ... }` 英文鍵值；並新增對應測試。
- 目前進度：Done
- 下一步：部署後重測 GPT-5，確認成功卡片顯示中文摘要而非原始 JSON 物件字串。
- 備註（可選）：已執行 `py_compile`；本機全量 unittest 仍受缺少 `redis` 套件限制。

## [2026-03-02 22:37] 行情/AI 載入時機與 K 線互動重構
- 完成事項：關閉行情與 AI 頁面的初始自動查詢（僅保留 health 自動檢查）；AI 執行前會先清空舊分析與舊策略資料；K 線圖改為紅漲綠跌並整合收盤走勢線，新增圖層開關（K 線、走勢、均線、成交量、量 MA5）；行情頁移除獨立走勢圖，改由 K 線卡片統一顯示。
- 目前進度：Done
- 下一步：請使用者前端驗收 3 點需求（初始空白、K 線開關與顏色、AI 執行清畫面）是否符合預期。
- 備註（可選）：已執行 `npm run build`（frontend）通過。

## [2026-03-02 22:44] 版面與 AI 容錯修正提交與推送
- 完成事項：提交並推送本輪所有修改，包含前端「手動觸發載入、K 線圖層開關與紅漲綠跌、AI 執行先清空舊資料」及後端 `partial_json` 容錯解析修正。
- 目前進度：Done
- 下一步：等待雲端部署後，驗收行情頁初始空白、K 線顯示切換、AI 重跑時舊資料是否清空。
- 備註（可選）：frontend build 已通過。

## [2026-03-02 23:01] AI 前置查價限制、中文化與載入彈窗
- 完成事項：AI 分析按鈕新增前置檢查（未先在行情頁查當前代號時提示「請先到行情頁面查詢股價」）；行情按鈕改名「查詢股價」；AI 分析重點改為預設空白；預設 AI 核心改為 GPT-5；行情與 AI 欄位改為有標題的欄位框；新增 AI 文案中文化轉換（含 `price_action_heuristic`、`No recent...`、`Heuristic sentiment...`、`window_days=0`、`unknown` 等）；新增行情/AI 分析中的毛玻璃遮罩 + 彈窗載入動畫。
- 目前進度：Done
- 下一步：請前端驗收 6 點需求（前置提示、預設 GPT-5、空白 prompt、欄位框、中文化、載入彈窗）。
- 備註（可選）：已執行 `npm run build`（frontend）通過。

## [2026-03-02 23:02] 六項前端優化提交與推送
- 完成事項：提交並推送本輪前端修正，包含 AI 前置查價提醒、查詢按鈕文案調整、GPT-5 預設、Prompt 預設空白、欄位標題框、AI 英文文案中文化、毛玻璃載入彈窗。
- 目前進度：Done
- 下一步：等待部署完成後，依 6 項需求逐一驗收。
- 備註（可選）：frontend build 已通過。

## [2026-03-02 23:14] 市場狀態修正：依台北時間與休市日判斷
- 完成事項：修正股票報價 `market_state` 判斷邏輯，改為依台北時間即時計算（盤中/開盤前/休市/假日休市），避免夜間仍顯示「交易中」；新增 `TWSE_HOLIDAYS` 環境變數支援手動指定證交所休市日；前端行情頁對應狀態文案更新為「開盤前／休市中／休市（假日）」。
- 目前進度：Done
- 下一步：部署後於夜間與週末各測一次行情頁，確認狀態顯示符合預期，必要時補上今年休市日期到 `TWSE_HOLIDAYS`。
- 備註（可選）：frontend `npm run build` 與 backend `py_compile` 已通過；本機 backend unittest 受缺少 `fastapi` 依賴限制未完整執行。

## [2026-03-02 23:18] 市場狀態修正提交與推送
- 完成事項：提交並推送市場狀態判斷修正（台北時間盤中/休市/假日）與 `TWSE_HOLIDAYS` 設定支援，包含前端狀態文案同步與文件更新。
- 目前進度：Done
- 下一步：等待雲端部署完成後，於夜間與假日驗收市場狀態是否正確顯示。
- 備註（可選）：backend unittest 仍受本機缺少 `fastapi` 套件限制，未完整執行。

## [2026-03-02 23:20] 指標欄位存在性確認（SMA/RSI/MACD）
- 完成事項：確認後端已實作並輸出 `SMA5`、`SMA20`、`RSI14`、`MACD`（含 `macd_signal`、`macd_hist`）；並釐清顯示空值常見原因是資料不足（天數不足）或 AI 路徑只讀本地快取 60 日歷史失敗。
- 目前進度：Done
- 下一步：若要避免 AI 出現空值，建議新增「AI 分析時快取不足則自動補抓歷史資料」的 fallback。
- 備註（可選）：本回合無程式碼變更，屬行為確認與原因釐清。

## [2026-03-02 23:23] 提供 latest 指標最短查詢指令
- 完成事項：提供僅輸出 `/stocks/indicators` 的 `latest` 欄位之最短 PowerShell 指令（含 JWT 取得與授權呼叫）。
- 目前進度：Done
- 下一步：使用者執行指令後回傳結果，確認 `sma5/sma20/rsi14/macd` 是否有值。
- 備註（可選）：本回合無程式碼變更，屬操作指引。

## [2026-03-02 23:26] AI 歷史資料 fallback：快取不足自動補抓
- 完成事項：在 `backend/app/ai/routes.py` 實作 AI 歷史資料 fallback：先讀 PostgreSQL 快取，若不足則自動呼叫 `stocks.service.get_history(days=60)` 補抓，抓不到才回 `none`；並新增 `backend/tests/test_ai_history_fallback.py` 覆蓋快取優先與 fallback 行為。
- 目前進度：Done
- 下一步：部署後重新測試 AI 分析，確認 `indicator_context.latest` 不再常態為空。
- 備註（可選）：`py_compile` 通過；本機 `unittest` 受缺少 `fastapi` 套件限制無法完整執行。

## [2026-03-02 23:26] AI 歷史 fallback 提交與推送
- 完成事項：提交並推送 AI 分析歷史資料 fallback 修正（快取不足時自動補抓歷史）與對應測試檔。
- 目前進度：Done
- 下一步：等待雲端部署完成後，實測 AI 分析確認指標欄位填值改善。
- 備註（可選）：僅提交本次相關檔案，未包含其他未追蹤檔。

## [2026-03-02 23:28] 主題預設調整與規格文件納入提交
- 完成事項：將前端主題初始化改為「首次開啟預設淺色」（不再依系統深色偏好自動切換），並準備把 `UPGRADE_SPEC.md` 一併納入本次提交。
- 目前進度：Done
- 下一步：commit + push 到 `origin/main`，確認雲端部署後首次開啟呈現淺色主題。
- 備註（可選）：frontend `npm run build` 已通過。
## [2026-03-02 23:40] 查詢股價新增中文模糊搜尋代號
- 完成事項：
  - 新增後端 `GET /stocks/search`（JWT 保護），支援關鍵字模糊比對 `symbol/name`。
  - 新增搜尋模組（provider/mapper/service/constants）與記憶體快取，外部清單抓取失敗時會 fallback 常用台股清單。
  - 前端查詢框支援輸入中文名稱（如台積電），提供候選清單；按「查詢股價」時若輸入非代號會先自動解析成台股代號再查報價。
  - 補前端樣式（候選清單）與 API 串接；新增/更新後端測試檔（search service 與 API integration 路徑）。
- 目前進度：Done
- 下一步：請在前端驗收「中文輸入 -> 候選代號 -> 查詢成功」，確認符合你的查價流程。
- 備註（可選）：frontend `npm run build` 通過；backend 在此環境缺少 `fastapi` 套件，僅完成 `py_compile` 語法檢查。
## [2026-03-02 23:44] 中文模糊搜尋功能提交與推送
- 完成事項：
  - 完成 commit `57606e9` 並 push 到 `origin/main`。
  - 本次包含後端 `/stocks/search`、前端中文名稱查價候選、查詢前自動解析代號與樣式調整。
- 目前進度：Done
- 下一步：請在雲端前端實測中文查價（例如輸入「台積電」）並確認能正確帶入 2330 查詢。
- 備註（可選）：本機 backend unittest 受缺少 fastapi 套件限制，已以語法檢查 + frontend build 驗證。
## [2026-03-03 00:03] 使用者最新前端調整提交準備
- 完成事項：
  - 檢查工作樹，確認前端多檔（App/AI/行情/K線/設定/樣式）與 `UI_IMPROVEMENT_SPEC.md` 為本回合待提交內容。
  - 依使用者要求執行 commit + push。
- 目前進度：In Progress
- 下一步：完成提交並推送到 `origin/main`，回報 commit hash。
- 備註（可選）：本回合以提交同步為主，未執行額外測試。
## [2026-03-03 00:04] 使用者最新前端調整提交完成
- 完成事項：
  - 完成提交 `575b0e3`（含前端 UI 調整與 `UI_IMPROVEMENT_SPEC.md`）。
  - 已推送至 `origin/main`。
- 目前進度：Done
- 下一步：請直接在雲端前端實機驗收最新 UI 互動與版面。
- 備註（可選）：本回合聚焦提交同步，未新增測試執行。
## [2026-03-03 00:12] 技術指標顯示異常排查與修正
- 完成事項：
  - 檢查行情技術指標標籤邏輯，確認原本 MA5/MA20 判斷是「大於即黃金交叉、小於即死亡交叉」，會造成看起來幾乎固定訊號。
  - 重整 `frontend/src/components/QuotePanel.vue`（UTF-8），修正指標判讀：
    - MA / MACD：先檢查前一筆與最新一筆是否真的發生穿越，只有穿越才顯示「黃金交叉 / 死亡交叉」，否則顯示「偏多排列 / 偏空排列（或偏多/偏空）」。
    - RSI：改為多段判讀（過熱/偏強/中性/偏弱/超賣），避免長期只顯示中性。
  - 執行 frontend build 驗證通過。
- 目前進度：Done
- 下一步：請前端驗收不同股票代號，確認 MA/MACD 標籤不再固定為同一結果。
- 備註（可選）：本回合未變更後端指標計算公式，僅修正前端顯示判讀與檔案編碼。 
## [2026-03-03 00:26] 四項 UX 計畫實作完成（AI舊資料提醒/歷史區間/橫幅鎖定/Logo）
- 完成事項：
  - `App.vue` 新增 AI 舊資料提醒邏輯：行情重查後切回 AI 分頁，若尚未重跑 AI 會彈窗提示「目前資料是上次最後 AI 分析的股票資料」。
  - 行情歷史區間擴充為 `5/20/90/180`（前端按鈕與資料代入已同步）。
  - 後端 `/stocks/history` 參數上限由 30 提升到 180，並將 TWSE 抓取月數改為隨 days 動態擴張。
  - 頂部/底部橫幅固定：`app-header` 改為 fixed，內容區補 top padding；tab bar 維持 fixed。
  - 標題改為 `StockMai (測試版)`，測試版字樣小字紅色。
  - 補測試：`test_stock_service` 新增 `_resolve_twse_month_count` 覆蓋。
- 目前進度：Done
- 下一步：請在前端驗收四項需求（尤其 AI stale 彈窗觸發與 90/180 日 K 線），若 OK 我可直接幫你 commit + push。
- 備註（可選）：frontend `npm run build` 通過；backend 以 `py_compile` 驗證 `routes/service/test_stock_service` 語法通過（本機缺少 fastapi，未跑全量 unittest）。
## [2026-03-03 00:27] 使用者要求：全部修改檔一次提交與推送
- 完成事項：
  - 彙整目前工作樹全部已修改檔案（含本回合 UX 實作與使用者先前修改檔）。
  - 依需求執行一次性 commit + push 到 `origin/main`。
- 目前進度：In Progress
- 下一步：完成推送後回報 commit hash 與同步狀態。
- 備註（可選）：本回合同步範圍包含前端與後端既有未提交變更。
## [2026-03-03 00:28] 全部修改檔提交與推送完成
- 完成事項：
  - 已將目前全部修改檔一次性提交並推送。
  - commit：`87c9f51`，branch：`main`，remote：`origin/main`。
- 目前進度：Done
- 下一步：請直接在雲端環境驗收本次 UI/行情/AI 流程更新。
- 備註（可選）：工作樹在本次 push 後為乾淨狀態。
## [2026-03-03 00:30] 確認歷史區間按鈕狀態（5/20/90/180）
- 完成事項：
  - 檢查前端 `useQuoteHistory`、`MarketView`、`QuotePanel`，確認歷史區間按鈕已包含 `5/20/90/180` 並已串接查詢。
  - 檢查目前工作樹為乾淨，無需額外程式碼變更。
- 目前進度：Done
- 下一步：若使用者畫面未顯示 90/180，請先重新部署前端並清除快取後再驗收。
- 備註（可選）：本回合無程式變更，屬結果確認。
## [2026-03-03 00:32] 422 錯誤訊息說明與部署狀態判讀
- 完成事項：
  - 釐清 `GET /stocks/history?symbol=2485&days=180` 回 422 的典型原因為參數驗證不通過（多半是後端仍在舊版 days 上限）。
  - 本地程式已確認 `/stocks/history` 允許 `days <= 180`。
- 目前進度：Done
- 下一步：請檢查 Render backend 是否已部署到含 `le=180` 的最新 commit，並重試 180 天查詢。
- 備註（可選）：本回合無程式變更，屬錯誤訊息判讀與排查建議。
## [2026-03-03 00:33] 歷史區間按鈕鎖定（90/180 反灰不可點）
- 完成事項：
  - `QuotePanel` 新增區間鎖定規則：`90`、`180` 天按鈕永久 disabled。
  - 按鈕樣式新增 `locked` 狀態，反灰且游標為 `not-allowed`，避免誤點。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請前端驗收歷史區間列，確認 `90/180` 反灰且無法點擊、`5/20` 正常可查。
- 備註（可選）：本回合僅前端 UI 鎖定調整，未變更 API。
## [2026-03-03 00:35] 分享連結標題來源路徑確認
- 完成事項：
  - 確認前端分享連結標題目前來自 `frontend/index.html` 的 `<title>`。
  - 確認目前專案未設定 `og:title` / `twitter:title` meta。
- 目前進度：Done
- 下一步：若要控制社群分享卡標題，建議在同檔新增 `og:title` 與 `twitter:title`。
- 備註（可選）：本回合無程式碼變更，屬路徑與設定確認。
## [2026-03-03 00:37] 前端標題改名並推送準備
- 完成事項：
  - 將前端頁面標題改為 `Stock金小麥台股AI分析系統`（`frontend/index.html`）。
  - frontend `npm run build` 驗證通過。
- 目前進度：In Progress
- 下一步：commit + push 到 `origin/main`。
- 備註（可選）：本回合依使用者要求直接修改標題並同步版本。
## [2026-03-03 00:38] 前端標題改名提交完成
- 完成事項：
  - 已完成 commit `5241a70` 並 push 到 `origin/main`。
  - 首頁標題已更新為 `Stock金小麥台股AI分析系統`。
- 目前進度：Done
- 下一步：請部署後前端強制重整，確認瀏覽器分頁標題已更新。
- 備註（可選）：本回合只調整 `frontend/index.html` 標題文案。
## [2026-03-03 00:43] 新增 AI 短線分析欄位與版本提醒
- 完成事項：
  - `AIPanel` 新增「AI短線分析（1~5 個交易日）」欄位，從現有 AI 共識摘要與重點組合短線內容。
  - 新增固定提醒文案：「目前此版本參考資料不多，此分析僅供參考，待後續改版。」
  - 同步重整 `AIPanel.vue` 文案為可讀中文，避免舊有亂碼影響使用體驗。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請在 AI 分析頁驗收新欄位顯示與提醒文案是否符合需求。
- 備註（可選）：本回合屬前端顯示層優化，未調整後端 AI 推論 API。
## [2026-03-03 00:45] AI短線分析補強：加入依據資料分析內容
- 完成事項：
  - `AIPanel` 的「AI短線分析（1~5 個交易日）」新增「AI依據資料分析」條列內容。
  - 條列依據包含：均線（SMA5/SMA20）、RSI14、MACD/Signal、市場情緒、AI 共識信心、共識重點。
  - 保留並固定顯示提醒文字：`提醒：目前此版本參考資料不多，此分析僅供參考，待後續改版。`
  - 新增 `short-term-evidence` 樣式並通過 frontend build。
- 目前進度：Done
- 下一步：請在 AI 分析頁驗收短線欄位內容是否符合期待；若要我可再調整為更像「進出場建議格式」。
- 備註（可選）：本回合僅前端顯示層調整，未改動後端 API。
## [2026-03-03 00:48] 決策理由 UI 重構：一卡一理由
- 完成事項：
  - `StrategyPanel` 重整為乾淨 UTF-8，將「決策理由」改為一卡一理由的 `reason-card` 呈現。
  - 補上理由卡片樣式（標題、內文、間距與邊框），提升閱讀性並避免原本段落擁擠。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請在 AI 分析頁驗收策略決策區塊，確認每個理由都獨立成卡片。
- 備註（可選）：本回合僅前端顯示層調整，未改動策略決策 API 內容。
## [2026-03-03 00:49] 本輪 UI 調整提交與推送
- 完成事項：
  - 將 AI短線分析依據內容與策略決策理由卡片化調整，執行 commit + push。
- 目前進度：Done
- 下一步：部署後驗收 AI短線分析與理由卡片顯示。
- 備註（可選）：本次提交以前端 UI 呈現優化為主。
## [2026-03-03 00:51] 行情技術指標文案調整為中文(英文)且不換行
- 完成事項：
  - 行情頁技術指標標籤改為中文(英文)格式：
    - 均線 (SMA5 / SMA20)
    - 相對強弱 (RSI14)
    - 趨勢動能 (MACD / Signal)
    - 柱狀差 (MACD Hist)
    - 來源改為「來源 (Source)」
  - 技術指標列樣式調整為小字、單行不換行，並支援橫向滾動避免擠壓斷行。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請在手機版行情頁驗收技術指標區塊，確認文字不換行且可讀。
- 備註（可選）：本回合僅前端文案與樣式調整，未改 API。
## [2026-03-03 00:58] AI短線分析去重與文案調整
- 完成事項：
  - `AIPanel` 移除 AI短線分析中與 AI共識結果重複的「短線情境／摘要」內容。
  - AI短線分析僅保留「AI依據資料分析」條列，並移除共識信心與共識重點的重複條目。
  - 詳細區塊按鈕更名為「收合AI反饋數據／展開AI反饋數據」。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請在 AI 分析頁驗收短線區塊是否只剩依據條列，並確認收合按鈕文字。
- 備註（可選）：本回合僅前端顯示與文案調整，未改後端 API。
## [2026-03-03 00:59] AI短線去重改版提交與推送
- 完成事項：
  - 完成 AIPanel 調整：AI短線分析只保留「AI依據資料分析」清單，移除與 AI共識重複內容。
  - 將詳細區塊按鈕文字改為「收合AI反饋數據／展開AI反饋數據」。
  - 已完成 commit 4fc01de 並 push 到 origin/main。
- 目前進度：Done
- 下一步：請在 AI 分析頁驗收短線區塊內容與按鈕文字是否符合預期。
- 備註（可選）：本回合含前端調整與版本推送。
## [2026-03-03 12:12] 查詢股價非即時問題排查與修正
- 完成事項：
  - 釐清根因：`get_quote` 原流程為「短快取 -> PostgreSQL -> provider chain」，只要 DB 有資料就不會抓即時來源。
  - 後端調整為「短快取 -> provider chain（TWSE 即時優先）-> PostgreSQL 回退」。
  - 新增測試案例：
    - 有 PostgreSQL 快取時仍優先 provider。
    - provider 不可用時回退 PostgreSQL。
  - README 同步更新 quote/history 快取策略說明。
  - 前端 `npm run build` 驗證通過；`py_compile` 語法檢查通過。
- 目前進度：Done
- 下一步：部署 backend 後，實測 `/stocks/quote?symbol=2330`，確認 `source=twse_realtime`、`is_realtime=true`（盤中）。
- 備註（可選）：本機未安裝 `fastapi`，故 `python -m unittest backend.tests.test_stock_service` 無法在此環境執行完整測試。
## [2026-03-03 12:13] 即時報價修正提交與推送
- 完成事項：
  - 將 quote 流程改為 provider 優先、PostgreSQL 回退，避免盤中優先命中舊快取。
  - 補上 `get_quote` 行為測試（provider 優先 / provider 失敗回退）。
  - README 更新為最新快取策略說明。
  - 依使用者要求執行 commit + push。
- 目前進度：Done
- 下一步：部署 backend 後實測 `/stocks/quote` 是否回傳 `source=twse_realtime`（盤中）。
- 備註（可選）：本機缺 `fastapi` 套件，無法在此環境跑完整 backend unittest。
## [2026-03-03 12:53] 非即時股價深度排查（雲端實測）
- 完成事項：
  - 以 `scripts/cloud-smoke.ps1` 直接打雲端 backend 驗證報價來源。
  - 兩次實測結果皆為 `source=twse_realtime`、`is_realtime=true`、`source_priority=realtime_primary`，顯示後端當下有抓到即時來源。
  - 檢視前後端程式路徑，確認目前不屬於瀏覽器插件依賴。
  - 整理可能非即時原因：前端未自動輪詢、瀏覽器舊版 bundle/快取、上游 TWSE 瞬時不可用時回退日線來源。
- 目前進度：Done
- 下一步：請在你的畫面同時確認 `來源` 與 `即時/日線` 標記；若顯示非 `twse_realtime`，即為上游回退而非插件問題。
- 備註（可選）：本回合屬診斷排查，未新增程式碼變更。
## [2026-03-03 13:03] 即時報價體驗強化（自動刷新 + 防快取 + 回退可視）
- 完成事項：
  - `/stocks/quote` 回應新增防快取標頭：`Cache-Control: no-store`、`Pragma: no-cache`、`Expires: 0`。
  - 前端查價請求改為 `cache: no-store` 並加時間戳參數，降低瀏覽器/中繼快取影響。
  - 行情頁新增盤中自動更新：市場狀態為 `trading` 且頁面可見時，每 5 秒靜默刷新一次。
  - 行情卡新增即時診斷資訊：`成交時間`、`供應商`、`通道`、`回退(是/否)`。
  - 驗證通過：frontend `npm run build`、backend `python -m py_compile`。
- 目前進度：Done
- 下一步：部署 backend + frontend 後，盤中驗收「5 秒自動刷新」與「回退標記」。
- 備註（可選）：本回合含前後端程式變更，尚未 commit/push。
## [2026-03-03 13:05] 即時查價強化提交與推送
- 完成事項：
  - 將行情自動刷新、防快取、回退可視化等變更納入提交。
  - 依使用者要求執行 commit + push。
- 目前進度：Done
- 下一步：部署後盤中驗收 5 秒自動刷新與回退標記是否正常。
- 備註（可選）：本回合為版本提交與推送。
## [2026-03-03 13:15] 3231 跳價問題深度修復（即時解析與盤中防污染）
- 完成事項：
  - 修正 TWSE 即時解析：`z`（最新成交）缺值時，先用買賣盤首檔（`b/a`）推估，不再直接把昨收 `y` 當即時價。
  - 將 `price_source=prev_close` 的情況標記為 `is_realtime=false`，並加上 `note` 說明來源退化。
  - 新增盤中防污染策略：盤中若取得非即時 quote，跳過 Redis 短快取與 PostgreSQL upsert，避免舊值覆蓋當日資料造成來回跳價。
  - 補測試案例：
    - `z` 缺值時採用買賣盤中間價。
    - 僅剩昨收時標記為非即時。
  - 驗證通過：`py_compile`（quote_provider/service/tests）與 frontend `npm run build`。
- 目前進度：Done
- 下一步：部署 backend 後，盤中連續查 `3231` 驗收是否不再於 `131.5` 與 `135` 間跳動。
- 備註（可選）：本機缺 `fastapi` 套件，無法執行完整 unittest 匯入鏈路。
## [2026-03-03 13:18] 3231 跳價修復提交與推送
- 完成事項：
  - 將 3231 跳價修復（TWSE 即時解析、盤中防污染、測試）納入提交。
  - 依使用者要求執行 commit + push。
- 目前進度：Done
- 下一步：部署 backend 後，盤中連續查 3231，確認不再於昨收價與即時價間跳動。
- 備註（可選）：本回合為版本提交與推送。
## [2026-03-03 13:25] 行情報價欄位拆行與分隔線優化
- 完成事項：
  - 行情頁報價資訊改為六個欄位各自獨立一行：交易日、成交時間、即時報價來源、供應商、通道、回退。
  - 每行之間新增分隔線，提升可讀性與掃讀效率。
  - 新增對應樣式：`quote-meta-list` / `quote-meta-row` / `quote-meta-key` / `quote-meta-value`。
  - frontend `npm run build` 驗證通過。
- 目前進度：Done
- 下一步：請在行情頁驗收六欄位分行與分隔線顯示是否符合預期。
- 備註（可選）：本回合僅前端 UI 呈現調整，未改動 API。
## [2026-03-03 13:30] 0 價格排查與防呆修復
- 完成事項：
  - 釐清 0 價來源風險：TWSE 即時欄位 `z` 有機會回 `0/-`，舊邏輯會被當成有效成交價。
  - 修正即時解析：價格需 `>0` 才視為有效；`z=0` 時改走買賣盤 `b/a` 或其他回退邏輯。
  - 新增服務層驗證：quote `close<=0` 視為無效，不再用於短快取/回傳優先資料。
  - 新增儲存層防呆：PostgreSQL 讀寫時跳過非正值 OHLC，避免 0 價污染快取資料。
  - 補測試：quote provider（`z=0` 場景）、storage（非正值跳過）、service（無效 provider payload 回退 postgres）。
  - 驗證通過：`py_compile`（後端相關檔案）與 frontend `npm run build`。
- 目前進度：Done
- 下一步：部署 backend 後，連續查詢曾出現 0 價的股票，確認不再回傳 0 與亂跳。
- 備註（可選）：本機缺 `fastapi` 套件，無法執行完整 backend unittest 匯入鏈路。
## [2026-03-03 13:57] AI分析閱讀順序與情緒圖示化優化
- 完成事項：
  - AI 分析頁面調整為「執行 AI 分析區」優先顯示：在 `AiView` 先呈現 `AIPanel`，再呈現策略決策區塊。
  - 市場情緒卡片移入「展開AI反饋數據」收折內，與技術指標、各模型結果統一放在詳細區。
  - 情緒摘要中的括號數據改為圖示化指標卡（情緒分數／漲跌幅／波動率／視窗天數），摘要文字保留可讀敘述。
  - AI 分析主要欄位標題加上獨立底色（含 AI 分析主標、欄位標題、卡片標題），並同步套用到策略決策標題。
  - 前端驗證完成：`npm run build` 通過。
- 目前進度：Done
- 下一步：請在手機版實機驗收 AI 分析頁的閱讀順序、收折行為與情緒圖示可讀性，再回報是否要微調顏色與圖示語意。
- 備註（可選）：本回合為前端 UI/UX 調整，未改動後端 API。
## [2026-03-03 13:58] AI分析閱讀體驗優化提交與推送
- 完成事項：
  - 依需求將 AI 分析區塊置頂、情緒數據改為圖示化、欄位標題底色化、市場情緒移入 AI 反饋收折區。
  - 本回合執行版本提交與推送（commit + push）。
- 目前進度：Done
- 下一步：請雲端環境重新部署後，手機版實機驗收 AI 分析頁閱讀順序與收折內容。
- 備註（可選）：本回合以前端 UI/UX 調整為主。
