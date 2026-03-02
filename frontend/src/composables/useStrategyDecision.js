import { onBeforeUnmount, ref } from "vue";

import { getStrategyDecision } from "../api";
import { formatTimeLabel } from "../utils/formatters";

export function useStrategyDecision(symbolRef, promptRef, selectedProviderRef) {
  const strategyResult = ref(null);
  const strategyLoading = ref(false);
  const strategyError = ref("");
  const strategyCheckedAt = ref("");

  let controller = null;

  function showStrategyPrerequisiteError(message) {
    strategyResult.value = null;
    strategyCheckedAt.value = "";
    strategyLoading.value = false;
    strategyError.value = message;
  }

  async function refreshStrategy() {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

    strategyResult.value = null;
    strategyCheckedAt.value = "";
    strategyLoading.value = true;
    strategyError.value = "";

    try {
      strategyResult.value = await getStrategyDecision(
        symbolRef.value,
        promptRef.value,
        [selectedProviderRef.value],
        controller.signal,
      );
      strategyCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (error.name !== "AbortError") {
        strategyResult.value = null;
        strategyError.value = error.message || "策略決策失敗";
      }
    } finally {
      strategyLoading.value = false;
    }
  }

  onBeforeUnmount(() => {
    controller?.abort();
  });

  return {
    strategyResult,
    strategyLoading,
    strategyError,
    strategyCheckedAt,
    refreshStrategy,
    showStrategyPrerequisiteError,
  };
}
