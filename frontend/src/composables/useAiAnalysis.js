import { onBeforeUnmount, ref } from "vue";

import { analyzeStock } from "../api";
import { formatTimeLabel } from "../utils/formatters";

export function useAiAnalysis(symbolRef, initialProvider = "claude") {
  const aiResult = ref(null);
  const aiLoading = ref(false);
  const aiError = ref("");
  const aiCheckedAt = ref("");

  const userPrompt = ref("請聚焦短線趨勢、風險與可執行建議。");
  const selectedProvider = ref(initialProvider);
  const providerOptions = ["claude", "gpt5", "grok", "gemini"];

  let controller = null;

  async function refreshAi() {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

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
  };
}
