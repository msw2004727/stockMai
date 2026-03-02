# UI 改善計劃規格書

> 撰寫日期：2026-03-02
> 狀態：規格討論稿，尚未實作
> 前提：所有改善均基於現有架構，不引入新 UI framework

---

## 目錄

1. [問題一：跨頁面隱性依賴（AI 頁 disabled 輸入框）](#問題一跨頁面隱性依賴)
2. [問題二：股票報價卡片資訊優先級錯亂](#問題二股票報價卡片資訊優先級錯亂)
3. [問題三：技術指標純文字列表缺乏視覺提示](#問題三技術指標純文字列表缺乏視覺提示)
4. [問題四：策略決策缺乏視覺化表達](#問題四策略決策缺乏視覺化表達)
5. [問題五：K 線圖無觸控支援](#問題五k-線圖無觸控支援)
6. [問題六：AI 分析結果資訊架構混亂](#問題六ai-分析結果資訊架構混亂)
7. [問題七：空狀態缺乏引導設計](#問題七空狀態缺乏引導設計)
8. [問題八：主題切換重複兩處](#問題八主題切換重複兩處)
9. [改善優先級總表](#改善優先級總表)
10. [修改的檔案清單](#修改的檔案清單)

---

## 問題一：跨頁面隱性依賴

### 現況描述

AI 分析頁（`AIPanel.vue`）的股票代號輸入框是 `disabled` 狀態，
提示文字為「先在行情頁查詢股價，再執行 AI 分析會更準確。」

使用者第一次進入 AI 分析頁，會看到：
- 一個灰色無法點擊的輸入框
- 一個無法按下的「執行 AI 分析」按鈕
- 一行小字說明（很可能被忽略）

這個設計要求使用者先讀懂規則才能操作，屬於「隱性依賴」——UI 本身無法傳達正確的操作順序。

### 根本原因

`App.vue` 中 `symbol` 是跨 tab 共享的 shallowRef，架構上 AI 頁完全可以直接輸入代號。
目前之所以 disabled，是因為 AI 分析「前置需要有 quote 資料」，
但這個需求沒有在 UI 上被友善地表達出來。

### 改善方案

**方案 A（推薦）：解除鎖定，AI 頁允許直接輸入代號**

AI 頁加回可用的輸入框，使用者輸入代號後按「執行 AI 分析」：
1. 若當前 symbol 已有 quote（`hasCurrentQuote === true`）→ 直接執行
2. 若無 quote → 先觸發 `refreshQuote()`，quote 拿到後自動接續執行 AI 分析

好處：單一頁面可完成完整流程，不需要跨 tab。

**方案 B：強化引導 Banner（最小改動）**

保留 disabled 輸入框，但在上方加一個醒目的引導 banner：

```
┌─────────────────────────────────────────────┐
│  ⚠  尚未查詢行情                              │
│  請先到「行情」頁輸入股票代號並查詢，           │
│  再回到此頁執行 AI 分析。                      │
│                          [ 前往行情頁 →  ]    │
└─────────────────────────────────────────────┘
```

點擊「前往行情頁」按鈕直接切換 tab。

### 實作步驟（方案 A）

**Step 1** — `AIPanel.vue`

將輸入框從 `disabled` 改為可用，綁定 `@input` 與 `@keydown.enter`：
```html
<!-- 舊 -->
<input :value="symbol" class="input" type="text" disabled />

<!-- 新 -->
<input
  :value="symbol"
  class="input"
  type="text"
  placeholder="輸入台股代號，例如 2330"
  @input="emit('update:symbol', $event.target.value)"
  @keydown.enter.prevent="emit('refresh')"
/>
```

移除 hint 文字「先在行情頁查詢股價...」，改為：
```html
<p class="hint">輸入代號後執行分析，若尚未查詢行情會自動補查。</p>
```

**Step 2** — `App.vue`

`refreshAiAndStrategy` 函數改為：若無 quote，先打 `refreshQuote()`，
並在 quote 完成後（watch `quote`）自動觸發 AI。

---

## 問題二：股票報價卡片資訊優先級錯亂

### 現況描述

行情查詢後顯示 4 張等重的 card：
1. 股票資訊（代號、名稱、日期、市場狀態）
2. 價格區間（開高低收，全是小字 `.sub`）
3. 漲跌與量能（顯示點數差，**沒有 % 漲跌幅**）
4. 資料來源（單獨一張 card，佔面積大）

核心問題：
- **收盤價** 應是最重要的數字，但目前字體跟其他 `.sub` 一樣小
- **漲跌幅（%）** 是台股使用者最先想看的資訊，目前完全沒有
- **資料來源** 是輔助資訊，不應與股價平起平坐各佔一 card

### 改善方案：重構報價區塊

**重新設計報價主卡（Hero Card）：**

```
┌─────────────────────────────────────────┐
│  2330  台積電                            │
│                                         │
│      960.00                             │  ← 收盤價，最大字體
│   ▲ +12.00  (+1.27%)                    │  ← 漲跌（紅/綠色彩，含 % 幅）
│                                         │
│  開 948.0  高 965.0  低 947.0           │  ← 次要資訊，一行緊湊顯示
│  量 45,231 張  ·  2025-03-01  休市中    │
└─────────────────────────────────────────┘
```

「資料來源」降級：不佔獨立 card，改為主卡底部的一行小字或移入「進階資訊」可展開區塊。

### 實作步驟

**Step 1** — `QuotePanel.vue`：新增 `fmtPct` 函數

```js
function fmtPct(change, close) {
  const prev = close - change;
  if (!prev || prev <= 0) return "";
  return ((change / prev) * 100).toFixed(2) + "%";
}
```

**Step 2** — 重構 quote card HTML

將原本 4 個獨立 article card 合併為 1 個 Hero card + 1 個小字補充列：

```html
<article class="card hero-quote-card">
  <!-- 股票標題 -->
  <div class="quote-title-row">
    <span class="quote-symbol">{{ quote.symbol }}</span>
    <span class="quote-name">{{ quote.name }}</span>
    <span class="quote-state-badge" :class="quote.is_realtime ? 'badge-live' : 'badge-close'">
      {{ marketStateLabel(quote.market_state) }}
    </span>
  </div>

  <!-- 主價格 -->
  <div class="quote-price-row">
    <span class="quote-close" :class="quote.change >= 0 ? 'rise' : 'fall'">
      {{ quote.close }}
    </span>
    <span class="quote-change" :class="quote.change >= 0 ? 'rise' : 'fall'">
      {{ quote.change >= 0 ? '▲' : '▼' }}
      {{ Math.abs(quote.change).toFixed(2) }}
      （{{ fmtPct(quote.change, quote.close) }}）
    </span>
  </div>

  <!-- 開高低量 -->
  <div class="quote-ohlv-row">
    <span>開 {{ quote.open }}</span>
    <span>高 {{ quote.high }}</span>
    <span>低 {{ quote.low }}</span>
    <span>量 {{ fmtVol(quote.volume) }} 張</span>
  </div>

  <!-- 資料說明（降級） -->
  <p class="quote-meta-line">
    {{ quote.as_of_date }}
    · {{ quote.is_realtime ? "即時報價" : "日線報價" }}
    · 來源：{{ quote.source }}
  </p>
</article>
```

**Step 3** — `styles.css`：新增 Hero Card 樣式

```css
.hero-quote-card {
  padding: 20px;
}

.quote-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.quote-symbol {
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--ink);
}

.quote-name {
  font-size: 0.95rem;
  color: var(--muted);
}

.badge-live {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  background: color-mix(in srgb, var(--ok) 18%, transparent);
  color: var(--ok);
}

.badge-close {
  margin-left: auto;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
  background: var(--bg-b);
  color: var(--muted);
}

.quote-price-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 10px;
}

.quote-close {
  font-size: clamp(2rem, 6vw, 2.8rem);
  font-weight: 900;
  line-height: 1;
  letter-spacing: -0.02em;
}

.quote-change {
  font-size: 1.05rem;
  font-weight: 700;
}

.quote-ohlv-row {
  display: flex;
  gap: 16px;
  font-size: 0.88rem;
  color: var(--muted);
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.quote-meta-line {
  margin: 6px 0 0;
  font-size: 0.78rem;
  color: var(--muted);
}
```

---

## 問題三：技術指標純文字列表缺乏視覺提示

### 現況描述

```
SMA5（5 日均線）：960.1234
SMA20（20 日均線）：945.8765
RSI14（相對強弱）：62.3456
MACD（趨勢動能）：8.4400
Signal（訊號線）：7.2100
Histogram（柱狀差）：1.2300
```

問題：
- **RSI 62** 到底是超買還是正常？數字本身對非專業者無意義
- **MACD > Signal（8.44 > 7.21）** 代表偏多訊號，但使用者需要自己計算比大小
- 所有數字顯示 **4 位小數**，RSI 到整數、均線到 2 位小數就夠

### 改善方案：加入判讀標籤與視覺提示

**RSI 判讀標籤（最小改動，最大效果）：**

```
RSI14：62.3  [中性]        ← 30~70 為中性
RSI14：28.4  [超賣 ↑]      ← < 30 為超賣（偏多訊號）
RSI14：73.1  [超買 ↓]      ← > 70 為超買（偏空訊號）
```

**MACD 判讀標籤：**

```
MACD：8.44 / Signal：7.21  [偏多 ▲]   ← MACD > Signal
MACD：5.12 / Signal：6.33  [偏空 ▼]   ← MACD < Signal
```

**均線多空判讀：**

```
MA5 > MA20  →  [黃金交叉 ▲]
MA5 < MA20  →  [死亡交叉 ▼]
```

**數字精度縮減：**

| 指標 | 現有精度 | 建議精度 |
|------|---------|---------|
| SMA5 / SMA20 | 4 位 | 2 位 |
| RSI14 | 4 位 | 1 位 |
| MACD / Signal | 4 位 | 2 位 |
| MACD Hist | 4 位 | 2 位 |

### 實作步驟

**Step 1** — `QuotePanel.vue`：新增判讀函數

```js
function rsiLabel(rsi) {
  const v = parseFloat(rsi);
  if (isNaN(v)) return "";
  if (v >= 70) return "超買";
  if (v <= 30) return "超賣";
  return "中性";
}

function rsiClass(rsi) {
  const v = parseFloat(rsi);
  if (isNaN(v)) return "";
  if (v >= 70) return "warn-text";
  if (v <= 30) return "ok";
  return "muted-text";
}

function macdSignal(macd, signal) {
  const m = parseFloat(macd);
  const s = parseFloat(signal);
  if (isNaN(m) || isNaN(s)) return "";
  return m > s ? "偏多" : "偏空";
}

function macdSignalClass(macd, signal) {
  const m = parseFloat(macd);
  const s = parseFloat(signal);
  if (isNaN(m) || isNaN(s)) return "";
  return m > s ? "rise" : "fall";
}

function maLabel(ma5, ma20) {
  const a = parseFloat(ma5);
  const b = parseFloat(ma20);
  if (isNaN(a) || isNaN(b)) return "";
  return a > b ? "黃金交叉" : "死亡交叉";
}

function maLabelClass(ma5, ma20) {
  const a = parseFloat(ma5);
  const b = parseFloat(ma20);
  if (isNaN(a) || isNaN(b)) return "";
  return a > b ? "rise" : "fall";
}
```

**Step 2** — 技術指標卡片 HTML 改寫（QuotePanel.vue）

```html
<article class="card full-span">
  <p class="label">技術指標</p>
  <template v-if="indicators?.latest">

    <!-- 均線區 -->
    <div class="indicator-row">
      <span class="indicator-name">MA5 / MA20</span>
      <span class="indicator-value">
        {{ fmt(indicators.latest.sma5, 2) }} / {{ fmt(indicators.latest.sma20, 2) }}
      </span>
      <span class="indicator-tag" :class="maLabelClass(indicators.latest.sma5, indicators.latest.sma20)">
        {{ maLabel(indicators.latest.sma5, indicators.latest.sma20) }}
      </span>
    </div>

    <!-- RSI 區 -->
    <div class="indicator-row">
      <span class="indicator-name">RSI14</span>
      <span class="indicator-value">{{ fmt(indicators.latest.rsi14, 1) }}</span>
      <span class="indicator-tag" :class="rsiClass(indicators.latest.rsi14)">
        {{ rsiLabel(indicators.latest.rsi14) }}
      </span>
    </div>

    <!-- MACD 區 -->
    <div class="indicator-row">
      <span class="indicator-name">MACD / Signal</span>
      <span class="indicator-value">
        {{ fmt(indicators.latest.macd, 2) }} / {{ fmt(indicators.latest.macd_signal, 2) }}
      </span>
      <span class="indicator-tag" :class="macdSignalClass(indicators.latest.macd, indicators.latest.macd_signal)">
        {{ macdSignal(indicators.latest.macd, indicators.latest.macd_signal) }}
      </span>
    </div>

  </template>
  <p v-else class="sub">暫無技術指標資料</p>
</article>
```

**Step 3** — `styles.css`：新增 indicator-row 樣式

```css
.indicator-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 0;
  border-bottom: 1px solid var(--border);
  font-size: 0.9rem;
}

.indicator-row:last-child {
  border-bottom: none;
}

.indicator-name {
  flex: 0 0 120px;
  color: var(--muted);
  font-size: 0.84rem;
}

.indicator-value {
  flex: 1;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}

.indicator-tag {
  flex: 0 0 auto;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--bg-b);
}

.indicator-tag.rise { color: var(--up-color); }
.indicator-tag.fall { color: var(--down-color); }
.indicator-tag.ok   { color: var(--ok); }
.indicator-tag.warn-text { color: var(--warn); }
.indicator-tag.muted-text { color: var(--muted); }
```

---

## 問題四：策略決策缺乏視覺化表達

### 現況描述

策略決策結果（`StrategyPanel.vue`）：

```
總結
偏多（信心 0.72）
風險等級：中
綜合分數：0.214

分項分數
技術指標：偏多（0.400）
市場情緒：中性（0.000）
AI 共識：偏多（0.286）
```

問題：
- 「偏多」這個重要結論與其他說明文字大小相同，沒有視覺重量
- 「信心 0.72」是什麼意思？應該讓使用者一眼看出「72% 的把握」
- 分項分數是純文字，三個項目的強弱無從比較

### 改善方案

**Action Badge（最優先，最小改動）：**

```
┌─────────────────────────────────────────────┐
│  策略決策                                    │
│                                             │
│       ┌────────────────────┐               │
│       │  ▲  偏  多         │  ← 大型有色 badge
│       └────────────────────┘               │
│   信心  ████████████░░  72%                 │  ← 進度條
│   風險等級：中     綜合分數：0.21            │
│                                             │
│  分項評估                                   │
│  技術指標  ████████░░░  偏多                 │
│  市場情緒  █████░░░░░░  中性                 │
│  AI 共識  ███████░░░░  偏多                  │
└─────────────────────────────────────────────┘
```

**顏色規則：**
- 偏多（buy）→ `var(--up-color)`（紅色，台股慣例漲紅）
- 偏空（sell）→ `var(--down-color)`（綠色，台股慣例跌綠）
- 觀望（hold）→ `var(--muted)`（灰色）

### 實作步驟

**Step 1** — `StrategyPanel.vue`：新增 CSS class 函數

```js
function actionClass(action) {
  const parsed = String(action || "").toLowerCase();
  if (parsed === "buy") return "action-buy";
  if (parsed === "sell") return "action-sell";
  return "action-hold";
}

function confidencePct(confidence) {
  const v = parseFloat(confidence);
  if (isNaN(v)) return 0;
  return Math.round(v * 100);
}

function componentScore(item) {
  const v = parseFloat(item?.score ?? 0);
  return Math.min(Math.max(Math.round(((v + 1) / 2) * 100), 0), 100);
}
```

**Step 2** — 重構 StrategyPanel.vue 主結構 HTML

```html
<article class="card full-span">
  <p class="label">策略決策</p>

  <template v-if="strategyResult">
    <!-- Action Badge -->
    <div class="strategy-action-row">
      <div class="action-badge" :class="actionClass(strategyResult.action)">
        {{ toActionLabel(strategyResult.action) }}
      </div>
    </div>

    <!-- 信心進度條 -->
    <div class="confidence-row">
      <span class="confidence-label">信心</span>
      <div class="progress-track">
        <div
          class="progress-fill"
          :class="actionClass(strategyResult.action)"
          :style="{ width: confidencePct(strategyResult.confidence) + '%' }"
        ></div>
      </div>
      <span class="confidence-pct">{{ confidencePct(strategyResult.confidence) }}%</span>
    </div>

    <!-- 風險 + 分數 -->
    <div class="strategy-meta-row">
      <span class="sub">風險：{{ toRiskLabel(strategyResult.risk_level) }}</span>
      <span class="sub">分數：{{ fmt(strategyResult.weighted_score, 3) }}</span>
    </div>

    <div class="divider"></div>

    <!-- 分項評估 -->
    <p class="field-title">分項評估</p>
    <div
      v-for="(item, key) in strategyResult.components || {}"
      :key="`comp-${key}`"
      class="component-row"
    >
      <span class="component-name">{{ componentLabel(key) }}</span>
      <div class="progress-track">
        <div
          class="progress-fill"
          :class="item.label === 'bullish' ? 'action-buy' : item.label === 'bearish' ? 'action-sell' : 'action-hold'"
          :style="{ width: componentScore(item) + '%' }"
        ></div>
      </div>
      <span class="component-signal" :class="item.label === 'bullish' ? 'rise' : item.label === 'bearish' ? 'fall' : ''">
        {{ signalLabel(item.label) }}
      </span>
    </div>

    <!-- 決策理由 -->
    <div class="field-box compact-box">
      <p class="field-title">決策理由</p>
      <p v-for="(reason, idx) in strategyResult.reasons || []" :key="`reason-${idx}`" class="sub">
        {{ idx + 1 }}. {{ localize(reason) }}
      </p>
    </div>
  </template>

  <p v-else class="sub">尚未執行策略決策。</p>
</article>
```

**Step 3** — `styles.css`：新增策略視覺樣式

```css
.strategy-action-row {
  display: flex;
  justify-content: center;
  margin: 16px 0 12px;
}

.action-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 140px;
  padding: 12px 24px;
  border-radius: 14px;
  font-size: 1.4rem;
  font-weight: 900;
  letter-spacing: 0.06em;
}

.action-buy {
  background: color-mix(in srgb, var(--up-color) 14%, transparent);
  color: var(--up-color);
  border: 1.5px solid color-mix(in srgb, var(--up-color) 30%, transparent);
}

.action-sell {
  background: color-mix(in srgb, var(--down-color) 14%, transparent);
  color: var(--down-color);
  border: 1.5px solid color-mix(in srgb, var(--down-color) 30%, transparent);
}

.action-hold {
  background: var(--bg-b);
  color: var(--muted);
  border: 1.5px solid var(--border);
}

.confidence-row,
.component-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 8px 0;
}

.confidence-label {
  flex: 0 0 28px;
  font-size: 0.84rem;
  color: var(--muted);
}

.component-name {
  flex: 0 0 72px;
  font-size: 0.84rem;
  color: var(--muted);
}

.progress-track {
  flex: 1;
  height: 7px;
  border-radius: 999px;
  background: var(--bg-b);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 600ms ease;
}

.progress-fill.action-buy  { background: var(--up-color); }
.progress-fill.action-sell { background: var(--down-color); }
.progress-fill.action-hold { background: var(--muted); }

.confidence-pct {
  flex: 0 0 36px;
  text-align: right;
  font-size: 0.88rem;
  font-weight: 700;
}

.component-signal {
  flex: 0 0 36px;
  text-align: right;
  font-size: 0.84rem;
  font-weight: 700;
}

.strategy-meta-row {
  display: flex;
  gap: 20px;
  margin-top: 4px;
  justify-content: center;
}
```

---

## 問題五：K 線圖無觸控支援

### 現況描述

`KlineSvgLayer.vue` 只有 mouse 事件：
```html
@mousemove="emit('mousemove', $event)"
@mouseleave="emit('mouseleave')"
@click="emit('click', $event)"
```

手機上無法顯示 tooltip，下方的 hint 文字「**滑鼠**移動可看單日 OHLC」在手機上也是錯誤的說明。

### 改善方案

在 SVG 上加入 touch events，並在 `useKlineSeries.js` 或 `KlineChart.vue` 中將
touch 座標轉換成與 mouse event 相同的格式，複用現有的 `onMouseMove` 邏輯。

### 實作步驟

**Step 1** — `KlineSvgLayer.vue`：加入 touch 事件綁定

```html
<svg
  ...
  @mousemove="emit('mousemove', $event)"
  @mouseleave="emit('mouseleave')"
  @click="emit('click', $event)"
  @touchstart.prevent="emit('touchstart', $event)"
  @touchmove.prevent="emit('touchmove', $event)"
  @touchend="emit('touchend', $event)"
>
```

同步補充 `defineEmits`：
```js
const emit = defineEmits(["mousemove", "mouseleave", "click", "touchstart", "touchmove", "touchend"]);
```

**Step 2** — `KLineChart.vue`：新增 touch handler 函數

```js
function toSvgPoint(svgEl, clientX) {
  const rect = svgEl.getBoundingClientRect();
  const scaleX = svgEl.viewBox.baseVal.width / rect.width;
  return (clientX - rect.left) * scaleX;
}

function onTouchMove(event) {
  const touch = event.touches[0];
  if (!touch) return;
  const svgEl = event.currentTarget;
  const syntheticX = toSvgPoint(svgEl, touch.clientX);
  onMouseMove({ offsetX: syntheticX / (svgEl.viewBox.baseVal.width / svgEl.getBoundingClientRect().width) });
}

function onTouchEnd() {
  // 觸控結束保留 tooltip（模擬 click 鎖定行為）
  onClick({});
}
```

綁定到 `KlineSvgLayer`：
```html
@touchmove="onTouchMove"
@touchend="onTouchEnd"
```

**Step 3** — `KLineChart.vue`：更新 hint 文字

```html
<!-- 舊 -->
<p class="hint-tip">滑鼠移動可看單日 OHLC 與量能，點一下可鎖定 tooltip，再點一次取消。</p>

<!-- 新 -->
<p class="hint-tip">移動（或觸控滑動）可看單日 OHLC 與量能，點一下鎖定，再點取消。</p>
```

---

## 問題六：AI 分析結果資訊架構混亂

### 現況描述

AI 分析結果（`AIPanel.vue`）的 card 順序：
1. AI 共識結論
2. 市場情緒
3. 技術指標快照
4. **成本摘要**（`本次成本（美元）：0.00000012`）← 技術細節與分析結論同等展示
5. 各 provider 個別結果（GPT-5、Claude、Grok、DeepSeek）

問題：
- 成本摘要 0.00000012 美元，顯示 8 位小數，對一般使用者完全無意義
- 各 provider 卡片堆疊，讓整頁很長但多數資訊不重要
- 使用者最想看的「AI 共識結論」被淹沒在一堆卡片中

### 改善方案：資訊分層

**主要層（常態顯示）：**
- AI 共識結論（含 signal、confidence、summary）
- 市場情緒摘要

**次要層（預設摺疊，可展開）：**
- 技術指標快照
- 各 provider 個別結果

**隱藏層（移至設定頁或完全隱藏）：**
- 成本摘要（或改為只在設定頁顯示累計消費）

### 實作步驟

**Step 1** — `AIPanel.vue`：新增 `showDetail` 展開狀態

```js
import { ref } from "vue";
const showDetail = ref(false);
```

**Step 2** — 重構 AI 結果區段

```html
<!-- 主要：共識 + 情緒 -->
<article class="card full-span">
  <p class="label">AI 共識結論</p>
  <p class="value" :class="aiResult.consensus.signal === 'bullish' ? 'rise' : aiResult.consensus.signal === 'bearish' ? 'fall' : ''">
    {{ toSignalLabel(aiResult.consensus.signal) }}（信心 {{ fmt(aiResult.consensus.confidence, 2) }}）
  </p>
  <p class="sub">{{ localize(aiResult.consensus.summary) }}</p>
  <p class="sub muted">主導：{{ providerLabel(aiResult.consensus.source_provider || "未知") }}</p>
</article>

<article class="card full-span">
  <p class="label">市場情緒</p>
  <p class="sub">方向：{{ toSignalLabel(aiResult.sentiment_context?.market_sentiment) }}</p>
  <p class="sub">{{ localize(aiResult.sentiment_context?.summary, "尚無情緒摘要") }}</p>
</article>

<!-- 展開按鈕 -->
<button class="detail-toggle" @click="showDetail = !showDetail">
  {{ showDetail ? "▲ 收起詳細資訊" : "▼ 展開各模型詳情" }}
</button>

<!-- 次要：各 provider + 技術指標（摺疊） -->
<template v-if="showDetail">
  <article class="card">
    <p class="label">技術指標快照</p>
    <!-- ... 原有內容 ... -->
  </article>

  <article v-for="item in aiResult.results" :key="item.provider" class="card">
    <!-- ... 原有各 provider 內容 ... -->
  </article>
</template>
```

**Step 3** — `styles.css`：展開按鈕樣式

```css
.detail-toggle {
  width: 100%;
  margin: 4px 0 8px;
  padding: 10px;
  border: 1px dashed var(--border);
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  font-size: 0.86rem;
  font-weight: 600;
  cursor: pointer;
  transition: border-color 200ms, color 200ms;
}

.detail-toggle:hover {
  border-color: var(--brand);
  color: var(--brand);
}
```

**Step 4** — 成本摘要處理

將「成本摘要」card 從 AI 分析結果中移除，
改在 `SettingsView.vue` 的系統狀態區塊加入一行：

```html
<p class="sub">今日 AI 消費：${{ (dailyCost || 0).toFixed(4) }} USD</p>
```

---

## 問題七：空狀態缺乏引導設計

### 現況描述

使用者第一次打開行情頁，只有：
- 一個輸入框
- 一行小字提示「支援台股代號與中文名稱模糊搜尋，例如 2330、台積電、00878」

沒有任何引導性的視覺元素幫助新用戶快速體驗功能。

### 改善方案：熱門股票快捷入口

在輸入框下方（僅在 `quote === null` 時顯示）加入快捷股票按鈕：

```
┌────────────────────────────────────────────────┐
│  熱門                                           │
│  [ 台積電 2330 ]  [ 聯發科 2454 ]  [ 00878 ]   │
│  [ 鴻海 2317   ]  [ 玉山金 2884 ]  [ 00919 ]   │
└────────────────────────────────────────────────┘
```

點擊後直接填入代號並觸發查詢，使用者一鍵即可看到結果。

### 實作步驟

**Step 1** — `QuotePanel.vue`：新增 shortcut 常數

```js
const SHORTCUTS = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
  { symbol: "2884", name: "玉山金" },
  { symbol: "0050", name: "元大 0050" },
  { symbol: "00878", name: "國泰永續" },
];

function onShortcut(item) {
  emit("update:symbol", item.symbol);
  emit("refresh");
}
```

**Step 2** — 在 HTML 加入快捷入口（條件顯示）

```html
<div v-if="!quote && !quoteLoading" class="shortcut-section">
  <p class="field-title">熱門</p>
  <div class="shortcut-row">
    <button
      v-for="item in SHORTCUTS"
      :key="item.symbol"
      type="button"
      class="shortcut-btn"
      @click="onShortcut(item)"
    >
      <span class="shortcut-name">{{ item.name }}</span>
      <span class="shortcut-symbol">{{ item.symbol }}</span>
    </button>
  </div>
</div>
```

**Step 3** — `styles.css`：快捷按鈕樣式

```css
.shortcut-section {
  margin-top: 14px;
}

.shortcut-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 8px;
}

.shortcut-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-card);
  cursor: pointer;
  transition: border-color 200ms, background 200ms;
}

.shortcut-btn:hover {
  border-color: var(--brand);
  background: var(--brand-soft);
}

.shortcut-name {
  font-size: 0.82rem;
  color: var(--muted);
}

.shortcut-symbol {
  font-size: 1rem;
  font-weight: 800;
  color: var(--ink);
}
```

---

## 問題八：主題切換重複兩處

### 現況描述

深淺主題切換按鈕存在於兩處：
1. `App.vue` Header 右上角（月亮/太陽 SVG icon）
2. `SettingsView.vue` 外觀設定區（「切換至深色模式」文字按鈕）

造成重複，且設定頁按鈕使用的是普通 `.btn` 樣式，不像「設定頁的 toggle」。

### 改善方案

**移除 Header 的切換按鈕**，保留設定頁入口，
並將設定頁的按鈕升級為更有質感的 **Toggle Switch 元件**：

```
外觀設定
深色模式      ●───○   ← toggle switch，開啟時滑塊在右
```

### 實作步驟

**Step 1** — `App.vue`：移除 Header 的 `theme-toggle` 按鈕

刪除以下整段：
```html
<button type="button" class="theme-toggle" ...>
  <svg v-if="theme === 'dark'" ...>...</svg>
  <svg v-else ...>...</svg>
</button>
```

同時移除 `App.vue` 中 `useTheme` 的引用（改由 SettingsView 負責）。

**Step 2** — `SettingsView.vue`：改為 Toggle Switch

```html
<div class="settings-row">
  <div class="settings-row-label">
    <span>深色模式</span>
    <span class="settings-row-desc">深色背景，保護夜間視力</span>
  </div>
  <button
    type="button"
    class="toggle-switch"
    :class="{ active: theme === 'dark' }"
    role="switch"
    :aria-checked="theme === 'dark'"
    @click="toggleTheme"
  >
    <span class="toggle-knob"></span>
  </button>
</div>
```

**Step 3** — `styles.css`：Toggle Switch 樣式

```css
.toggle-switch {
  flex: 0 0 auto;
  width: 46px;
  height: 26px;
  border-radius: 999px;
  border: none;
  background: var(--border);
  cursor: pointer;
  position: relative;
  transition: background 220ms ease;
  padding: 0;
}

.toggle-switch.active {
  background: var(--brand);
}

.toggle-knob {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.2);
  transition: transform 220ms ease;
}

.toggle-switch.active .toggle-knob {
  transform: translateX(20px);
}

.settings-row-label {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.settings-row-desc {
  font-size: 0.8rem;
  color: var(--muted);
}
```

---

## 改善優先級總表

| # | 問題 | 使用者影響 | 實作複雜度 | 優先級 |
|---|------|-----------|-----------|-------|
| 2 | 報價卡片缺 % 漲跌幅 + 收盤價太小 | 核心資訊缺失 | 低 | **P0** |
| 7 | 空狀態缺熱門股票快捷入口 | 新用戶冷啟動障礙 | 低 | **P0** |
| 4 | 策略決策無色彩 badge + 進度條 | 結論不一目瞭然 | 低~中 | **P1** |
| 3 | 技術指標無判讀標籤（RSI 超買/超賣等） | 數字對非專業者無意義 | 低 | **P1** |
| 1 | AI 頁 disabled 輸入框 + 跨頁依賴 | 首次使用者困惑 | 中 | **P1** |
| 6 | AI 分析結果成本摘要是一級資訊 | 技術細節干擾閱讀 | 低 | **P1** |
| 8 | 主題切換重複 + 缺 toggle switch | 設定頁不一致 | 低 | **P2** |
| 5 | K 線圖無觸控支援 | 手機 chart 靜態 | 中 | **P2** |

---

## 修改的檔案清單

```text
frontend/src/
├── App.vue
│   └── 移除 header 的 theme-toggle 按鈕
│
├── styles.css
│   └── 新增：.hero-quote-card、.quote-price-row、.quote-close（大字）
│   └── 新增：.indicator-row、.indicator-tag
│   └── 新增：.action-badge、.action-buy/sell/hold
│   └── 新增：.progress-track、.progress-fill
│   └── 新增：.shortcut-btn、.shortcut-row
│   └── 新增：.toggle-switch、.toggle-knob
│   └── 新增：.detail-toggle
│
├── components/
│   ├── QuotePanel.vue
│   │   └── 重構報價 Hero Card（加 % 漲跌幅、收盤價大字）
│   │   └── 重構技術指標區（加判讀標籤、縮減小數位）
│   │   └── 新增空狀態熱門股票快捷入口
│   │
│   ├── StrategyPanel.vue
│   │   └── 新增 Action Badge（偏多/偏空/觀望 + 顏色）
│   │   └── 新增信心進度條
│   │   └── 新增分項評估進度條
│   │
│   ├── AIPanel.vue
│   │   └── 解除 symbol 輸入框的 disabled
│   │   └── 成本摘要從主要 card 移除或摺疊
│   │   └── 各 provider 詳情加展開/摺疊
│   │
│   ├── SettingsView.vue
│   │   └── 主題切換改為 Toggle Switch 元件
│   │
│   └── kline/
│       └── KlineSvgLayer.vue
│           └── 加入 @touchstart、@touchmove、@touchend
│
└── composables/
    └── （如採方案 A）useQuoteHistory.js 或 App.vue 調整
        quote 未取得時的 AI 分析前置補查邏輯
```

---

*本文件為 StockMai UI 改善規格書，所有章節均為規劃討論稿，實作前請對照實際 component 結構確認相容性。*
