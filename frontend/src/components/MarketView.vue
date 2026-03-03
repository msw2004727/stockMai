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
  selectedDays: { type: Number, default: 5 },
  dayOptions: { type: Array, default: () => [5, 20, 90, 180] },
});

const emit = defineEmits(["update:symbol", "refresh", "change-day"]);
</script>

<template>
  <div class="view-container">
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
        :selected-days="selectedDays"
        :day-options="dayOptions"
        @update:symbol="emit('update:symbol', $event)"
        @refresh="emit('refresh')"
        @change-day="emit('change-day', $event)"
      />
    </div>
  </div>
</template>
