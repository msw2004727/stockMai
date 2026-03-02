<script setup>
import KLineChart from "./KLineChart.vue";
import { useStockSymbolSearch } from "../composables/useStockSymbolSearch";

defineProps({
  symbol: { type: String, default: "" },
  quote: { type: Object, default: null },
  quoteLoading: { type: Boolean, default: false },
  quoteError: { type: String, default: "" },
  quoteCheckedAt: { type: String, default: "" },
  history: { type: Object, default: null },
  historyError: { type: String, default: "" },
  indicators: { type: Object, default: null },
  indicatorsError: { type: String, default: "" },
  selectedDays: { type: Number, default: 5 },
  dayOptions: { type: Array, default: () => [5, 20] },
});

const emit = defineEmits(["update:symbol", "refresh", "change-day"]);

const { searchResults, searchLoading, searchError, clearSearch, scheduleSearch } = useStockSymbolSearch();

const SHORTCUTS = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
  { symbol: "2884", name: "玉山金" },
  { symbol: "0050", name: "元大 0050" },
  { symbol: "00878", name: "國泰永續" },
];

function onSymbolInput(event) {
  const value = event.target.value;
  emit("update:symbol", value);
  scheduleSearch(value);
}

function onSelectSearchResult(item) {
  if (!item?.symbol) return;
  emit("update:symbol", item.symbol);
  clearSearch();
}

function onRefreshClick() {
  clearSearch();
  emit("refresh");
}

function onShortcut(item) {
  emit("update:symbol", item.symbol);
  clearSearch();
  emit("refresh");
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "－";
  return Number(value).toFixed(digits);
}

function fmtVol(value) {
  if (!value && value !== 0) return "－";
  return new Intl.NumberFormat("zh-TW").format(value);
}

function fmtPct(change, close) {
  const c = Number(change);
  const p = Number(close);
  if (!Number.isFinite(c) || !Number.isFinite(p) || p <= 0) return "";
  const prev = p - c;
  if (prev <= 0) return "";
  return ((c / prev) * 100).toFixed(2) + "%";
}

function marketStateLabel(raw) {
  const value = String(raw || "").toLowerCase();
  if (value === "trading") return "交易中";
  if (value === "pre_open") return "開盤前";
  if (value === "market_holiday") return "休市（假日）";
  if (value === "daily_close" || value === "post_close") return "休市中";
  return "休市中";
}

function marketStateBadgeClass(raw) {
  const value = String(raw || "").toLowerCase();
  if (value === "trading") return "badge-live";
  return "badge-close";
}

// ── 技術指標判讀 ──────────────────────────────────────────────
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
  if (v <= 30) return "tag-ok";
  return "tag-muted";
}

function macdDirection(macd, signal) {
  const m = parseFloat(macd);
  const s = parseFloat(signal);
  if (isNaN(m) || isNaN(s)) return "";
  return m > s ? "偏多" : "偏空";
}

function macdDirectionClass(macd, signal) {
  const m = parseFloat(macd);
  const s = parseFloat(signal);
  if (isNaN(m) || isNaN(s)) return "";
  return m > s ? "tag-rise" : "tag-fall";
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
  return a > b ? "tag-rise" : "tag-fall";
}
</script>

