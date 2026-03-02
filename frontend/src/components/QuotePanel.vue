<script setup>
import KLineChart from "./KLineChart.vue";

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
    return "暫無資料";
  }
  return Number(value).toFixed(4);
}

function marketStateLabel(raw) {
  const value = String(raw || "").toLowerCase();
  if (value === "trading") {
    return "交易中";
  }
  if (value === "daily_close" || value === "post_close") {
    return "收盤後";
  }
  return "未知";
}
</script>

<template>
  <h2 class="section-title">行情查詢</h2>
  <p class="hint hint-inline">支援 4~6 碼台股代號，例如 2330、2485、00878</p>

  <div class="field-box">
    <p class="field-title">查詢條件</p>
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
        {{ quoteLoading ? "查詢中..." : "查詢股價" }}
      </button>
      <span v-if="quoteCheckedAt" class="checked-at no-wrap">更新時間：{{ quoteCheckedAt }}</span>
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
    <article class="card">
      <p class="label">股票資訊</p>
      <p class="value">{{ quote.symbol }} {{ quote.name }}</p>
      <p class="sub">資料日期：{{ quote.as_of_date }}</p>
      <p class="sub">報價時間：{{ quote.quote_time || "暫無資料" }}</p>
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
      <p class="label">漲跌與量能</p>
      <p class="value" :class="quote.change >= 0 ? 'rise' : 'fall'">{{ quote.change }}</p>
      <p class="sub">成交量：{{ quote.volume }}</p>
    </article>

    <article class="card">
      <p class="label">資料來源</p>
      <p class="value">{{ quote.source || "暫無資料" }}</p>
      <p class="sub" v-if="quote.note">{{ quote.note }}</p>
    </article>

    <article class="card full-span">
      <p class="label">技術指標（最近 60 日）</p>
      <template v-if="indicators?.latest">
        <p class="sub">SMA5（5 日均線）：{{ fmt(indicators.latest.sma5) }}</p>
        <p class="sub">SMA20（20 日均線）：{{ fmt(indicators.latest.sma20) }}</p>
        <p class="sub">RSI14（相對強弱）：{{ fmt(indicators.latest.rsi14) }}</p>
        <p class="sub">MACD（趨勢動能）：{{ fmt(indicators.latest.macd) }}</p>
        <p class="sub">Signal（訊號線）：{{ fmt(indicators.latest.macd_signal) }}</p>
        <p class="sub">Histogram（柱狀差）：{{ fmt(indicators.latest.macd_hist) }}</p>
        <p class="sub">來源：{{ indicators.history_source }}</p>
      </template>
      <p v-else class="sub">暫無技術指標資料</p>
      <p v-if="indicatorsError" class="sub warn-text">{{ indicatorsError }}</p>
    </article>

    <article class="card full-span">
      <p class="label">最近 {{ history?.days || selectedDays }} 日 K 線（含走勢線，可切換顯示）</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">暫無 K 線資料</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>
  </div>
</template>
