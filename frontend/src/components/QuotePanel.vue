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
</script>

<template>
  <h2 class="section-title">股票報價查詢</h2>
  <p class="hint">輸入 4 碼台股代號（例如：2330、2317、0050）</p>

  <div class="query-row">
    <input
      :value="symbol"
      class="input"
      type="text"
      maxlength="4"
      inputmode="numeric"
      placeholder="輸入股票代號"
      @input="onSymbolInput"
    />
    <button type="button" class="btn" :disabled="quoteLoading" @click="emit('refresh')">
      {{ quoteLoading ? "查詢中..." : "查詢報價" }}
    </button>
    <span v-if="quoteCheckedAt" class="checked-at">最後查詢：{{ quoteCheckedAt }}</span>
  </div>

  <div class="period-row">
    <span class="period-label">週期：</span>
    <button
      v-for="d in dayOptions"
      :key="d"
      type="button"
      class="period-btn"
      :class="{ active: selectedDays === d }"
      :disabled="quoteLoading"
      @click="emit('change-day', d)"
    >
      {{ d }}D
    </button>
  </div>

  <div v-if="quoteError" class="card error">{{ quoteError }}</div>

  <div v-else-if="quote" class="grid quote-grid">
    <article class="card">
      <p class="label">股票</p>
      <p class="value">{{ quote.symbol }} {{ quote.name }}</p>
      <p class="sub">日期：{{ quote.as_of_date }}</p>
    </article>

    <article class="card">
      <p class="label">開高低收</p>
      <p class="sub">開：{{ quote.open }}</p>
      <p class="sub">高：{{ quote.high }}</p>
      <p class="sub">低：{{ quote.low }}</p>
      <p class="sub">收：{{ quote.close }}</p>
    </article>

    <article class="card">
      <p class="label">漲跌 / 成交量</p>
      <p class="value" :class="quote.change >= 0 ? 'ok' : 'warn'">{{ quote.change }}</p>
      <p class="sub">成交量：{{ quote.volume }}</p>
    </article>

    <article class="card">
      <p class="label">資料來源</p>
      <p class="value">{{ quote.source }}</p>
      <p class="sub" v-if="quote.note">{{ quote.note }}</p>
    </article>

    <article class="card full-span">
      <p class="label">近 {{ history?.days || 0 }} 日收盤趨勢</p>
      <PriceTrendChart v-if="history?.series?.length" :points="history.series" />
      <p v-else class="sub">暫無可視化資料</p>
      <p v-if="historyError" class="sub warn-text">{{ historyError }}</p>
    </article>

    <article class="card full-span">
      <p class="label">近 {{ history?.days || 0 }} 日 K 線（OHLC）</p>
      <KLineChart v-if="history?.ohlc?.length" :ohlc="history.ohlc" />
      <p v-else class="sub">暫無 K 線資料</p>
    </article>
  </div>
</template>
