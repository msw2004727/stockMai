<script setup>
import { ref } from "vue";
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";
import { useStockSymbolSearch } from "../composables/useStockSymbolSearch";

defineProps({
  symbol: { type: String, default: "" },
  aiResult: { type: Object, default: null },
  aiLoading: { type: Boolean, default: false },
  aiError: { type: String, default: "" },
  aiCheckedAt: { type: String, default: "" },
  userPrompt: { type: String, default: "" },
  selectedProvider: { type: String, default: "gpt5" },
  providerOptions: { type: Array, default: () => ["gpt5", "claude", "grok", "deepseek"] },
});

const emit = defineEmits(["refresh", "update:symbol", "update:prompt", "change-provider"]);

const showDetail = ref(false);

const { searchResults, searchLoading, searchError, clearSearch, scheduleSearch } = useStockSymbolSearch();

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

function onPromptInput(event) {
  emit("update:prompt", event.target.value);
}

function toSignalLabel(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") return "偏多";
  if (parsed === "bearish") return "偏空";
  return "中性";
}

function signalClass(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") return "rise";
  if (parsed === "bearish") return "fall";
  return "";
}

function providerLabel(provider) {
  const parsed = String(provider || "").toLowerCase();
  if (parsed === "gpt5") return "GPT-5";
  if (parsed === "claude") return "Claude";
  if (parsed === "grok") return "Grok";
  if (parsed === "deepseek") return "DeepSeek";
  return displayOrFallback(provider, "未知");
}

function fmt(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "－";
  return Number(value).toFixed(digits);
}

function localize(value, fallback = "暫無資料") {
  return displayOrFallback(value, fallback);
}

function localizeError(value) {
  return localizeAiText(value) || "分析失敗";
}
</script>

<template>
  <h2 class="section-title">AI 分析</h2>
  <p class="hint">輸入代號後執行分析，系統將自動帶入最新行情與技術指標。</p>

  <!-- 可編輯的代號輸入框 -->
  <div class="field-box">
    <p class="field-title">分析標的</p>
    <div class="query-row">
      <input
        :value="symbol"
        class="input"
        type="text"
        maxlength="20"
        inputmode="text"
        placeholder="輸入台股代號，例如 2330"
        :disabled="aiLoading"
        @input="onSymbolInput"
        @keydown.enter.prevent="onRefreshClick"
      />
      <button type="button" class="btn" :disabled="aiLoading" @click="onRefreshClick">
        {{ aiLoading ? "分析中..." : "執行分析" }}
      </button>
      <span v-if="aiCheckedAt" class="checked-at no-wrap">更新：{{ aiCheckedAt }}</span>
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

  <div class="field-box">
    <p class="field-title">AI 核心</p>
    <div class="period-row provider-grid">
      <button
        v-for="provider in providerOptions"
        :key="provider"
        type="button"
        class="period-btn"
        :class="{ active: selectedProvider === provider }"
        :disabled="aiLoading"
        @click="emit('change-provider', provider)"
      >
        {{ providerLabel(provider) }}
      </button>
    </div>
  </div>

  <div class="field-box">
    <p class="field-title">分析重點（可留空）</p>
    <textarea
      :value="userPrompt"
      class="textarea"
      rows="3"
      placeholder="例如：短線支撐壓力、風險控制、進出節奏"
      :disabled="aiLoading"
      @input="onPromptInput"
    ></textarea>
  </div>

  <div v-if="aiError" class="card error">{{ localizeError(aiError) }}</div>

  <div v-else-if="aiResult">

    <!-- 主要：AI 共識結論 -->
    <article class="card full-span" style="margin-top:16px;">
      <p class="label">AI 共識結論</p>
      <p class="value" :class="signalClass(aiResult.consensus.signal)" style="margin-top:8px;">
        {{ toSignalLabel(aiResult.consensus.signal) }}
        <span style="font-size:1rem;font-weight:600;">（信心 {{ fmt(aiResult.consensus.confidence, 2) }}）</span>
      </p>
      <p class="sub" style="margin-top:8px;">{{ localize(aiResult.consensus.summary) }}</p>
      <p class="sub" style="margin-top:4px;font-size:0.82rem;">主導：{{ providerLabel(aiResult.consensus.source_provider || "未知") }}
        · 備援：{{ aiResult.fallback_used ? "是" : "否" }}</p>
    </article>

    <!-- 主要：市場情緒 -->
    <article class="card full-span" style="margin-top:0;">
      <p class="label">市場情緒</p>
      <p class="sub" style="margin-top:6px;">
        <span :class="signalClass(aiResult.sentiment_context?.market_sentiment)" style="font-weight:700;">
          {{ toSignalLabel(aiResult.sentiment_context?.market_sentiment) }}
        </span>
        · 波動：{{ localize(aiResult.sentiment_context?.volatility_level, "－") }}
      </p>
      <p class="sub">{{ localize(aiResult.sentiment_context?.summary, "尚無情緒摘要") }}</p>
    </article>

    <!-- 展開/摺疊按鈕 -->
    <button class="detail-toggle" @click="showDetail = !showDetail">
      {{ showDetail ? "▲ 收起詳細資訊" : "▼ 展開各模型詳情與指標" }}
    </button>

    <template v-if="showDetail">
      <!-- 技術指標快照 -->
      <article class="card full-span">
        <p class="label">技術指標快照</p>
        <p class="sub" style="margin-top:6px;">
          來源：{{ localize(aiResult.indicator_context?.history_source, "－") }}
          · {{ localize(aiResult.indicator_context?.as_of_date, "－") }}
        </p>
        <p class="sub">SMA5：{{ fmt(aiResult.indicator_context?.latest?.sma5, 2) }}
          ／ SMA20：{{ fmt(aiResult.indicator_context?.latest?.sma20, 2) }}</p>
        <p class="sub">RSI14：{{ fmt(aiResult.indicator_context?.latest?.rsi14, 1) }}
          ／ MACD：{{ fmt(aiResult.indicator_context?.latest?.macd, 2) }}</p>
      </article>

      <!-- 各 provider 結果 -->
      <article v-for="item in aiResult.results" :key="item.provider" class="card">
        <p class="label">{{ providerLabel(item.provider) }}</p>
        <p class="value" :class="item.ok ? (signalClass(item.data?.signal) || 'ok') : 'warn'" style="margin-top:6px;font-size:1rem;">
          {{ item.ok ? toSignalLabel(item.data?.signal) : "失敗" }}
        </p>
        <p class="sub" v-if="item.ok">{{ localize(item.data.summary) }}</p>
        <p class="sub" v-else>{{ localizeError(item.error) }}</p>
        <p class="sub" v-if="item.ok" style="font-size:0.82rem;">信心：{{ fmt(item.data.confidence, 2) }}</p>
      </article>
    </template>

  </div>
</template>
