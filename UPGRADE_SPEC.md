# StockMai 大改版計劃規格書 v2.0

> 撰寫日期：2026-03-02
> 目標版本：v2.0
> 狀態：規格討論稿，尚未實作

---

## 目錄

1. [現況分析](#1-現況分析)
2. [改版目標](#2-改版目標)
3. [資料豐富化策略](#3-資料豐富化策略)
4. [爬蟲架構設計](#4-爬蟲架構設計)
5. [AI 分析資料擴充](#5-ai-分析資料擴充)
6. [推薦模組清單](#6-推薦模組清單)
7. [實作分階段計劃](#7-實作分階段計劃)
8. [新增與修改的檔案清單](#8-新增與修改的檔案清單)
9. [環境變數新增總表](#9-環境變數新增總表)

---

## 1. 現況分析

### 1.1 已整合模組完整狀態表

#### Backend Python（requirements.txt）

| 模組 | 狀態 | 實際使用位置 | 備註 |
|------|------|-------------|------|
| `fastapi` | ✅ 核心在用 | 所有 routes.py | — |
| `uvicorn[standard]` | ✅ 核心在用 | 進入點 | — |
| `pydantic-settings` | ✅ 在用 | `app/config.py` | — |
| `psycopg[binary]` | ✅ 在用 | `modules/data_pipeline/storage.py`、`app/health.py` | 直接驅動 PostgreSQL |
| `redis` | ✅ 在用 | `app/stocks/quote_runtime.py`、`app/health.py` | Quote 短快取 + Rate Guard |
| `httpx` | ✅ 在用（可選） | `modules/ai_gateway/base_http_client.py` | 有 urllib fallback |
| `sqlalchemy` | ⚠️ 僅 Alembic 用 | `backend/alembic/env.py` | App 本身沒用，可移除或補用 |
| `alembic` | ✅ 在用 | `alembic.ini`、migration 目錄 | Schema 版本管理 |

#### 選用模組（不在 requirements.txt，try/except fallback）

| 模組 | 狀態 | 使用位置 | 若未安裝的行為 |
|------|------|---------|--------------|
| `TA-Lib` | ⚠️ 選配 | `modules/feature_engineering/indicators.py` | 自動切換 Python 原生計算 |
| `numpy` | ⚠️ 選配 | 同上（TA-Lib 依賴） | 同上 |

#### 外部資料源（API 呼叫，非套件）

| 資料源 | 狀態 | 優先順序 | 免費 | 限制 |
|--------|------|---------|------|------|
| TWSE 即時行情 `mis.twse.com.tw` | ✅ 在用 | 1（優先） | 是 | 盤中才有資料 |
| FinMind `api.finmindtrade.com` | ✅ 在用 | 2 | 免費限 600 筆/日 | 需 token |
| TWSE 月報表 `twse.com.tw` | ✅ 在用 | 3（fallback） | 是 | 只有近 1～2 個月 |
| PostgreSQL 快取 | ✅ 在用 | 0（最優先） | — | 以本地快取為主 |

#### AI 提供商（無 key 自動走 mock）

| 提供商 | 狀態 | 角色定位（prompt_builder.py） |
|--------|------|-------------------------------|
| Claude (Anthropic) | ✅ 接入 | 語意分析師，產業鏈效應、情境推演 |
| OpenAI GPT | ✅ 接入 | 技術分析師，多時框指標對齊 |
| Grok (xAI) | ✅ 接入 | 即時情報偵察，事件驅動、新聞風險 |
| DeepSeek | ✅ 接入 | 資金流量審計，異常量價行為偵測 |

#### Frontend (Node.js)

| 模組 | 版本 | 用途 |
|------|------|------|
| `vue` | ^3.5.13 | UI 框架、Composition API |
| `vite` | ^7.1.12 | 打包/開發伺服器、HMR |
| `@vitejs/plugin-vue` | ^6.0.1 | Vue SFC 支援 |

---

### 1.2 現有資料覆蓋面（AI 分析吃到的資料）

| 資料類型 | 現況 | 說明 |
|---------|------|------|
| K 線 OHLCV 日線 | ✅ 有 | TWSE / FinMind / PostgreSQL |
| SMA5 / SMA20 | ✅ 有 | TA-Lib 或 Python 計算 |
| RSI14 | ✅ 有 | 同上 |
| MACD / Signal / Hist | ✅ 有 | 同上 |
| 價格動能情緒（heuristic） | ✅ 有 | price_action_heuristic，無外部資料 |
| 財報基本面（EPS、ROE 等） | ❌ 無 | — |
| 新聞輿情 | ❌ 無 | — |
| 三大法人買賣超 | ❌ 無 | — |
| 融資融券 | ❌ 無 | — |
| 外資持股比例 | ❌ 無 | — |
| 期貨未平倉量（大盤） | ❌ 無 | — |
| 股利政策 / 殖利率 | ❌ 無 | — |
| 產業分類 / 同業比較 | ❌ 無 | — |

### 1.3 現有缺口摘要

1. **歷史資料深度不足**：TWSE 月報只能抓近 1～2 個月，FinMind 免費版每日 600 筆上限，回測與長周期技術指標嚴重受限。
2. **情感分析僅靠價格**：`sentiment_analysis/analyzer.py` 是純量價啟發式，沒有新聞、沒有社群輿情。
3. **沒有籌碼面資料**：缺乏三大法人、融資融券等關鍵市場資料。
4. **沒有基本面資料**：缺乏財報、EPS、股利等，無法做價值型分析。
5. **沒有爬蟲排程**：所有資料都是「按需請求」，高峰期受外部 API 速率限制影響大。
6. **技術指標單薄**：只有 SMA / RSI / MACD，缺少 KD（Stochastic）、布林通道、OBV 等常用指標。

---

## 2. 改版目標

| 目標 | 分類 | 優先級 |
|------|------|-------|
| 補全 5～10 年台股歷史日線資料 | 資料 | P0 |
| 加入三大法人、融資融券資料 | 資料 | P0 |
| 新增財報基本面資料（EPS、ROE、股利） | 資料 | P1 |
| 新增財經新聞爬蟲（鉅亨、MoneydJ） | 資料 | P1 |
| 新增 MOPS 重大訊息擷取 | 資料 | P2 |
| 擴充技術指標（KD、布林通道、OBV、ATR） | 功能 | P1 |
| AI Prompt 加入籌碼面與基本面資料 | AI | P1 |
| 建立排程背景爬蟲（定時更新 PostgreSQL） | 架構 | P1 |
| 支援可指定來源的爬蟲任務 | 架構 | P2 |
| 前端新增籌碼面圖表 | UI | P2 |
| 前端新增財經新聞面板 | UI | P2 |

---

## 3. 資料豐富化策略

### 3.1 Phase A — 歷史資料補強（最高優先）

#### 方案：使用 `yfinance` 做初始全量補填

**yfinance** 是目前台股歷史日線補填最實際的免費方案：

- 支援台股代碼格式：`2330.TW`（上市）、`6547.TWO`（上櫃）
- 免費，無需 token，無頻率限制（非官方 API，需合理使用）
- 歷史深度：可追溯 20 年以上
- 資料欄位：Open / High / Low / Close / Volume / Dividends / Stock Splits

```python
# 使用範例
import yfinance as yf
df = yf.download("2330.TW", start="2015-01-01", end="2025-12-31")
```

**整合策略：**
- `yfinance` 用於**一次性歷史補填**（`scripts/backfill_yfinance.py`）
- 日常更新仍用 TWSE 官方 API（免費、穩定、無速率爭議）
- FinMind 用於有 token 的用戶做進階資料補強

**補填優先順序：**
```
1. yfinance 補填 5 年歷史日線 → upsert 進 PostgreSQL
2. FinMind 覆蓋補填（如有 token，補充更精確的台灣官方資料）
3. 日常更新：TWSE + FinMind 按需抓取
```

---

### 3.2 Phase B — 籌碼面資料擴充（次高優先）

以下資料全部來自 **TWSE/MOP 官方 JSON API**，免費、免 token、可直接呼叫：

#### 三大法人買賣超（`TWSE 法人資料`）
- 來源：`https://www.twse.com.tw/fund/T86`
- 資料：外資、投信、自營商每日買賣超張數
- 更新頻率：每個交易日收盤後約 17:00

#### 融資融券（`TWSE 信用交易`）
- 來源：`https://www.twse.com.tw/exchangeReport/MI_MARGN`
- 資料：融資餘額、融券餘額、融資增減、融券增減
- 更新頻率：每個交易日收盤後

#### 外資持股比例
- 來源：`https://www.twse.com.tw/fund/MI_QFIIS`
- 資料：外資持股股數、持股比例、上限

#### 每日收盤行情（完整版）
- 來源：`https://www.twse.com.tw/exchangeReport/MI_INDEX`
- 補充漲跌停、均量、本益比等每日欄位

---

### 3.3 Phase C — 新聞輿情爬蟲

#### 目標網站（由易到難）

| 網站 | 資料類型 | 難度 | 說明 |
|------|---------|------|------|
| 鉅亨網 `cnyes.com` | 台股財經新聞 | 中 | 有分類 API，部分 JSON 可直抓 |
| MoneydJ `moneydj.com` | 台股新聞、法人報告 | 中 | 需解析 HTML |
| MOPS 公開資訊觀測站 | 重大訊息、財報 | 中 | 有官方 API（`mops.twse.com.tw`） |
| Yahoo 股市 | 新聞聚合 | 易 | yfinance 附帶 `.news` 屬性 |
| StockFeel 股感 | 分析文章 | 高 | 需爬蟲解析 |

#### 最推薦的新聞來源整合方式

```
yfinance.Ticker("2330.TW").news  → 最快，Yahoo 新聞聚合，英文為主
cnyes.com JSON API               → 中文財經新聞，最貼近台灣市場
MOPS                             → 官方重大訊息，具法律效力
```

---

### 3.4 Phase D — 基本面資料（財報）

#### 來源：FinMind 財報資料集（有 token）
- `TaiwanStockFinancialStatements` - 損益表
- `TaiwanStockBalanceSheet` - 資產負債表
- `TaiwanStockCashFlowsStatement` - 現金流量表
- `TaiwanStockDividend` - 股利政策

#### 來源：MOPS 公開資訊觀測站（免費）
- 每季財報
- 重大訊息公告

#### 最小可用集（P1 優先實作）
```
EPS（每股盈餘）
ROE（股東權益報酬率）
殖利率
本益比（P/E）
股價淨值比（P/B）
負債比率
```

---

## 4. 爬蟲架構設計

### 4.1 現有機制說明

**目前沒有爬蟲。** 所有資料抓取都是「按需請求」模式：
- 每次打 API 端點才觸發外部資料源請求
- Redis 有短快取（5 秒），PostgreSQL 有歷史快取
- 沒有背景定時拉取機制

### 4.2 改版後的爬蟲架構：雙模式設計

```
┌─────────────────────────────────────────────────────────────┐
│                      爬蟲任務系統                             │
├──────────────────────┬──────────────────────────────────────┤
│   模式一：按需爬取    │   模式二：排程背景爬取                 │
│  (On-demand Fetch)   │   (Scheduled Background Crawl)       │
├──────────────────────┼──────────────────────────────────────┤
│ 觸發：API 請求        │ 觸發：定時任務（APScheduler）          │
│ 目標：立即回傳最新資料 │ 目標：預先寫入 PostgreSQL             │
│ 適合：即時報價        │ 適合：法人、融資券、新聞               │
│ 限制：受外部 API 速率  │ 優點：不受請求峰值影響               │
└──────────────────────┴──────────────────────────────────────┘
```

### 4.3 排程設計（APScheduler）

```python
# 建議的排程頻率
每個交易日 08:30  → 拉取上一日三大法人、融資融券
每個交易日 09:00  → 確認今日開盤資料
每個交易日 14:00  → 拉取盤中即時行情（可配合 Redis 短快取）
每個交易日 17:00  → 拉取當日收盤完整行情
每周六 00:00      → yfinance 補填近一個月歷史（差補）
每月一日 00:00    → 財報更新（FinMind）
```

### 4.4 可指定網站的爬蟲任務 API

新增 `POST /crawler/run` 端點，支援指定來源：

```json
// 請求範例
{
  "task_type": "news",
  "sources": ["cnyes", "moneydj", "yahoo"],
  "symbols": ["2330", "2317"],
  "date_range": { "start": "2025-01-01", "end": "2025-03-01" }
}

// 回應
{
  "task_id": "crawl_20250302_001",
  "status": "queued",
  "estimated_sources": ["cnyes", "moneydj", "yahoo"],
  "estimated_count": 150
}
```

**支援的 source 清單：**

| source 名稱 | 對應目標 | 資料類型 |
|------------|---------|---------|
| `twse_institutional` | TWSE 法人 JSON | 三大法人買賣超 |
| `twse_margin` | TWSE 信用交易 JSON | 融資融券 |
| `twse_foreign` | TWSE 外資持股 JSON | 外資持股比例 |
| `finmind_history` | FinMind API | 完整歷史日線 |
| `yfinance_history` | Yahoo Finance | 長期歷史日線 |
| `cnyes_news` | 鉅亨網 | 台股新聞 |
| `moneydj_news` | MoneydJ | 台股新聞 |
| `mops_announcements` | MOPS | 重大訊息 |
| `mops_financials` | MOPS | 每季財報 |

### 4.5 爬蟲任務狀態追蹤（Redis）

```python
# Redis key 結構
crawler:task:{task_id}:status    → queued / running / done / failed
crawler:task:{task_id}:progress  → { fetched: 42, total: 150, source: "cnyes" }
crawler:task:{task_id}:errors    → [ { source: "moneydj", reason: "timeout" } ]
```

---

## 5. AI 分析資料擴充

### 5.1 擴充後 AI Prompt 資料輸入矩陣

| 資料類型 | 現況 | 改版後 | 對應欄位 |
|---------|------|--------|---------|
| K 線 OHLCV | ✅ | ✅ | close, open, high, low, volume |
| SMA5 / SMA20 | ✅ | ✅ | sma5, sma20 |
| RSI14 | ✅ | ✅ | rsi14 |
| MACD | ✅ | ✅ | macd, macd_signal, macd_hist |
| KD（Stochastic） | ❌ | ✅ P1 | k_value, d_value |
| 布林通道 | ❌ | ✅ P1 | bb_upper, bb_middle, bb_lower |
| OBV（能量潮） | ❌ | ✅ P1 | obv |
| ATR（真實波幅） | ❌ | ✅ P1 | atr14 |
| 價格動能情緒 | ✅ | ✅ | sentiment_score, market_sentiment |
| 三大法人買賣超 | ❌ | ✅ P0 | foreign_buy, trust_buy, dealer_buy |
| 融資融券 | ❌ | ✅ P0 | margin_balance, short_balance |
| 外資持股比例 | ❌ | ✅ P1 | foreign_hold_pct |
| EPS（近四季） | ❌ | ✅ P1 | eps_ttm |
| 本益比 P/E | ❌ | ✅ P1 | pe_ratio |
| 股價淨值比 P/B | ❌ | ✅ P1 | pb_ratio |
| 殖利率 | ❌ | ✅ P1 | dividend_yield |
| 新聞標題摘要 | ❌ | ✅ P1 | recent_news (top 5) |
| 重大訊息 | ❌ | ✅ P2 | mops_announcements |

### 5.2 Prompt Builder 擴充方向

現有 `modules/ai_gateway/prompt_builder.py` 已處理：
- `indicator_context`（技術指標）
- `sentiment_context`（價格動能情緒）

**改版後新增 context 注入點：**

```python
def build_analysis_prompt(
    symbol: str,
    user_prompt: str = "",
    indicator_context: dict | None = None,
    sentiment_context: dict | None = None,
    # ↓ 新增
    institutional_context: dict | None = None,   # 三大法人
    margin_context: dict | None = None,          # 融資融券
    fundamental_context: dict | None = None,     # 基本面
    news_context: dict | None = None,            # 新聞摘要
    provider: str | None = None,
) -> str:
    ...
```

### 5.3 各 AI 提供商角色強化（建議）

| 提供商 | 現有角色 | 改版後補強方向 |
|--------|---------|--------------|
| Claude | 語意分析師，產業鏈效應 | 加入基本面解讀、財報趨勢分析 |
| GPT | 技術分析師 | 加入更多技術指標（KD、布林通道） |
| Grok | 即時情報偵察 | 主力消化新聞輿情、重大訊息 |
| DeepSeek | 資金流量審計 | 主力消化三大法人、籌碼面異常 |

---

## 6. 推薦模組清單

### 6.1 Backend 新增模組

| 模組 | 安裝指令 | 用途 | 優先級 |
|------|---------|------|-------|
| `yfinance` | `pip install yfinance` | 台股長期歷史日線補填 | P0 |
| `pandas` | `pip install pandas` | yfinance 回傳 DataFrame 處理 | P0（yfinance 依賴） |
| `apscheduler` | `pip install apscheduler` | 背景排程爬蟲任務 | P1 |
| `beautifulsoup4` | `pip install beautifulsoup4` | HTML 解析（鉅亨、MoneydJ） | P1 |
| `lxml` | `pip install lxml` | BeautifulSoup 的高效能解析器 | P1 |
| `playwright` | `pip install playwright` | JavaScript 渲染網頁爬蟲 | P2 |
| `ta` | `pip install ta` | 純 Python 技術指標套件（KD、布林等） | P1 |
| `numpy` | `pip install numpy` | 移入 requirements.txt（現在是選配） | P1 |

> **關於 TA-Lib**：TA-Lib 在 Windows 安裝複雜（需 C 編譯環境），建議改用 `ta`（Technical Analysis Library）作為主要指標計算套件，語法更簡單，pip 即可安裝，不需 C library。

### 6.2 模組選型說明

#### `yfinance` vs `twstock` vs `FinMind`

| 比較項目 | yfinance | twstock | FinMind |
|---------|----------|---------|---------|
| 歷史深度 | 20 年+ | 1～2 年 | 10 年（付費完整） |
| 免費 | 是 | 是 | 免費版有限制 |
| 需 token | 否 | 否 | 是 |
| 資料穩定性 | 中（非官方） | 高（來自 TWSE） | 高（官方資料整合） |
| 上市 + 上櫃 | 是（.TW/.TWO） | 是 | 是 |
| 基本面資料 | 有（部分） | 無 | 有（完整） |
| **建議用途** | 歷史補填 | 日常即時更新 | 進階籌碼/財報 |

#### 爬蟲框架：`httpx + BeautifulSoup` vs `playwright`

| 比較項目 | httpx + BeautifulSoup | playwright |
|---------|----------------------|------------|
| 適合場景 | 靜態 HTML、JSON API | JavaScript 渲染網頁 |
| 速度 | 快 | 慢（需啟動瀏覽器） |
| 部署複雜度 | 低 | 高（需安裝 chromium） |
| **建議** | 優先使用 | 僅當 JS 渲染必須時才用 |

#### 排程：`APScheduler` vs `Celery`

| 比較項目 | APScheduler | Celery |
|---------|-------------|--------|
| 部署依賴 | 輕量，內嵌 FastAPI | 需額外 worker 進程、Broker |
| 適合規模 | 中小型 | 大型分散式 |
| 學習成本 | 低 | 高 |
| 與 FastAPI 整合 | 直接整合 lifespan | 需獨立服務 |
| **建議** | ✅ 優先選用 | 未來流量大再考慮 |

---

## 7. 實作分階段計劃

### Phase 0 — 基礎準備（前置作業）

**目標：** 安裝新依賴、建立資料庫 schema、整理 requirements.txt

**步驟：**
1. 將 `numpy` 從選配移入 `requirements.txt`
2. 新增 `yfinance`、`pandas`、`ta` 到 `requirements.txt`
3. 新增 Alembic migration：`stock_institutional`（法人）、`stock_margin`（融資券）、`stock_news`（新聞）、`stock_fundamentals`（基本面）四張新表
4. 移除 `requirements.txt` 中 `sqlalchemy`（若確認只供 alembic 使用，可保留但加上注解）

---

### Phase 1 — 歷史資料補強（P0，最先做）

**目標：** 補填 5 年台股日線資料進 PostgreSQL

**步驟：**
1. 新增 `scripts/backfill_yfinance.py`
   - 接受 `--symbols 2330,2317,0050` 和 `--years 5` 參數
   - 呼叫 yfinance，轉換格式，upsert 進 `stock_daily_prices`
2. 更新 `modules/data_pipeline/repository.py`
   - 新增 `get_history_deep(symbol, days)` 函數：PostgreSQL → yfinance fallback
3. 驗收：`backfill_yfinance.py` 跑完後，`/stocks/history?days=250` 能正確回傳

---

### Phase 2 — 籌碼面資料（P0）

**目標：** 接入三大法人、融資融券，存入 PostgreSQL，AI 分析可讀取

**步驟：**
1. 新增 `modules/data_pipeline/twse_institutional_client.py`
   - `fetch_institutional(symbol, date)` → 呼叫 TWSE T86 API
2. 新增 `modules/data_pipeline/twse_margin_client.py`
   - `fetch_margin(symbol, date)` → 呼叫 TWSE MI_MARGN API
3. 新增對應 Alembic migration（`stock_institutional`、`stock_margin` 表）
4. 更新 `app/stocks/routes.py`：新增 `GET /stocks/institutional` 和 `GET /stocks/margin`
5. 更新 `app/strategy/service.py`：在 `build_strategy_decision` 中加入 `institutional_context` 和 `margin_context`
6. 更新 `modules/ai_gateway/prompt_builder.py`：新增 `_build_institutional_block` 和 `_build_margin_block`

---

### Phase 3 — 技術指標擴充（P1）

**目標：** 加入 KD（Stochastic）、布林通道（Bollinger Bands）、OBV、ATR

**步驟：**
1. 將 `ta` 套件加入 `requirements.txt`
2. 更新 `modules/feature_engineering/indicators.py`
   - 新增 `compute_extended_indicators(price_series)` 函數
   - 輸出：`k_value`, `d_value`, `bb_upper`, `bb_middle`, `bb_lower`, `obv`, `atr14`
3. 更新 `app/stocks/routes.py`：`/stocks/indicators` 回應加入新指標欄位
4. 更新 `modules/ai_gateway/prompt_builder.py`：`_build_indicator_block` 補充新指標

---

### Phase 4 — 新聞爬蟲（P1）

**目標：** 定期爬取台股新聞，存入 PostgreSQL，AI 分析可摘要引用

**步驟：**
1. 新增 `modules/news_crawler/` 目錄
   - `base_crawler.py`：共用 HTTP + 解析基底類別
   - `cnyes_crawler.py`：鉅亨網新聞爬蟲
   - `yahoo_news_fetcher.py`：yfinance `.news` 屬性封裝
   - `mops_announcements_fetcher.py`：MOPS 重大訊息
2. 新增 Alembic migration：`stock_news` 表（symbol, title, url, published_at, source, summary）
3. 新增 `modules/data_pipeline/news_repository.py`：新聞 CRUD
4. 新增 `app/crawler/routes.py`：`POST /crawler/run` 端點（支援指定 sources）
5. 更新 `prompt_builder.py`：新增 `_build_news_block`，摘要最近 5 則新聞標題

---

### Phase 5 — 排程背景爬蟲（P1）

**目標：** 建立 APScheduler 排程，定時更新所有資料至 PostgreSQL

**步驟：**
1. 新增 `backend/scheduler.py`
   - 定義所有排程任務（法人、融資券、收盤行情、新聞）
   - 使用 `AsyncIOScheduler` 與 FastAPI lifespan 整合
2. 更新 `backend/app/main.py`
   - 在 `lifespan` 上下文管理器中啟動/關閉 scheduler
3. 新增 `GET /scheduler/status` 端點：顯示各排程最後執行時間與狀態

---

### Phase 6 — 基本面資料（P1）

**目標：** 接入 EPS、ROE、本益比、殖利率，AI 可用於價值分析

**步驟：**
1. 新增 `modules/data_pipeline/finmind_fundamentals_client.py`
   - 封裝 FinMind 財報資料集（EPS、損益表、股利）
2. 新增 Alembic migration：`stock_fundamentals` 表
3. 新增 `app/stocks/routes.py`：`GET /stocks/fundamentals`
4. 更新 `prompt_builder.py`：新增 `_build_fundamental_block`

---

### Phase 7 — 前端擴充（P2）

**目標：** 新增籌碼面圖表、新聞面板

**步驟：**
1. 新增 `frontend/src/composables/useInstitutional.js`
2. 新增 `frontend/src/components/InstitutionalChart.vue`（三大法人走勢圖）
3. 新增 `frontend/src/components/MarginChart.vue`（融資融券走勢圖）
4. 新增 `frontend/src/components/NewsPanel.vue`（最新新聞列表）
5. 更新 `frontend/src/App.vue`：整合新元件

---

## 8. 新增與修改的檔案清單

### 8.1 新增檔案

```text
backend/
├── scheduler.py                                     # APScheduler 排程主程式
│
├── alembic/versions/
│   ├── xxxx_add_stock_institutional.py              # 三大法人表 migration
│   ├── xxxx_add_stock_margin.py                     # 融資融券表 migration
│   ├── xxxx_add_stock_news.py                       # 新聞表 migration
│   └── xxxx_add_stock_fundamentals.py               # 基本面表 migration
│
├── app/
│   ├── crawler/
│   │   ├── __init__.py
│   │   └── routes.py                                # POST /crawler/run 端點
│   └── scheduler/
│       ├── __init__.py
│       └── routes.py                                # GET /scheduler/status
│
└── modules/
    ├── data_pipeline/
    │   ├── twse_institutional_client.py             # 三大法人 TWSE API 客戶端
    │   ├── twse_margin_client.py                    # 融資融券 TWSE API 客戶端
    │   ├── twse_foreign_client.py                   # 外資持股 TWSE API 客戶端
    │   ├── finmind_fundamentals_client.py           # FinMind 財報客戶端
    │   ├── institutional_repository.py              # 法人資料 DB CRUD
    │   ├── margin_repository.py                     # 融資券資料 DB CRUD
    │   ├── fundamentals_repository.py               # 基本面資料 DB CRUD
    │   └── news_repository.py                       # 新聞資料 DB CRUD
    │
    └── news_crawler/
        ├── __init__.py
        ├── base_crawler.py                          # 共用 HTTP + 解析基底
        ├── cnyes_crawler.py                         # 鉅亨網新聞爬蟲
        ├── yahoo_news_fetcher.py                    # yfinance 新聞封裝
        └── mops_announcements_fetcher.py            # MOPS 重大訊息

scripts/
├── backfill_yfinance.py                             # yfinance 歷史補填腳本
└── backfill_institutional.py                        # 三大法人歷史補填腳本

frontend/src/
├── composables/
│   ├── useInstitutional.js                          # 三大法人狀態邏輯
│   ├── useMargin.js                                 # 融資融券狀態邏輯
│   └── useNews.js                                   # 新聞列表狀態邏輯
└── components/
    ├── InstitutionalChart.vue                       # 三大法人圖表元件
    ├── MarginChart.vue                              # 融資融券圖表元件
    └── NewsPanel.vue                                # 最新新聞面板
```

### 8.2 修改的既有檔案

```text
backend/requirements.txt
  → 新增：yfinance, pandas, ta, apscheduler, beautifulsoup4, lxml, numpy
  → 調整：numpy 從選配移入正式依賴

backend/app/main.py
  → 新增：APScheduler lifespan 整合
  → 新增：crawler router、scheduler router 掛載

backend/app/config.py
  → 新增：CRAWLER_ENABLED、SCHEDULER_ENABLED、NEWS_CRAWL_INTERVAL_HOURS
  → 新增：YFINANCE_BACKFILL_YEARS

backend/app/stocks/routes.py
  → 新增：GET /stocks/institutional
  → 新增：GET /stocks/margin
  → 新增：GET /stocks/fundamentals

backend/modules/data_pipeline/__init__.py
  → 補充 export 新增的 client/repository

backend/modules/feature_engineering/indicators.py
  → 新增：compute_extended_indicators()（KD、布林、OBV、ATR）
  → 套件切換：優先用 ta 套件，TA-Lib 為可選加速

backend/modules/ai_gateway/prompt_builder.py
  → 新增：_build_institutional_block()
  → 新增：_build_margin_block()
  → 新增：_build_fundamental_block()
  → 新增：_build_news_block()
  → 修改：build_analysis_prompt() 新增四個 context 參數

backend/app/strategy/service.py
  → 新增：institutional_context 組裝與注入
  → 新增：margin_context 組裝與注入
  → 新增：fundamental_context 組裝與注入
  → 新增：news_context 組裝與注入

backend/app/ai/routes.py（POST /ai/analyze）
  → 新增：從 PostgreSQL 讀取法人、融資券、基本面、新聞資料並注入 prompt

frontend/src/App.vue
  → 整合：InstitutionalChart, MarginChart, NewsPanel

frontend/src/api.js
  → 新增：fetchInstitutional(), fetchMargin(), fetchFundamentals(), fetchNews()
```

---

## 9. 環境變數新增總表

在 `.env.example` 新增以下項目：

```env
# ───── 資料補填 ─────
YFINANCE_BACKFILL_YEARS=5          # yfinance 一次補填年份數（預設 5）
BACKFILL_SYMBOLS=2330,2317,0050    # 預設補填標的清單

# ───── 排程爬蟲 ─────
SCHEDULER_ENABLED=true             # 是否啟用背景排程（預設 true）
CRAWLER_ENABLED=true               # 是否允許 /crawler/run 手動觸發

# 各排程時間（Asia/Taipei，cron 語法）
SCHEDULE_INSTITUTIONAL=30 17 * * 1-5    # 每交易日 17:30 拉三大法人
SCHEDULE_MARGIN=30 17 * * 1-5           # 每交易日 17:30 拉融資券
SCHEDULE_NEWS_CRAWL_HOURS=6             # 新聞爬蟲每 N 小時執行一次（預設 6）

# ───── 新聞爬蟲 ─────
CNYES_NEWS_ENABLED=true            # 啟用鉅亨網新聞爬蟲
MOPS_ANNOUNCEMENTS_ENABLED=true    # 啟用 MOPS 重大訊息
NEWS_MAX_AGE_DAYS=7                # 只保留最近 N 天的新聞

# ───── 基本面 ─────
FUNDAMENTALS_UPDATE_MONTHLY=true   # 每月更新財報
```

---

## 附錄 A：資料表結構（新增四張表）

### `stock_institutional`（三大法人）
```sql
CREATE TABLE stock_institutional (
    id           BIGSERIAL PRIMARY KEY,
    symbol       VARCHAR(10)  NOT NULL,
    trade_date   DATE         NOT NULL,
    foreign_buy  BIGINT,           -- 外資買進張數
    foreign_sell BIGINT,           -- 外資賣出張數
    foreign_net  BIGINT,           -- 外資買賣超
    trust_buy    BIGINT,           -- 投信買進
    trust_sell   BIGINT,           -- 投信賣出
    trust_net    BIGINT,           -- 投信買賣超
    dealer_buy   BIGINT,           -- 自營商買進
    dealer_sell  BIGINT,           -- 自營商賣出
    dealer_net   BIGINT,           -- 自營商買賣超
    source       VARCHAR(50),
    updated_at   TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (symbol, trade_date)
);
```

### `stock_margin`（融資融券）
```sql
CREATE TABLE stock_margin (
    id                BIGSERIAL PRIMARY KEY,
    symbol            VARCHAR(10) NOT NULL,
    trade_date        DATE        NOT NULL,
    margin_balance    BIGINT,     -- 融資餘額（張）
    margin_change     BIGINT,     -- 融資增減
    short_balance     BIGINT,     -- 融券餘額（張）
    short_change      BIGINT,     -- 融券增減
    source            VARCHAR(50),
    updated_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, trade_date)
);
```

### `stock_news`（財經新聞）
```sql
CREATE TABLE stock_news (
    id           BIGSERIAL PRIMARY KEY,
    symbol       VARCHAR(10),     -- 可為 NULL（大盤新聞）
    title        TEXT        NOT NULL,
    url          TEXT        UNIQUE,
    summary      TEXT,
    published_at TIMESTAMPTZ,
    source       VARCHAR(50),     -- cnyes / moneydj / yahoo / mops
    fetched_at   TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_stock_news_symbol_date ON stock_news(symbol, published_at DESC);
```

### `stock_fundamentals`（基本面）
```sql
CREATE TABLE stock_fundamentals (
    id              BIGSERIAL PRIMARY KEY,
    symbol          VARCHAR(10) NOT NULL,
    report_date     DATE        NOT NULL,   -- 財報日期（季末）
    eps_ttm         NUMERIC(10,4),          -- 近四季 EPS
    roe             NUMERIC(8,4),           -- 股東權益報酬率 %
    pe_ratio        NUMERIC(8,4),           -- 本益比
    pb_ratio        NUMERIC(8,4),           -- 股價淨值比
    dividend_yield  NUMERIC(8,4),           -- 殖利率 %
    revenue_growth  NUMERIC(8,4),           -- 營收年成長率 %
    source          VARCHAR(50),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (symbol, report_date)
);
```

---

## 附錄 B：改版後 AI 分析 Prompt 完整輸入格式（示意）

```
你是台灣股票分析助理。請回傳 JSON: summary, signal, confidence, key_points.
signal: bullish/bearish/neutral, confidence: 0~1.
目標標的: 2330 (台積電)

[角色定位] 技術分析師：多時框指標對齊，趨勢結構，執行力風險報酬。

[技術指標 source=postgres, days=60, as_of=2025-03-01]:
SMA5=960.2 SMA20=945.8 RSI14=62.3 MACD=8.44 MACD_SIGNAL=7.21 MACD_HIST=1.23
KD_K=72.1 KD_D=68.4 BB_UPPER=985.0 BB_MIDDLE=945.8 BB_LOWER=906.6 ATR14=18.5

[情緒指標 source=price_action_heuristic, window=20]:
label=bullish score=0.45 change=+5.2% volatility=1.8%

[籌碼面 source=twse, as_of=2025-03-01]:
外資=+8,500張 投信=+1,200張 自營商=-300張 三大法人合計=+9,400張
融資餘額=45,000張 (-500) 融券餘額=3,200張 (+100)

[基本面 as_of=2025-Q1]:
EPS_TTM=45.2 PE=21.3 PB=6.8 殖利率=2.1% 營收年成長=+18%

[最新新聞 top-5]:
1. [cnyes 2025-03-01] 台積電 CoWoS 擴產確定，法人上調目標價至 1100
2. [yahoo 2025-02-28] TSMC ADR 收漲 2.3%，市場看好 AI 晶片需求
...

User focus: 偏短線，重視風險控制

請以繁體中文回答。
```

---

*本文件為 StockMai v2.0 大改版規格書，所有章節內容均為規劃討論稿，正式實作前應進行技術評估與優先級確認。*
