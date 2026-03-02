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
  dayOptions: { type: Array, default: () => [5, 20, 90, 180] },
});

const emit = defineEmits(["update:symbol", "refresh", "change-day"]);

const { searchResults, searchLoading, searchError, clearSearch, scheduleSearch } = useStockSymbolSearch();

const SHORTCUTS = [
  { symbol: "2330", name: "台積電" },
  { symbol: "2317", name: "鴻海" },
  { symbol: "2454", name: "聯發科" },
  { symbol: "2884", name: "玉山金" },
  { symbol: "0050", name: "元大台灣50" },
  { symbol: "00878", name: "國泰永續高股息" },
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
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function fmtVol(value) {
  if (!value && value !== 0) return "--";
  return new Intl.NumberFormat("zh-TW").format(value);
}

function fmtPct(change, close) {
  const c = Number(change);
  const p = Number(close);
  if (!Number.isFinite(c) || !Number.isFinite(p) || p <= 0) return "";
  const prev = p - c;
  if (prev <= 0) return "";
  return `${((c / prev) * 100).toFixed(2)}%`;
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
  return String(raw || "").toLowerCase() === "trading" ? "badge-live" : "badge-close";
}

function toNumber(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function pickLatestAndPrev(indicatorPayload) {
  const series = Array.isArray(indicatorPayload?.series) ? indicatorPayload.series : [];
  if (series.length >= 2) {
    return {
      prev: series[series.length - 2] || null,
      latest: series[series.length - 1] || null,
    };
  }

  return {
    prev: null,
    latest: indicatorPayload?.latest || null,
  };
}

function rsiLabel(rsi) {
  const v = toNumber(rsi);
  if (v === null) return "資料不足";
  if (v >= 70) return "過熱";
  if (v >= 55) return "偏強";
  if (v > 45) return "中性";
  if (v > 30) return "偏弱";
  return "超賣";
}

function rsiClass(rsi) {
  const v = toNumber(rsi);
  if (v === null) return "tag-muted";
  if (v >= 70) return "warn-text";
  if (v >= 55) return "tag-rise";
  if (v > 45) return "tag-muted";
  if (v > 30) return "tag-fall";
  return "tag-ok";
}

function maLabel(indicatorPayload) {
  const { prev, latest } = pickLatestAndPrev(indicatorPayload);
  const sma5 = toNumber(latest?.sma5);
  const sma20 = toNumber(latest?.sma20);
  if (sma5 === null || sma20 === null) return "資料不足";

  const prevSma5 = toNumber(prev?.sma5);
  const prevSma20 = toNumber(prev?.sma20);
  if (prevSma5 !== null && prevSma20 !== null && prevSma5 <= prevSma20 && sma5 > sma20) return "黃金交叉";
  if (prevSma5 !== null && prevSma20 !== null && prevSma5 >= prevSma20 && sma5 < sma20) return "死亡交叉";
  if (sma5 > sma20) return "偏多排列";
  if (sma5 < sma20) return "偏空排列";
  return "中性";
}

function maLabelClass(indicatorPayload) {
  const label = maLabel(indicatorPayload);
  if (label === "黃金交叉" || label === "偏多排列") return "tag-rise";
  if (label === "死亡交叉" || label === "偏空排列") return "tag-fall";
  return "tag-muted";
}

function macdDirection(indicatorPayload) {
  const { prev, latest } = pickLatestAndPrev(indicatorPayload);
  const macd = toNumber(latest?.macd);
  const signal = toNumber(latest?.macd_signal);
  if (macd === null || signal === null) return "資料不足";

  const prevMacd = toNumber(prev?.macd);
  const prevSignal = toNumber(prev?.macd_signal);
  if (prevMacd !== null && prevSignal !== null && prevMacd <= prevSignal && macd > signal) return "黃金交叉";
  if (prevMacd !== null && prevSignal !== null && prevMacd >= prevSignal && macd < signal) return "死亡交叉";
  if (macd > signal) return "偏多";
  if (macd < signal) return "偏空";
  return "中性";
}

function macdDirectionClass(indicatorPayload) {
  const direction = macdDirection(indicatorPayload);
  if (direction === "黃金交叉" || direction === "偏多") return "tag-rise";
  if (direction === "死亡交叉" || direction === "偏空") return "tag-fall";
  return "tag-muted";
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
      <span v-if="quoteCheckedAt" class="checked-at no-wrap">更新時間：{{ quoteCheckedAt }}</span>
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

  <div v-if="!quote && !quoteLoading && !quoteError" class="shortcut-section">
    <p class="field-title">快速查詢</p>
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
          <span class="quote-change-pct">({{ fmtPct(quote.change, quote.close) }})</span>
        </div>
      </div>

      <div class="quote-ohlv-row">
        <span>開 {{ fmt(quote.open) }}</span>
        <span class="ohlv-divider">•</span>
        <span>高 {{ fmt(quote.high) }}</span>
        <span class="ohlv-divider">•</span>
        <span>低 {{ fmt(quote.low) }}</span>
        <span class="ohlv-divider">•</span>
        <span>量 {{ fmtVol(quote.volume) }} 張</span>
      </div>

      <p class="quote-meta-line">
        {{ quote.as_of_date }}
        • {{ quote.is_realtime ? "即時報價" : "日線報價" }}
        • 來源：{{ quote.source || "--" }}
      </p>
    </article>

    <article class="card full-span">
      <p class="label">技術指標</p>
      <template v-if="indicators?.latest">
        <div class="indicator-row">
          <span class="indicator-name">MA5 / MA20</span>
          <span class="indicator-value">{{ fmt(indicators.latest.sma5) }} / {{ fmt(indicators.latest.sma20) }}</span>
          <span class="indicator-tag" :class="maLabelClass(indicators)">
            {{ maLabel(indicators) }}
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
          <span class="indicator-tag" :class="macdDirectionClass(indicators)">
            {{ macdDirection(indicators) }}
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

    <article class="card full-span">
      <p class="label">最近 {{ history?.days || selectedDays }} 天 K 線</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">暫無 K 線資料</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>
  </div>
</template>
