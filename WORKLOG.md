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