<template>
  <h2 class="section-title">行情查詢</h2>
  <p class="hint hint-inline">支援台股代號與中文名稱模糊搜尋，例如 2330、台積電、00878</p>

  <div class="field-box">
    <p class="field-title">查詢條件</p>
    <div class="query-row">
      <input
        :value="symbol"
        class="input"
        type="text"
        maxlength="20"
        inputmode="text"
        placeholder="輸入台股代號或中文名稱"
        @input="onSymbolInput"
        @keydown.enter.prevent="onRefreshClick"
      />
      <button type="button" class="btn" :disabled="quoteLoading" @click="onRefreshClick">
        {{ quoteLoading ? "查詢中..." : "查詢股價" }}
      </button>
      <span v-if="quoteCheckedAt" class="checked-at no-wrap">更新：{{ quoteCheckedAt }}</span>
    </div>

    <p v-if="searchLoading" class="sub">正在搜尋代號...</p>
    <p v-else-if="searchError" class="sub warn-text">{{ searchError }}</p>
    <ul v-else-if="searchResults.length" class="search-list" role="listbox" aria-label="股票代號建議">
      <li v-for="item in searchResults" :key="item.symbol" class="search-item-wrap">
        <button
          type="button"
          class="search-item"
          @mousedown.prevent="onSelectSearchResult(item)"
          @click="onSelectSearchResult(item)"
        >
          <span class="search-symbol">{{ item.symbol }}</span>
          <span class="search-name">{{ item.name }}</span>
        </button>
      </li>
    </ul>
  </div>

  <!-- 空狀態：熱門快捷入口 -->
  <div v-if="!quote && !quoteLoading && !quoteError" class="shortcut-section">
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

  <div class="field-box">
    <p class="field-title">歷史區間</p>
    <div class="period-row">
      <button
        v-for="d in dayOptions"
        :key="d"
        type="button"
        class="period-btn"
        :class="{ active: selectedDays === d }"
        :disabled="quoteLoading"
        @click="emit('change-day', d)"
      >
        {{ d }} 天
      </button>
    </div>
  </div>

  <div v-if="quoteError" class="card error">{{ quoteError }}</div>

  <div v-else-if="quote" class="grid quote-grid">

    <!-- Hero 報價卡 -->
    <article class="card hero-quote-card full-span">
      <div class="quote-title-row">
        <span class="quote-symbol">{{ quote.symbol }}</span>
        <span class="quote-name">{{ quote.name }}</span>
        <span class="market-state-badge" :class="marketStateBadgeClass(quote.market_state)">
          {{ marketStateLabel(quote.market_state) }}
        </span>
      </div>

      <div class="quote-price-row">
        <span class="quote-close" :class="Number(quote.change) >= 0 ? 'rise' : 'fall'">
          {{ fmt(quote.close) }}
        </span>
        <div class="quote-change-block" :class="Number(quote.change) >= 0 ? 'rise' : 'fall'">
          <span class="quote-change-arrow">{{ Number(quote.change) >= 0 ? '▲' : '▼' }}</span>
          <span class="quote-change-value">{{ fmt(Math.abs(quote.change)) }}</span>
          <span class="quote-change-pct">（{{ fmtPct(quote.change, quote.close) }}）</span>
        </div>
      </div>

      <div class="quote-ohlv-row">
        <span>開 {{ fmt(quote.open) }}</span>
        <span class="ohlv-divider">·</span>
        <span>高 {{ fmt(quote.high) }}</span>
        <span class="ohlv-divider">·</span>
        <span>低 {{ fmt(quote.low) }}</span>
        <span class="ohlv-divider">·</span>
        <span>量 {{ fmtVol(quote.volume) }} 張</span>
      </div>

      <p class="quote-meta-line">
        {{ quote.as_of_date }}
        · {{ quote.is_realtime ? "即時報價" : "日線報價" }}
        · 來源：{{ quote.source || "－" }}
      </p>
    </article>

    <!-- 技術指標 -->
    <article class="card full-span">
      <p class="label">技術指標</p>
      <template v-if="indicators?.latest">
        <div class="indicator-row">
          <span class="indicator-name">MA5 / MA20</span>
          <span class="indicator-value">{{ fmt(indicators.latest.sma5) }} / {{ fmt(indicators.latest.sma20) }}</span>
          <span class="indicator-tag" :class="maLabelClass(indicators.latest.sma5, indicators.latest.sma20)">
            {{ maLabel(indicators.latest.sma5, indicators.latest.sma20) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">RSI14</span>
          <span class="indicator-value">{{ fmt(indicators.latest.rsi14, 1) }}</span>
          <span class="indicator-tag" :class="rsiClass(indicators.latest.rsi14)">
            {{ rsiLabel(indicators.latest.rsi14) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">MACD / Signal</span>
          <span class="indicator-value">{{ fmt(indicators.latest.macd) }} / {{ fmt(indicators.latest.macd_signal) }}</span>
          <span class="indicator-tag" :class="macdDirectionClass(indicators.latest.macd, indicators.latest.macd_signal)">
            {{ macdDirection(indicators.latest.macd, indicators.latest.macd_signal) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">MACD Hist</span>
          <span class="indicator-value">{{ fmt(indicators.latest.macd_hist) }}</span>
          <span class="indicator-tag tag-muted">來源：{{ indicators.history_source }}</span>
        </div>
      </template>
      <p v-else class="sub">暫無技術指標資料</p>
      <p v-if="indicatorsError" class="sub warn-text">{{ indicatorsError }}</p>
    </article>

    <!-- K 線圖 -->
    <article class="card full-span">
      <p class="label">最近 {{ history?.days || selectedDays }} 日 K 線</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">暫無 K 線資料</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>

  </div>
</template>
