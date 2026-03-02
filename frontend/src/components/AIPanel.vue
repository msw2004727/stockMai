<script setup>
import { ref } from "vue";

import { useStockSymbolSearch } from "../composables/useStockSymbolSearch";
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";

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
  return displayOrFallback(provider, "未知模型");
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function localize(value, fallback = "暫無資料") {
  return displayOrFallback(value, fallback);
}

function localizeError(value) {
  return localizeAiText(value) || "AI 分析失敗";
}

function toNum(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function shortTermEvidence(result) {
  if (!result) {
    return ["尚無可用資料，請先執行 AI 分析。"];
  }

  const evidence = [];
  const latest = result?.indicator_context?.latest || {};

  const sma5 = toNum(latest?.sma5);
  const sma20 = toNum(latest?.sma20);
  if (sma5 !== null && sma20 !== null) {
    const trendText =
      sma5 > sma20 ? "短均線在長均線上方，短線偏多。" : sma5 < sma20 ? "短均線在長均線下方，短線偏空。" : "短長均線接近，中性盤整。";
    evidence.push(`均線依據：SMA5 ${fmt(sma5, 2)}、SMA20 ${fmt(sma20, 2)}，${trendText}`);
  }

  const rsi14 = toNum(latest?.rsi14);
  if (rsi14 !== null) {
    const rsiText = rsi14 >= 70 ? "過熱" : rsi14 <= 30 ? "超賣" : rsi14 >= 55 ? "偏強" : rsi14 <= 45 ? "偏弱" : "中性";
    evidence.push(`動能依據：RSI14 ${fmt(rsi14, 1)}，目前 ${rsiText}。`);
  }

  const macd = toNum(latest?.macd);
  const macdSignal = toNum(latest?.macd_signal);
  if (macd !== null && macdSignal !== null) {
    const macdText = macd > macdSignal ? "MACD 高於訊號線，動能偏多。" : macd < macdSignal ? "MACD 低於訊號線，動能偏空。" : "MACD 接近訊號線，動能中性。";
    evidence.push(`趨勢依據：MACD ${fmt(macd, 2)}、Signal ${fmt(macdSignal, 2)}，${macdText}`);
  }

  const sentimentLabel = toSignalLabel(result?.sentiment_context?.market_sentiment);
  const sentimentSummary = localize(result?.sentiment_context?.summary, "");
  if (sentimentSummary) {
    evidence.push(`情緒依據：市場情緒 ${sentimentLabel}。${sentimentSummary}`);
  } else {
    evidence.push(`情緒依據：市場情緒 ${sentimentLabel}。`);
  }

  return evidence.slice(0, 6);
}
</script>

<template>
  <h2 class="section-title">AI 分析</h2>
  <p class="hint">先在行情頁查詢股價，再執行 AI 分析會更準確。</p>

  <div class="field-box">
    <p class="field-title">分析標的</p>
    <div class="query-row">
      <input
        :value="symbol"
        class="input"
        type="text"
        maxlength="20"
        inputmode="text"
        placeholder="輸入台股代號或中文名稱"
        :disabled="aiLoading"
        @input="onSymbolInput"
        @keydown.enter.prevent="onRefreshClick"
      />
      <button type="button" class="btn" :disabled="aiLoading" @click="onRefreshClick">
        {{ aiLoading ? "分析中..." : "執行 AI 分析" }}
      </button>
      <span v-if="aiCheckedAt" class="checked-at no-wrap">更新時間：{{ aiCheckedAt }}</span>
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
    <p class="field-title">你想要 AI 著重的分析重點</p>
    <textarea
      :value="userPrompt"
      class="textarea"
      rows="3"
      placeholder="例如：短線壓力支撐、進出場節奏、停損停利建議"
      :disabled="aiLoading"
      @input="onPromptInput"
    ></textarea>
  </div>

  <div v-if="aiError" class="card error">{{ localizeError(aiError) }}</div>

  <div v-else-if="aiResult">
    <article class="card full-span" style="margin-top:16px;">
      <p class="label">AI 共識結果</p>
      <p class="value" :class="signalClass(aiResult.consensus?.signal)" style="margin-top:8px;">
        {{ toSignalLabel(aiResult.consensus?.signal) }}
        <span style="font-size:1rem;font-weight:600;">（信心 {{ fmt(aiResult.consensus?.confidence, 2) }}）</span>
      </p>
      <p class="sub" style="margin-top:8px;">{{ localize(aiResult.consensus?.summary) }}</p>
      <p class="sub" style="margin-top:4px;font-size:0.82rem;">
        主要來源：{{ providerLabel(aiResult.consensus?.source_provider || "") }}
        ・ 回退：{{ aiResult.fallback_used ? "有" : "無" }}
      </p>
    </article>

    <article class="card full-span" style="margin-top:0;">
      <p class="label">AI短線分析（1~5 個交易日）</p>
      <p class="sub" style="margin-top:8px;font-weight:700;">AI依據資料分析：</p>
      <ul class="short-term-evidence">
        <li v-for="(line, idx) in shortTermEvidence(aiResult)" :key="`short-evidence-${idx}`">
          {{ line }}
        </li>
      </ul>
      <p class="sub warn-text" style="margin-top:8px;font-size:0.82rem;">
        提醒：目前此版本參考資料不多，此分析僅供參考，待後續改版。
      </p>
    </article>

    <article class="card full-span" style="margin-top:0;">
      <p class="label">市場情緒</p>
      <p class="sub" style="margin-top:6px;">
        <span :class="signalClass(aiResult.sentiment_context?.market_sentiment)" style="font-weight:700;">
          {{ toSignalLabel(aiResult.sentiment_context?.market_sentiment) }}
        </span>
        ・ 波動：{{ localize(aiResult.sentiment_context?.volatility_level, "--") }}
      </p>
      <p class="sub">{{ localize(aiResult.sentiment_context?.summary, "尚無情緒摘要") }}</p>
    </article>

    <button class="detail-toggle" @click="showDetail = !showDetail">
      {{ showDetail ? "收合AI反饋數據" : "展開AI反饋數據" }}
    </button>

    <template v-if="showDetail">
      <article class="card full-span">
        <p class="label">技術指標快照</p>
        <p class="sub" style="margin-top:6px;">
          來源：{{ localize(aiResult.indicator_context?.history_source, "--") }}
          ・ 日期：{{ localize(aiResult.indicator_context?.as_of_date, "--") }}
        </p>
        <p class="sub">
          SMA5：{{ fmt(aiResult.indicator_context?.latest?.sma5, 2) }}
          ／ SMA20：{{ fmt(aiResult.indicator_context?.latest?.sma20, 2) }}
        </p>
        <p class="sub">
          RSI14：{{ fmt(aiResult.indicator_context?.latest?.rsi14, 1) }}
          ／ MACD：{{ fmt(aiResult.indicator_context?.latest?.macd, 2) }}
        </p>
      </article>

      <article v-for="item in aiResult.results" :key="item.provider" class="card">
        <p class="label">{{ providerLabel(item.provider) }}</p>
        <p class="value" :class="item.ok ? (signalClass(item.data?.signal) || 'ok') : 'warn'" style="margin-top:6px;font-size:1rem;">
          {{ item.ok ? toSignalLabel(item.data?.signal) : "失敗" }}
        </p>
        <p class="sub" v-if="item.ok">{{ localize(item.data?.summary) }}</p>
        <p class="sub" v-else>{{ localizeError(item.error) }}</p>
        <p class="sub" v-if="item.ok" style="font-size:0.82rem;">信心：{{ fmt(item.data?.confidence, 2) }}</p>
      </article>
    </template>
  </div>
</template>
