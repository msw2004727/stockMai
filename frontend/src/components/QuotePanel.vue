<script setup>
import KLineChart from "./KLineChart.vue";
import PriceTrendChart from "./PriceTrendChart.vue";

defineProps({
  symbol: {
    type: String,
    default: "",
  },
  quote: {
    type: Object,
    default: null,
  },
  quoteLoading: {
    type: Boolean,
    default: false,
  },
  quoteError: {
    type: String,
    default: "",
  },
  quoteCheckedAt: {
    type: String,
    default: "",
  },
  history: {
    type: Object,
    default: null,
  },
  historyError: {
    type: String,
    default: "",
  },
  indicators: {
    type: Object,
    default: null,
  },
  indicatorsError: {
    type: String,
    default: "",
  },
  selectedDays: {
    type: Number,
    default: 5,
  },
  dayOptions: {
    type: Array,
    default: () => [5, 20],
  },
});

const emit = defineEmits(["update:symbol", "refresh", "change-day"]);

function onSymbolInput(event) {
  emit("update:symbol", event.target.value);
}

function fmt(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }
  return Number(value).toFixed(4);
}

function marketStateLabel(raw) {
  const value = String(raw || "").toLowerCase();
  if (value === "trading") {
    return "盤中交易";
  }
  if (value === "daily_close" || value === "post_close") {
    return "收盤資料";
  }
  return "狀態未知";
}
</script>

<template>
  <h2 class="section-title">即時報價與行情</h2>
  <p class="hint hint-inline">支援 4~6 碼台股代號，例如 2330、2485、00878</p>

  <div class="query-row">
    <input
      :value="symbol"
      class="input"
      type="text"
      maxlength="6"
      inputmode="numeric"
      placeholder="輸入台股代號"
      @input="onSymbolInput"
    />
    <button type="button" class="btn" :disabled="quoteLoading" @click="emit('refresh')">
      {{ quoteLoading ? "查詢中..." : "查詢報價" }}
    </button>
    <span v-if="quoteCheckedAt" class="checked-at no-wrap">更新時間：{{ quoteCheckedAt }}</span>
  </div>

  <div class="period-row">
    <span class="period-label">歷史天數：</span>
    <button
      v-for="d in dayOptions"
      :key="d"
      type="button"
      class="period-btn"
      :class="{ active: selectedDays === d }"
      :disabled="quoteLoading"
      @click="emit('change-day', d)"
    >
      {{ d }} 日
    </button>
  </div>

  <div v-if="quoteError" class="card error">{{ quoteError }}</div>

  <div v-else-if="quote" class="grid quote-grid">
    <article class="card">
      <p class="label">股票資訊</p>
      <p class="value">{{ quote.symbol }} {{ quote.name }}</p>
      <p class="sub">資料日期：{{ quote.as_of_date }}</p>
      <p class="sub">報價時間：{{ quote.quote_time || "N/A" }}</p>
      <p class="sub">市場狀態：{{ marketStateLabel(quote.market_state) }}</p>
      <p class="sub">資料類型：{{ quote.is_realtime ? "即時報價" : "日線報價" }}</p>
    </article>

    <article class="card">
      <p class="label">價格區間</p>
      <p class="sub">開盤：{{ quote.open }}</p>
      <p class="sub">最高：{{ quote.high }}</p>
      <p class="sub">最低：{{ quote.low }}</p>
      <p class="sub">收盤：{{ quote.close }}</p>
    </article>

    <article class="card">
      <p class="label">漲跌與成交量</p>
      <p class="value" :class="quote.change >= 0 ? 'ok' : 'warn'">{{ quote.change }}</p>
      <p class="sub">成交量：{{ quote.volume }}</p>
    </article>

    <article class="card">
      <p class="label">資料來源</p>
      <p class="value">{{ quote.source }}</p>
      <p class="sub" v-if="quote.note">{{ quote.note }}</p>
    </article>

    <article class="card">
      <p class="label">技術指標摘要（近 60 日）</p>
      <template v-if="indicators?.latest">
        <p class="sub">SMA5（5日簡單移動平均）：{{ fmt(indicators.latest.sma5) }}</p>
        <p class="sub">SMA20（20日簡單移動平均）：{{ fmt(indicators.latest.sma20) }}</p>
        <p class="sub">RSI14（相對強弱指標）：{{ fmt(indicators.latest.rsi14) }}</p>
        <p class="sub">MACD（趨勢動能指標）：{{ fmt(indicators.latest.macd) }}</p>
        <p class="sub">訊號線（Signal）：{{ fmt(indicators.latest.macd_signal) }}</p>
        <p class="sub">柱狀圖（Histogram）：{{ fmt(indicators.latest.macd_hist) }}</p>
        <p class="sub">指標資料來源：{{ indicators.history_source }}</p>
      </template>
      <p v-else class="sub">目前沒有可用的技術指標資料。</p>
      <p v-if="indicatorsError" class="sub warn-text">{{ indicatorsError }}</p>
    </article>

    <article class="card full-span">
      <p class="label">近 {{ history?.days || 0 }} 日收盤走勢</p>
      <PriceTrendChart v-if="history?.series?.length" :points="history.series" />
      <p v-else class="sub">目前沒有可用的價格走勢資料。</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>

    <article class="card full-span">
      <p class="label">近 {{ history?.days || 0 }} 日 K 線（OHLC）</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">目前沒有可用的 K 線資料。</p>
    </article>
  </div>
</template>

