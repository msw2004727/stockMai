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
</script>

<template>
  <h2 class="section-title">AI Analysis</h2>
  <p class="hint">Send current symbol to AI Gateway and review consensus output.</p>

  <div class="query-row">
    <input :value="symbol" class="input" type="text" disabled />
    <button type="button" class="btn" :disabled="aiLoading" @click="emit('refresh')">
      {{ aiLoading ? "Analyzing..." : "Run AI Analyze" }}
    </button>
    <span v-if="aiCheckedAt" class="checked-at">Last check: {{ aiCheckedAt }}</span>
  </div>

  <div class="period-row">
    <span class="period-label">Provider:</span>
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
    placeholder="Type your analysis focus..."
    :disabled="aiLoading"
    @input="onPromptInput"
  ></textarea>

  <div v-if="aiError" class="card error">{{ aiError }}</div>

  <div v-else-if="aiResult" class="grid quote-grid">
    <article class="card full-span">
      <p class="label">Consensus</p>
      <p class="value">{{ aiResult.consensus.signal }} ({{ aiResult.consensus.confidence }})</p>
      <p class="sub">{{ aiResult.consensus.summary }}</p>
      <p class="sub">source: {{ aiResult.consensus.source_provider || "n/a" }}</p>
      <p class="sub">fallback used: {{ aiResult.fallback_used ? "yes" : "no" }}</p>
    </article>

    <article v-for="item in aiResult.results" :key="item.provider" class="card">
      <p class="label">{{ item.provider }}</p>
      <p class="value" :class="item.ok ? 'ok' : 'warn'">{{ item.ok ? "ok" : "error" }}</p>
      <p class="sub" v-if="item.ok">{{ item.data.summary }}</p>
      <p class="sub" v-else>{{ item.error }}</p>
      <p class="sub" v-if="item.ok">signal: {{ item.data.signal }}, confidence: {{ item.data.confidence }}</p>
    </article>
  </div>
</template>
