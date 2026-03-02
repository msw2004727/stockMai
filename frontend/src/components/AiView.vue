<script setup>
import AIPanel from "./AIPanel.vue";

defineProps({
  symbol: { type: String, default: "" },
  aiResult: { type: Object, default: null },
  aiLoading: { type: Boolean, default: false },
  aiError: { type: String, default: "" },
  aiCheckedAt: { type: String, default: "" },
  userPrompt: { type: String, default: "" },
  selectedProvider: { type: String, default: "claude" },
  providerOptions: { type: Array, default: () => ["claude", "gpt5", "grok", "gemini"] },
});

const emit = defineEmits(["refresh", "update:prompt", "change-provider"]);
</script>

<template>
  <div class="view-container">
    <div class="panel">
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
