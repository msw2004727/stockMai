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
