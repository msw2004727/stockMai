<script setup>
import QuotePanel from "./QuotePanel.vue";

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
</script>

<template>
  <div class="view-container market-view-container">
    <div class="panel">
      <QuotePanel
        :symbol="symbol"
        :quote="quote"
        :quote-loading="quoteLoading"
        :quote-error="quoteError"
        :quote-checked-at="quoteCheckedAt"
        :history="history"
        :history-error="historyError"
        :indicators="indicators"
        :indicators-error="indicatorsError"
        :market-movers="marketMovers"
        :market-movers-loading="marketMoversLoading"
        :market-movers-error="marketMoversError"
        :intel-overview="intelOverview"
        :intel-overview-loading="intelOverviewLoading"
        :intel-overview-error="intelOverviewError"
        :intel-deep="intelDeep"
        :intel-deep-loading="intelDeepLoading"
        :intel-deep-error="intelDeepError"
        :intel-status="intelStatus"
        :intel-status-error="intelStatusError"
        :selected-days="selectedDays"
        :day-options="dayOptions"
        @update:symbol="emit('update:symbol', $event)"
        @refresh="emit('refresh')"
        @change-day="emit('change-day', $event)"
      />
    </div>
  </div>
</template>
