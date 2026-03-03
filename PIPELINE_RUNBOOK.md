# Pipeline Runbook

## 1. 目標
- 每個交易日上午自動同步全市場日資料到 `stock_daily_prices`。
- 同步後自動檢查 pipeline 健康度與覆蓋率。
- 行情頁「前一交易日快速查詢」直接使用同步結果。

## 2. Render 排程（已在 `render.yaml`）
- `stockmai-snapshot-cron`
  - 排程：`30 0 * * 1-5`（UTC，台灣時間 08:30）
  - 任務：`python scripts/run_pipeline_snapshot.py`
- `stockmai-pipeline-monitor-cron`
  - 排程：`0 1 * * 1-5`（UTC，台灣時間 09:00）
  - 任務：`python scripts/check_pipeline_status.py`

## 3. 手動觸發（本機或雲端 shell）
1. 先取 token：
```powershell
$base="https://stockmai-backend.onrender.com"
$token=(Invoke-RestMethod -Method Post -Uri "$base/auth/token" -ContentType "application/json" -Body '{"user_id":"manual-pipeline","expires_minutes":30}').access_token
```
2. 觸發同步：
```powershell
Invoke-RestMethod -Method Post -Uri "$base/stocks/pipeline/snapshot?max_symbols=3000" -Headers @{Authorization="Bearer $token"}
```
3. 查看狀態：
```powershell
Invoke-RestMethod -Method Get -Uri "$base/stocks/pipeline/status" -Headers @{Authorization="Bearer $token"}
```

## 4. 驗收重點
- `/stocks/pipeline/status`
  - `status` 應為 `ok`
  - `latest_trade_date` 應接近 `expected_trade_date`
  - `coverage_ratio` 建議高於 `0.8`
- `/stocks/movers?limit=6`
  - `as_of_date`、`requested_trade_date` 正常
  - `coverage_ratio` 與 pipeline 狀態一致

## 5. 異常處理
- `status=warn` 且 `lag_days > 0`
  - 先手動重跑 `/stocks/pipeline/snapshot`
  - 再查 `/stocks/pipeline/status`
- `coverage_ratio` 過低
  - 檢查 `TWSE STOCK_DAY_ALL` 是否成功抓取
  - 確認 `symbol_count / expected_universe_size` 是否異常下降
