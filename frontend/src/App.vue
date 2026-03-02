<script setup>
import { computed, onMounted, shallowRef } from "vue";

import AiView from "./components/AiView.vue";
import MarketView from "./components/MarketView.vue";
import SettingsView from "./components/SettingsView.vue";
import TabBar from "./components/TabBar.vue";
import { useAiAnalysis } from "./composables/useAiAnalysis";
import { useHealthStatus } from "./composables/useHealthStatus";
import { useQuoteHistory } from "./composables/useQuoteHistory";
import { useStrategyDecision } from "./composables/useStrategyDecision";

const activeTab = shallowRef("market");

const { health, healthLoading, healthError, healthCheckedAt, refreshHealth } = useHealthStatus();
const {
  symbol,
  quote,
  quoteLoading,
  quoteError,
  quoteCheckedAt,
  history,
  historyError,
  indicators,
  indicatorsError,
  selectedDays,
  dayOptions,
  refreshQuote,
  setDayRange,
} = useQuoteHistory("");

const {
  aiResult,
  aiLoading,
  aiError,
  aiCheckedAt,
  userPrompt,
  selectedProvider,
  providerOptions,
  refreshAi,
  setProvider,
  showAiPrerequisiteError,
} = useAiAnalysis(symbol, "gpt5");

const {
  strategyResult,
  strategyLoading,
  strategyError,
  strategyCheckedAt,
  refreshStrategy,
  showStrategyPrerequisiteError,
} = useStrategyDecision(symbol, userPrompt, selectedProvider);

const loadingMessage = computed(() => {
  if (aiLoading.value || strategyLoading.value) return "AI 分析中，請稍候...";
  if (quoteLoading.value) return "行情查詢中，請稍候...";
  return "";
});

const showLoadingOverlay = computed(() => Boolean(loadingMessage.value));

function updateSymbol(value) {
  symbol.value = value;
}

function updateUserPrompt(value) {
  userPrompt.value = value;
}

function refreshAiAndStrategy() {
  const sym = String(symbol.value || "").trim();
  if (!sym) {
    const message = "請先輸入股票代號";
    showAiPrerequisiteError(message);
    showStrategyPrerequisiteError(message);
    return;
  }
  refreshAi();
  refreshStrategy();
}

onMounted(() => {
  refreshHealth();
});
</script>

<template>
  <header class="app-header">
    <h1 class="app-title">stockMai</h1>
  </header>

  <main class="app-content">
    <MarketView
      v-show="activeTab === 'market'"
      :symbol="symbol"
      :quote="quote"
      :quote-loading="quoteLoading"
      :quote-error="quoteError"
      :quote-checked-at="quoteCheckedAt"
      :history="history"
      :history-error="historyError"
      :indicators="indicators"
      :indicators-error="indicatorsError"
      :selected-days="selectedDays"
      :day-options="dayOptions"
      @update:symbol="updateSymbol"
      @refresh="refreshQuote"
      @change-day="setDayRange"
    />

    <AiView
      v-show="activeTab === 'ai'"
      :symbol="symbol"
      :ai-result="aiResult"
      :ai-loading="aiLoading"
      :ai-error="aiError"
      :ai-checked-at="aiCheckedAt"
      :user-prompt="userPrompt"
      :selected-provider="selectedProvider"
      :provider-options="providerOptions"
      :strategy-result="strategyResult"
      :strategy-loading="strategyLoading"
      :strategy-error="strategyError"
      :strategy-checked-at="strategyCheckedAt"
      @refresh="refreshAiAndStrategy"
      @update:symbol="updateSymbol"
      @update:prompt="updateUserPrompt"
      @change-provider="setProvider"
    />

    <SettingsView
      v-show="activeTab === 'settings'"
      :health="health"
      :health-loading="healthLoading"
      :health-error="healthError"
      :health-checked-at="healthCheckedAt"
      @refresh-health="refreshHealth"
    />
  </main>

  <transition name="loading-fade">
    <div v-if="showLoadingOverlay" class="loading-overlay" role="status" aria-live="polite" aria-busy="true">
      <div class="loading-modal">
        <span class="loading-spinner" aria-hidden="true"></span>
        <p class="loading-text">{{ loadingMessage }}</p>
      </div>
    </div>
  </transition>

  <TabBar :active-tab="activeTab" @change="activeTab = $event" />
</template>
