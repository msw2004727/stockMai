<script setup>
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
    default: "claude",
  },
  providerOptions: {
    type: Array,
    default: () => ["claude", "gpt5", "grok", "gemini"],
  },
});

const emit = defineEmits(["refresh", "update:prompt", "change-provider"]);

function onPromptInput(event) {
  emit("update:prompt", event.target.value);
}

function toSignalLabel(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") {
    return "看多";
  }
  if (parsed === "bearish") {
    return "看空";
  }
  return "中立";
}

function fmt(value, digits = 6) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "N/A";
  }
  return Number(value).toFixed(digits);
}
</script>

<template>
  <h2 class="section-title">AI 分析</h2>
  <p class="hint">送出目前股票代號到 AI Gateway，查看多模型共識結果。</p>

  <div class="query-row">
    <input :value="symbol" class="input" type="text" disabled />
    <button type="button" class="btn" :disabled="aiLoading" @click="emit('refresh')">
      {{ aiLoading ? "分析中..." : "執行 AI 分析" }}
    </button>
    <span v-if="aiCheckedAt" class="checked-at">上次分析：{{ aiCheckedAt }}</span>
  </div>

  <div class="period-row">
    <span class="period-label">模型來源：</span>
    <button
      v-for="provider in providerOptions"
      :key="provider"
      type="button"
      class="period-btn"
      :class="{ active: selectedProvider === provider }"
      :disabled="aiLoading"
      @click="emit('change-provider', provider)"
    >
      {{ provider }}
    </button>
  </div>

  <textarea
    :value="userPrompt"
    class="textarea"
    rows="3"
    placeholder="請輸入這次想聚焦的分析方向..."
    :disabled="aiLoading"
    @input="onPromptInput"
  ></textarea>

  <div v-if="aiError" class="card error">{{ aiError }}</div>

  <div v-else-if="aiResult" class="grid quote-grid">
    <article class="card full-span">
      <p class="label">AI 共識</p>
      <p class="value">{{ toSignalLabel(aiResult.consensus.signal) }}（{{ aiResult.consensus.confidence }}）</p>
      <p class="sub">{{ aiResult.consensus.summary }}</p>
      <p class="sub">來源模型：{{ aiResult.consensus.source_provider || "無" }}</p>
      <p class="sub">是否啟用備援：{{ aiResult.fallback_used ? "是" : "否" }}</p>
    </article>

    <article class="card">
      <p class="label">指標上下文</p>
      <p class="sub">來源：{{ aiResult.indicator_context?.history_source || "none" }}</p>
      <p class="sub">日期：{{ aiResult.indicator_context?.as_of_date || "N/A" }}</p>
      <p class="sub">SMA5：{{ fmt(aiResult.indicator_context?.latest?.sma5, 4) }}</p>
      <p class="sub">SMA20：{{ fmt(aiResult.indicator_context?.latest?.sma20, 4) }}</p>
      <p class="sub">RSI14：{{ fmt(aiResult.indicator_context?.latest?.rsi14, 4) }}</p>
      <p class="sub">MACD：{{ fmt(aiResult.indicator_context?.latest?.macd, 4) }}</p>
    </article>

    <article class="card">
      <p class="label">成本摘要</p>
      <p class="sub">本次成本：${{ fmt(aiResult.cost?.total_request_cost_usd, 8) }}</p>
      <p class="sub">今日累計：${{ fmt(aiResult.cost?.daily_total_usd, 8) }}</p>
      <p class="sub">今日預算：${{ fmt(aiResult.cost?.daily_budget_usd, 2) }}</p>
      <p class="sub">是否超預算：{{ aiResult.cost?.budget_exceeded ? "是" : "否" }}</p>
    </article>

    <article v-for="item in aiResult.results" :key="item.provider" class="card">
      <p class="label">{{ item.provider }}</p>
      <p class="value" :class="item.ok ? 'ok' : 'warn'">{{ item.ok ? "成功" : "失敗" }}</p>
      <p class="sub" v-if="item.ok">{{ item.data.summary }}</p>
      <p class="sub" v-else>{{ item.error }}</p>
      <p class="sub" v-if="item.ok">
        方向：{{ toSignalLabel(item.data.signal) }}，信心：{{ item.data.confidence }}
      </p>
      <p class="sub" v-if="item.ok && item.cost">成本：${{ fmt(item.cost.request_cost_usd, 8) }}</p>
    </article>
  </div>
</template>
