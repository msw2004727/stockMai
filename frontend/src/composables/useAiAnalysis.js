import { onBeforeUnmount, ref } from "vue";

import { analyzeStock } from "../api";
import { formatTimeLabel } from "../utils/formatters";

export function useAiAnalysis(symbolRef, initialProvider = "gpt5") {
  const aiResult = ref(null);
  const aiLoading = ref(false);
  const aiError = ref("");
  const aiCheckedAt = ref("");

  const userPrompt = ref("");
  const selectedProvider = ref(initialProvider);
  const providerOptions = ["gpt5", "claude", "grok", "deepseek"];

  let controller = null;

  function showAiPrerequisiteError(message) {
    aiResult.value = null;
    aiCheckedAt.value = "";
    aiLoading.value = false;
    aiError.value = message;
  }

  async function refreshAi() {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

    aiResult.value = null;
    aiCheckedAt.value = "";
    aiLoading.value = true;
    aiError.value = "";

    try {
      aiResult.value = await analyzeStock(
        symbolRef.value,
        userPrompt.value,
        [selectedProvider.value],
        controller.signal,
      );
      aiCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (error.name !== "AbortError") {
        aiResult.value = null;
        aiError.value = error.message || "AI 分析失敗";
      }
    } finally {
      aiLoading.value = false;
    }
  }

  function setProvider(provider) {
    selectedProvider.value = provider;
  }

  onBeforeUnmount(() => {
    controller?.abort();
  });

  return {
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
  };
}
