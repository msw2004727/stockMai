# stockMai

最小可執行初始化已完成：

1. FastAPI 後端骨架（含 `/health`）
2. `.env.example` 設定範本
3. `docker-compose.yml`（PostgreSQL + Redis）

## 快速啟動

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
docker compose up -d
uvicorn backend.app.main:app --reload
```

API 健康檢查：

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health | Select-Object -ExpandProperty Content
```

股票報價查詢（MVP）：

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/stocks/quote?symbol=2330" | Select-Object -ExpandProperty Content
```

近 5 日走勢查詢（MVP）：

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/stocks/history?symbol=2330&days=5" | Select-Object -ExpandProperty Content
```

近 20 日走勢查詢（含 `ohlc` K 線資料）：

```powershell
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/stocks/history?symbol=2330&days=20" | Select-Object -ExpandProperty Content
```

## H5 前端啟動（Vue + Vite）

```powershell
cd frontend
Copy-Item .env.example .env
npm.cmd install
npm.cmd run dev
```

前端網址：`http://127.0.0.1:5173`  
前端會透過 Vite proxy 呼叫後端 `/health`，並支援股票 `5D/20D` 走勢與 `OHLC` K 線顯示。

## 模組化架構（目前）

```text
backend/app/
  main.py                # App 組裝（包含 router）
  config.py              # 環境設定
  health.py              # 基礎健康檢查
  stocks/
    routes.py            # /stocks 路由層
    service.py           # 股票流程與 fallback
    provider.py          # TWSE 外部請求
    parsers.py           # 資料解析與格式轉換
    constants.py         # demo 資料

frontend/src/
  App.vue                # 頁面組裝層
  api.js                 # API 請求層
  composables/
    useHealthStatus.js   # 健康檢查狀態邏輯
    useQuoteHistory.js   # 股票查詢狀態邏輯
    useKlineSeries.js    # K 線運算與互動邏輯
  components/
    HealthPanel.vue      # 健康檢查 UI
    QuotePanel.vue       # 股票查詢 UI
    KLineChart.vue       # K 線主容器
    kline/
      KlineSvgLayer.vue  # K 線 SVG 圖層
      KlineLegend.vue    # K 線圖例
      KlineMeta.vue      # 區間資訊
```

## 重構後驗收

```powershell
# backend tests
.venv\Scripts\python.exe -m unittest discover -s backend/tests -p "test_*.py"

# frontend build
cd frontend
npm.cmd run build
cd ..

# optional one-shot smoke check
powershell -ExecutionPolicy Bypass -File .\scripts\smoke-check.ps1
```

## JWT quick start
`/stocks/quote` and `/stocks/history` now require bearer token and daily quota check.

```powershell
# 1) issue a token for a user id
$tokenResp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/auth/token" `
  -ContentType "application/json" `
  -Body '{"user_id":"demo-user","expires_minutes":60}'

$token = $tokenResp.access_token

# 2) call protected endpoints
Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:8000/stocks/quote?symbol=2330" `
  -Headers @{ Authorization = "Bearer $token" } | Select-Object -ExpandProperty Content
