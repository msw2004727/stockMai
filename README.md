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
