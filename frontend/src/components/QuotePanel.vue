<script setup>
import KLineChart from "./KLineChart.vue";
import StockIntelPanel from "./StockIntelPanel.vue";
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
  marketMovers: { type: Object, default: null },
  marketMoversLoading: { type: Boolean, default: false },
  marketMoversError: { type: String, default: "" },
  intelOverview: { type: Object, default: null },
  intelOverviewLoading: { type: Boolean, default: false },
  intelOverviewError: { type: String, default: "" },
  intelDeep: { type: Object, default: null },
  intelDeepLoading: { type: Boolean, default: false },
  intelDeepError: { type: String, default: "" },
  intelStatus: { type: Object, default: null },
  intelStatusError: { type: String, default: "" },
  selectedDays: { type: Number, default: 5 },
  dayOptions: { type: Array, default: () => [5, 20, 90, 180] },
});

const emit = defineEmits(["update:symbol", "refresh", "change-day"]);

const { searchResults, searchLoading, searchError, clearSearch, scheduleSearch } = useStockSymbolSearch();

const MOVER_GROUPS = [
  { key: "top_volume", title: "六大成交量", icon: "▦", tone: "volume" },
  { key: "top_gainers", title: "六大漲幅", icon: "▲", tone: "gainers" },
  { key: "top_losers", title: "六大跌幅", icon: "▼", tone: "losers" },
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

function onShortcut(symbol) {
  emit("update:symbol", symbol);
  clearSearch();
  emit("refresh");
}

function moversByCategory(payload, categoryKey) {
  if (!payload || !payload.categories) {
    return [];
  }
  const rows = payload.categories[categoryKey];
  return Array.isArray(rows) ? rows : [];
}

function moversLabel(item) {
  const name = String(item?.name || "").trim();
  if (name) return name;
  return String(item?.symbol || "--").trim() || "--";
}

function fmtLots(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const safeLots = Math.trunc(Math.max(Number(value), 0));
  return new Intl.NumberFormat("zh-TW", {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(safeLots);
}

function moverPercent(item, categoryKey) {
  const pct = Number(item?.change_pct);
  if (!Number.isFinite(pct)) return "";
  const sign = pct > 0 ? "+" : "";
  if (categoryKey === "top_volume") return `${sign}${pct.toFixed(2)}%`;
  return `${sign}${pct.toFixed(2)}%`;
}

function moverPercentClass(categoryKey) {
  if (categoryKey === "top_gainers") return "mover-pct-up";
  if (categoryKey === "top_losers") return "mover-pct-down";
  return "mover-pct-neutral";
}

function moverVolume(item) {
  return `量 ${fmtLots(item?.volume)} 張`;
}

function moversCoverageText(payload) {
  const ratio = Number(payload?.coverage_ratio);
  const actual = Number(payload?.universe_size);
  const expected = Number(payload?.expected_universe_size);

  if (!Number.isFinite(ratio) || ratio < 0) {
    return "";
  }
  if (Number.isFinite(actual) && actual >= 0 && Number.isFinite(expected) && expected > 0) {
    return `覆蓋率：${(ratio * 100).toFixed(1)}%（樣本 ${actual} / 全市場 ${expected}）`;
  }
  return `覆蓋率：${(ratio * 100).toFixed(1)}%`;
}

function moversFallbackText(payload) {
  const requested = String(payload?.requested_trade_date || "").trim();
  const asOf = String(payload?.as_of_date || "").trim();
  if (!requested || !asOf || requested === asOf) {
    return "";
  }
  return `指定交易日 ${requested} 無資料，已回退到最近可用交易日 ${asOf}`;
}

function isLockedRange(days) {
  return Number(days) === 90 || Number(days) === 180;
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

function isFallbackQuote(payload) {
  const priority = String(payload?.source_priority || "").toLowerCase();
  if (priority === "daily_fallback" || priority === "cache") return true;
  return !Boolean(payload?.is_realtime);
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
    <p class="field-title">前一交易日快速查詢</p>
    <p v-if="marketMovers?.as_of_date" class="sub">交易日：{{ marketMovers.as_of_date }}</p>
    <p v-if="moversCoverageText(marketMovers)" class="sub">{{ moversCoverageText(marketMovers) }}</p>
    <p v-if="moversFallbackText(marketMovers)" class="sub warn-text">{{ moversFallbackText(marketMovers) }}</p>
    <p v-if="marketMovers?.note" class="sub">{{ marketMovers.note }}</p>
    <p v-if="marketMoversLoading" class="sub">正在載入市場排行...</p>
    <p v-else-if="marketMoversError" class="sub warn-text">{{ marketMoversError }}</p>
    <div v-else class="movers-category-grid">
      <article
        v-for="group in MOVER_GROUPS"
        :key="group.key"
        class="movers-category-card"
        :class="`movers-tone-${group.tone}`"
      >
        <p class="movers-category-title">
          <span class="movers-title-icon" aria-hidden="true">{{ group.icon }}</span>
          <span class="movers-title-text">{{ group.title }}</span>
        </p>
        <p v-if="!moversByCategory(marketMovers, group.key).length" class="sub">暫無排行資料</p>
        <div v-else class="movers-shortcut-grid">
          <button
            v-for="item in moversByCategory(marketMovers, group.key)"
            :key="`${group.key}-${item.symbol}`"
            type="button"
            class="shortcut-btn mover-shortcut-btn"
            @click="onShortcut(item.symbol)"
          >
            <span class="mover-name">{{ moversLabel(item) }}</span>
            <span class="mover-symbol">{{ item.symbol }}</span>
            <span
              v-if="moverPercent(item, group.key)"
              class="mover-pct"
              :class="moverPercentClass(group.key)"
            >
              {{ moverPercent(item, group.key) }}
            </span>
            <span class="mover-volume">{{ moverVolume(item) }}</span>
          </button>
        </div>
      </article>
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
        :class="{ active: selectedDays === d, locked: isLockedRange(d) }"
        :disabled="quoteLoading || isLockedRange(d)"
        @click="emit('change-day', d)"
      >
        {{ d }} 天
      </button>
    </div>
  </div>

  <div v-if="quoteError" class="card error">{{ quoteError }}</div>

  <div v-else-if="quote" class="grid quote-grid market-data-grid">
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

      <div class="quote-meta-list" aria-label="報價資訊細節">
        <div class="quote-meta-row">
          <span class="quote-meta-key">交易日</span>
          <span class="quote-meta-value">{{ quote.as_of_date || "--" }}</span>
        </div>
        <div class="quote-meta-row">
          <span class="quote-meta-key">成交時間</span>
          <span class="quote-meta-value">{{ quote.quote_time || "--" }}</span>
        </div>
        <div class="quote-meta-row">
          <span class="quote-meta-key">即時報價來源</span>
          <span class="quote-meta-value">{{ quote.source || "--" }}</span>
        </div>
        <div class="quote-meta-row">
          <span class="quote-meta-key">供應商</span>
          <span class="quote-meta-value">{{ quote.provider_used || "--" }}</span>
        </div>
        <div class="quote-meta-row">
          <span class="quote-meta-key">通道</span>
          <span class="quote-meta-value">{{ quote.source_priority || "--" }}</span>
        </div>
        <div class="quote-meta-row">
          <span class="quote-meta-key">回退</span>
          <span class="quote-meta-value">{{ isFallbackQuote(quote) ? "是" : "否" }}</span>
        </div>
      </div>
    </article>

    <article class="card indicator-card">
      <p class="label">技術指標</p>
      <template v-if="indicators?.latest">
        <div class="indicator-row">
          <span class="indicator-name">均線 (SMA5 / SMA20)</span>
          <span class="indicator-value">{{ fmt(indicators.latest.sma5) }} / {{ fmt(indicators.latest.sma20) }}</span>
          <span class="indicator-tag" :class="maLabelClass(indicators)">
            {{ maLabel(indicators) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">相對強弱 (RSI14)</span>
          <span class="indicator-value">{{ fmt(indicators.latest.rsi14, 1) }}</span>
          <span class="indicator-tag" :class="rsiClass(indicators.latest.rsi14)">
            {{ rsiLabel(indicators.latest.rsi14) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">趨勢動能 (MACD / Signal)</span>
          <span class="indicator-value">{{ fmt(indicators.latest.macd) }} / {{ fmt(indicators.latest.macd_signal) }}</span>
          <span class="indicator-tag" :class="macdDirectionClass(indicators)">
            {{ macdDirection(indicators) }}
          </span>
        </div>
        <div class="indicator-row">
          <span class="indicator-name">柱狀差 (MACD Hist)</span>
          <span class="indicator-value">{{ fmt(indicators.latest.macd_hist) }}</span>
          <span class="indicator-tag tag-muted">來源 (Source)：{{ indicators.history_source }}</span>
        </div>
      </template>
      <p v-else class="sub">暫無技術指標資料</p>
      <p v-if="indicatorsError" class="sub warn-text">{{ indicatorsError }}</p>
    </article>

    <article class="card kline-card">
      <p class="label">最近 {{ history?.days || selectedDays }} 天 K 線</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">暫無 K 線資料</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>

    <article class="card full-span stock-intel-card">
      <StockIntelPanel
        :intel-overview="intelOverview"
        :intel-overview-loading="intelOverviewLoading"
        :intel-overview-error="intelOverviewError"
        :intel-deep="intelDeep"
        :intel-deep-loading="intelDeepLoading"
        :intel-deep-error="intelDeepError"
        :intel-status="intelStatus"
        :intel-status-error="intelStatusError"
      />
    </article>
  </div>
</template>