```

`/stocks/quote` response now includes quote mode metadata:
- `quote_time`
- `market_state` (`trading` / `daily_close` / `unknown`)
- `is_realtime`
- `source_priority` (`realtime_primary` / `daily_fallback` / `cache` / `short_cache`)
- `provider_used`
- `fetch_latency_ms`
- `cache_hit`
- `freshness` (`as_of_date`, `age_days`, `is_fresh`, `max_age_days`)

Quote runtime tuning envs:
- `QUOTE_SHORT_CACHE_TTL_SECONDS` (default `5`)
- `QUOTE_FETCH_RATE_LIMIT` (default `20`)
- `QUOTE_FETCH_RATE_WINDOW_SECONDS` (default `10`)

## Frontend auth behavior
Frontend now auto-requests JWT from `/auth/token` and attaches `Authorization: Bearer <token>` for `/stocks/*` calls.

Optional frontend env vars:

```env
VITE_API_BASE=/api
VITE_API_USER_ID=h5-demo-user
VITE_API_TOKEN_EXPIRES_MINUTES=60
```

## Deploy on Render (Blueprint)
This repo includes `render.yaml` for one-shot deployment (Postgres + Redis + Backend + Frontend).

Steps:
1. Push latest code to GitHub.
2. In Render dashboard: `New` -> `Blueprint`.
3. Select this repo and branch `main`, then apply.
4. After first deploy, set `FINMIND_TOKEN` in backend service env (optional but recommended).

Notes:
- Backend service URL is injected into frontend `VITE_API_BASE` automatically.
- Backend CORS is now whitelist-based. Set `CORS_ALLOW_ORIGINS` to comma-separated origins (Render default: `https://stockmai-frontend.onrender.com`).

## 1-minute cloud validation (no Docker)
Run from any device with PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\cloud-smoke.ps1 -BackendBaseUrl "https://stockmai-backend.onrender.com"
```

Or run in GitHub Actions:
1. Open `Actions` -> `Cloud Smoke`.
2. Click `Run workflow`.
3. Input your backend URL and run.
4. Check logs for `Cloud smoke check PASSED`.

Nightly monitor (GitHub Actions `schedule`) is enabled at 08:30 Asia/Taipei.
- Optional repo variable: `CLOUD_SMOKE_BACKEND_BASE_URL` (default `https://stockmai-backend.onrender.com`)
- Optional repo variable: `CLOUD_SMOKE_USER_ID` (default `cloud-smoke-nightly`)
- If nightly run fails, workflow auto-creates (or comments on) issue: `[Cloud Smoke] Nightly check failed`

## AI gateway MVP endpoint
Protected endpoint: `POST /ai/analyze`

```powershell
# issue token
$tokenResp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/auth/token" -ContentType "application/json" -Body '{"user_id":"demo-user","expires_minutes":60}'
$token = $tokenResp.access_token

# call AI analyze
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/ai/analyze" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"symbol":"2330","user_prompt":"focus on short-term trend"}'
```

Claude real client is enabled when backend env `ANTHROPIC_API_KEY` is set.
If key is empty, `claude` provider falls back to mock client.

Frontend now includes an AI panel that calls `/ai/analyze` using the same JWT flow.

Real provider clients now available:
- Claude: `ANTHROPIC_API_KEY` + `CLAUDE_MODEL`
- OpenAI (gpt5): `OPENAI_API_KEY` + `GPT_MODEL`
- Grok: `GROK_API_KEY` + `GROK_MODEL`
- Gemini: `GEMINI_API_KEY` + `GEMINI_MODEL`

If a key is missing, that provider automatically falls back to mock.

Step 4 additions:
- Weighted consensus: set `AI_PROVIDER_WEIGHTS` (example: `claude=1.0,gpt5=1.0,grok=1.0,gemini=1.0`).
- Cost tracking + budget: set `AI_DAILY_BUDGET_USD` (defaults to `5.0`).
- `/ai/analyze` response now includes `provider_weights` and `cost` summary.
- `/ai/analyze` now also includes `indicator_context` (from PostgreSQL cache when available), and prompt will append technical indicators for better AI analysis.
- `/ai/analyze` now also includes `sentiment_context` (price-action heuristic sentiment signals), and prompt will append sentiment context for better event/risk interpretation.

## Phase 1 data persistence (PostgreSQL + Alembic)
Run DB migration:

```powershell
.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
.venv\Scripts\alembic.exe -c alembic.ini upgrade head
```

Backfill recent history from FinMind into PostgreSQL:

```powershell
.venv\Scripts\python.exe .\scripts\backfill_prices.py --symbols 2330,2317,0050 --days 180
```

After this, `/stocks/quote` and `/stocks/history` read from PostgreSQL cache first, then fallback to FinMind/TWSE.
If upstream providers are temporarily unavailable, API returns `503` (no local demo quote fallback in production mode).

Symbol format:
- Stocks / ETFs now support `4~6` digit symbols (for example `2330`, `2485`, `00878`).

## Stock indicators endpoint
Protected endpoint: `GET /stocks/indicators?symbol=2330&days=60`

Response includes:
- `latest`: `sma5`, `sma20`, `rsi14`, `macd`, `macd_signal`, `macd_hist`
- `series`: indicator time series aligned by date
- `history_source`: where source history was loaded from (`postgres/finmind/twse`)
- `indicator_engine`: indicator calculator engine (`talib` or `python` fallback)
- `freshness`: as-of freshness metadata (`as_of_date`, `age_days`, `is_fresh`, `max_age_days`)

## Strategy decision MVP endpoint
Protected endpoint: `POST /strategy/decision`

```powershell
# issue token
$tokenResp = Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/auth/token" -ContentType "application/json" -Body '{"user_id":"demo-user","expires_minutes":60}'
$token = $tokenResp.access_token

# strategy decision
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/strategy/decision" `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"symbol":"2330","user_prompt":"偏短線，重視風險控制"}'
```

Response includes:
- `action` (`buy` / `hold` / `sell`)
- `confidence` (`0~1`)
- `risk_level` (`low` / `medium` / `high`)
- `reasons` (decision rationale)
- `components` (`indicators` / `sentiment` / `ai_consensus` scores)

## CI checks
GitHub Actions workflow: `.github/workflows/ci.yml`

Runs on every push / PR to `main`:
- backend unit tests
- frontend production build
- UTF-8 validation for `WORKLOG.md` (avoids Pages Jekyll encoding failures)

Operational monitoring workflow: `.github/workflows/cloud-smoke.yml`
- Manual trigger (`workflow_dispatch`) for ad-hoc cloud smoke
- Nightly trigger (`schedule`) with failure issue notification

## API error response format
Standard error payload now includes `error_code` for easier frontend handling and monitoring:

```json
{
  "error_code": "daily_quota_exceeded",
  "message": "Daily quota exceeded",
  "detail": "Daily quota exceeded",
  "status_code": 429,
  "path": "/stocks/quote"
}
```

Common codes:
- `auth_missing_bearer_token` (401)
- `not_found` (404)
- `daily_quota_exceeded` / `rate_limited` (429)
- `service_unavailable` (503)

## Production launch checklist (Batch 5)
- CORS restricted to trusted frontend origins only (`CORS_ALLOW_ORIGINS`, no `*` in production).
- API secrets stored in Render Secret env vars only (no hard-coded keys in repo).
- Cloud smoke run passed (`scripts/cloud-smoke.ps1` or GitHub `Cloud Smoke` workflow).
- Backend unit tests and frontend build are green in CI.
