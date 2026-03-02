<script setup>
import AIPanel from "./AIPanel.vue";
import StrategyPanel from "./StrategyPanel.vue";

defineProps({
  symbol: { type: String, default: "" },
  aiResult: { type: Object, default: null },
  aiLoading: { type: Boolean, default: false },
  aiError: { type: String, default: "" },
  aiCheckedAt: { type: String, default: "" },
  userPrompt: { type: String, default: "" },
  selectedProvider: { type: String, default: "claude" },
  providerOptions: { type: Array, default: () => ["claude", "gpt5", "grok", "gemini"] },
  strategyResult: { type: Object, default: null },
  strategyLoading: { type: Boolean, default: false },
  strategyError: { type: String, default: "" },
  strategyCheckedAt: { type: String, default: "" },
});

const emit = defineEmits(["refresh", "update:prompt", "change-provider"]);
</script>

<template>
  <div class="view-container">
    <div class="panel">
      <div class="grid quote-grid">
        <StrategyPanel
          :symbol="symbol"
          :strategy-result="strategyResult"
          :strategy-loading="strategyLoading"
          :strategy-error="strategyError"
          :strategy-checked-at="strategyCheckedAt"
        />
      </div>

      <div class="divider"></div>

      <AIPanel
        :symbol="symbol"
        :ai-result="aiResult"
        :ai-loading="aiLoading"
        :ai-error="aiError"
        :ai-checked-at="aiCheckedAt"
        :user-prompt="userPrompt"
        :selected-provider="selectedProvider"
        :provider-options="providerOptions"
        @refresh="emit('refresh')"
        @update:prompt="emit('update:prompt', $event)"
        @change-provider="emit('change-provider', $event)"
      />
    </div>
  </div>
</template>
