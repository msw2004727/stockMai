<script setup>
import { computed, onMounted, ref, shallowRef } from "vue";

import AiView from "./components/AiView.vue";
import MarketView from "./components/MarketView.vue";
import SettingsView from "./components/SettingsView.vue";
import TabBar from "./components/TabBar.vue";
import { useAiAnalysis } from "./composables/useAiAnalysis";
import { useHealthStatus } from "./composables/useHealthStatus";
import { useQuoteHistory } from "./composables/useQuoteHistory";
import { useStrategyDecision } from "./composables/useStrategyDecision";

const activeTab = shallowRef("market");
const showAiStalePrompt = ref(false);
const lastAiAnalyzedSnapshot = shallowRef(null);

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
  marketMovers,
  marketMoversLoading,
  marketMoversError,
  intelOverview,
  intelOverviewLoading,
  intelOverviewError,
  intelDeep,
  intelDeepLoading,
  intelDeepError,
  intelStatus,
  intelStatusError,
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

const currentQuoteSymbol = computed(() => String(quote.value?.symbol || "").trim());
const currentQuoteName = computed(() => String(quote.value?.name || currentQuoteSymbol.value || "").trim());

const isAiDataStale = computed(() => {
  const latestAiSymbol = String(lastAiAnalyzedSnapshot.value?.symbol || "").trim();
  if (!latestAiSymbol) {
    return false;
  }
  const latestMarketSymbol = currentQuoteSymbol.value;
  if (!latestMarketSymbol) {
    return false;
  }
  return latestAiSymbol !== latestMarketSymbol;
});

const staleAiStockName = computed(() => {
  const rawName = String(lastAiAnalyzedSnapshot.value?.name || "").trim();
  if (rawName) {
    return rawName;
  }
  return String(lastAiAnalyzedSnapshot.value?.symbol || "--").trim() || "--";
});

const loadingMessage = computed(() => {
  if (aiLoading.value || strategyLoading.value) {
    return "提醒：沒有人能準確預測股價走勢，即使是最頂級的分析師也不行，建議任何投資決策前，多參考專業券商的研究報告、諮詢合格的財務顧問，並且量力而為！";
  }
  return "";
});

const showLoadingOverlay = computed(() => Boolean(aiLoading.value || strategyLoading.value || quoteLoading.value));
const loadingMarqueeText = computed(() => {
  if (aiLoading.value || strategyLoading.value) {
    return "AI努力分析中";
  }
  if (quoteLoading.value) {
    return "您所查詢的股價行情正在資料庫查詢中，請稍後~";
  }
  return "";
});
const showLoadingMarquee = computed(() => Boolean(loadingMarqueeText.value));

function updateSymbol(value) {
  symbol.value = value;
}

function updateUserPrompt(value) {
  userPrompt.value = value;
}

function closeAiStalePrompt() {
  showAiStalePrompt.value = false;
}

function handleTabChange(nextTab) {
  activeTab.value = nextTab;

  if (nextTab === "ai" && isAiDataStale.value) {
    showAiStalePrompt.value = true;
    return;
  }

  showAiStalePrompt.value = false;
}

async function refreshAiAndStrategy(payload = null) {
  const nextSymbol = String(payload?.symbol || "").trim();
  const nextName = String(payload?.name || "").trim();
  if (nextSymbol) {
    symbol.value = nextSymbol;
  }

  const sym = String(symbol.value || "").trim();
  if (!sym) {
    showAiPrerequisiteError("");
    showStrategyPrerequisiteError("");
    return;
  }

  await Promise.all([refreshAi(), refreshStrategy()]);

  if (aiResult.value) {
    const analyzedSymbol = currentQuoteSymbol.value || sym;
    lastAiAnalyzedSnapshot.value = {
      symbol: analyzedSymbol,
      name: nextName || currentQuoteName.value || analyzedSymbol,
      checkedAt: String(aiCheckedAt.value || ""),
    };
    showAiStalePrompt.value = false;
  }
}

onMounted(() => {
  refreshHealth();
});
</script>

<template>
  <header class="app-header">
    <h1 class="app-title">
      <span>StockMai</span>
      <small class="app-title-beta">(測試版)</small>
    </h1>
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
        <div v-if="showLoadingMarquee" class="loading-marquee" aria-hidden="true">
          <div class="loading-marquee-track">
            <div class="loading-marquee-group">
              <span>{{ loadingMarqueeText }}</span>
              <span>{{ loadingMarqueeText }}</span>
              <span>{{ loadingMarqueeText }}</span>
            </div>
            <div class="loading-marquee-group" aria-hidden="true">
              <span>{{ loadingMarqueeText }}</span>
              <span>{{ loadingMarqueeText }}</span>
              <span>{{ loadingMarqueeText }}</span>
            </div>
          </div>
        </div>
        <p v-if="loadingMessage" class="loading-text">{{ loadingMessage }}</p>
      </div>
    </div>
  </transition>

  <transition name="loading-fade">
    <div
      v-if="showAiStalePrompt"
      class="stale-notice-overlay"
      role="alertdialog"
      aria-modal="true"
      aria-labelledby="stale-ai-title"
    >
      <div class="stale-notice-modal">
        <h2 id="stale-ai-title" class="stale-notice-title">提醒</h2>
        <p class="stale-notice-text">
          目前資料是上次最後 AI 分析的「{{ staleAiStockName }}」資料。<br />
          請按「執行 AI 分析」更新為最新查詢股票。
        </p>
        <div class="stale-notice-actions">
          <button type="button" class="btn" @click="closeAiStalePrompt">我知道了</button>
        </div>
      </div>
    </div>
  </transition>

  <TabBar :active-tab="activeTab" @change="handleTabChange" />
</template>
