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
import { useTheme } from "./composables/useTheme";

const { theme, toggleTheme } = useTheme();
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

const hasCurrentQuote = computed(() => {
  const currentSymbol = String(symbol.value || "").trim();
  const quoteSymbol = String(quote.value?.symbol || "").trim();
  return Boolean(currentSymbol && quoteSymbol && currentSymbol === quoteSymbol);
});

const loadingMessage = computed(() => {
  if (aiLoading.value || strategyLoading.value) {
    return "AI 分析中，請稍候...";
  }
  if (quoteLoading.value) {
    return "行情查詢中，請稍候...";
  }
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
  if (!hasCurrentQuote.value) {
    const message = "請先到行情頁面查詢股價";
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
    <button
      type="button"
      class="theme-toggle"
      @click="toggleTheme"
      :title="theme === 'light' ? '切換深色模式' : '切換淺色模式'"
    >
      <svg
        v-if="theme === 'dark'"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
      <svg
        v-else
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    </button>
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
