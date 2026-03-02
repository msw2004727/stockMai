<script setup>
import { onMounted } from "vue";

import HealthPanel from "./components/HealthPanel.vue";
import QuotePanel from "./components/QuotePanel.vue";
import { useHealthStatus } from "./composables/useHealthStatus";
import { useQuoteHistory } from "./composables/useQuoteHistory";

const { health, healthLoading, healthError, healthCheckedAt, refreshHealth } = useHealthStatus();
const {
  symbol,
  quote,
  quoteLoading,
  quoteError,
  quoteCheckedAt,
  history,
  historyError,
  selectedDays,
  dayOptions,
  refreshQuote,
  setDayRange,
} = useQuoteHistory("2330");

function updateSymbol(value) {
  symbol.value = value;
}

onMounted(() => {
  refreshHealth();
  refreshQuote();
});
</script>

<template>
  <main class="screen">
    <section class="panel">
      <p class="eyebrow">stockMai H5 MVP</p>
      <h1>後端連線狀態面板</h1>
      <p class="hint">上半部檢查服務健康度，下半部查詢第一支股票報價 API</p>

      <HealthPanel
        :health="health"
        :health-loading="healthLoading"
        :health-error="healthError"
        :health-checked-at="healthCheckedAt"
        @refresh="refreshHealth"
      />

      <div class="divider"></div>

      <QuotePanel
        :symbol="symbol"
        :quote="quote"
        :quote-loading="quoteLoading"
        :quote-error="quoteError"
        :quote-checked-at="quoteCheckedAt"
        :history="history"
        :history-error="historyError"
        :selected-days="selectedDays"
        :day-options="dayOptions"
        @update:symbol="updateSymbol"
        @refresh="refreshQuote"
        @change-day="setDayRange"
      />
    </section>
  </main>
</template>
