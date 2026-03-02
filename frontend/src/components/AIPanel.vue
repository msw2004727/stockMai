<script setup>
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";

defineProps({
  symbol: {
    type: String,
    default: "",
  },
  aiResult: {
    type: Object,
    default: null,
  },
  aiLoading: {
    type: Boolean,
    default: false,
  },
  aiError: {
    type: String,
    default: "",
  },
  aiCheckedAt: {
    type: String,
    default: "",
  },
  userPrompt: {
    type: String,
    default: "",
  },
  selectedProvider: {
    type: String,
    default: "gpt5",
  },
  providerOptions: {
    type: Array,
    default: () => ["gpt5", "claude", "grok", "deepseek"],
  },
});

const emit = defineEmits(["refresh", "update:prompt", "change-provider"]);

function onPromptInput(event) {
  emit("update:prompt", event.target.value);
}

function toSignalLabel(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") {
    return "偏多";
  }
  if (parsed === "bearish") {
    return "偏空";
  }
  return "中性";
}

function providerLabel(provider) {
  const parsed = String(provider || "").toLowerCase();
  if (parsed === "gpt5") {
    return "GPT-5";
  }
  if (parsed === "claude") {
    return "Claude";
  }
  if (parsed === "grok") {
    return "Grok";
  }
  if (parsed === "deepseek") {
    return "DeepSeek";
  }
  return displayOrFallback(provider, "未知");
}

function fmt(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "暫無資料";
  }
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
  <p class="hint">先在行情頁查詢股價，再執行 AI 分析會更準確。</p>

  <div class="field-box">
    <p class="field-title">分析標的</p>
    <div class="query-row">
      <input :value="symbol" class="input" type="text" disabled />
      <button type="button" class="btn" :disabled="aiLoading" @click="emit('refresh')">
        {{ aiLoading ? "分析中..." : "執行 AI 分析" }}
      </button>
      <span v-if="aiCheckedAt" class="checked-at no-wrap">更新時間：{{ aiCheckedAt }}</span>
    </div>
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
    <p class="field-title">你想要 AI 著重的分析重點（可留空）</p>
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

  <div v-else-if="aiResult" class="grid quote-grid">
    <article class="card full-span">
      <p class="label">AI 共識結論</p>
      <p class="value">{{ toSignalLabel(aiResult.consensus.signal) }}（信心 {{ fmt(aiResult.consensus.confidence, 2) }}）</p>
      <p class="sub">{{ localize(aiResult.consensus.summary) }}</p>
      <p class="sub">主導模型：{{ providerLabel(aiResult.consensus.source_provider || "未知") }}</p>
      <p class="sub">是否啟用備援：{{ aiResult.fallback_used ? "是" : "否" }}</p>
    </article>

    <article class="card">
      <p class="label">市場情緒</p>
      <p class="sub">方向：{{ toSignalLabel(aiResult.sentiment_context?.market_sentiment) }}</p>
      <p class="sub">情緒分數：{{ fmt(aiResult.sentiment_context?.sentiment_score, 4) }}</p>
      <p class="sub">波動等級：{{ localize(aiResult.sentiment_context?.volatility_level, "未知") }}</p>
      <p class="sub">{{ localize(aiResult.sentiment_context?.summary, "尚無情緒摘要") }}</p>
    </article>

    <article class="card">
      <p class="label">技術指標快照</p>
      <p class="sub">資料來源：{{ localize(aiResult.indicator_context?.history_source, "無") }}</p>
      <p class="sub">資料日期：{{ localize(aiResult.indicator_context?.as_of_date, "暫無資料") }}</p>
      <p class="sub">SMA5（5日均線）：{{ fmt(aiResult.indicator_context?.latest?.sma5, 4) }}</p>
      <p class="sub">SMA20（20日均線）：{{ fmt(aiResult.indicator_context?.latest?.sma20, 4) }}</p>
      <p class="sub">RSI14（相對強弱）：{{ fmt(aiResult.indicator_context?.latest?.rsi14, 4) }}</p>
      <p class="sub">MACD（趨勢動能）：{{ fmt(aiResult.indicator_context?.latest?.macd, 4) }}</p>
    </article>

    <article class="card">
      <p class="label">成本摘要</p>
      <p class="sub">本次成本（美元）：{{ fmt(aiResult.cost?.total_request_cost_usd, 8) }}</p>
      <p class="sub">今日累計（美元）：{{ fmt(aiResult.cost?.daily_total_usd, 8) }}</p>
      <p class="sub">今日預算上限（美元）：{{ fmt(aiResult.cost?.daily_budget_usd, 2) }}</p>
      <p class="sub">是否超出預算：{{ aiResult.cost?.budget_exceeded ? "是" : "否" }}</p>
    </article>

    <article v-for="item in aiResult.results" :key="item.provider" class="card">
      <p class="label">{{ providerLabel(item.provider) }}</p>
      <p class="value" :class="item.ok ? 'ok' : 'warn'">{{ item.ok ? "成功" : "失敗" }}</p>
      <p class="sub" v-if="item.ok">{{ localize(item.data.summary) }}</p>
      <p class="sub" v-else>{{ localizeError(item.error) }}</p>
      <p class="sub" v-if="item.ok">方向：{{ toSignalLabel(item.data.signal) }}（信心 {{ fmt(item.data.confidence, 2) }}）</p>
      <p class="sub" v-if="item.ok && item.cost">成本（美元）：{{ fmt(item.cost.request_cost_usd, 8) }}</p>
    </article>
  </div>
</template>
