import { onBeforeUnmount, ref } from "vue";

import { getHealth } from "../api";
import { formatTimeLabel } from "../utils/formatters";

export function useHealthStatus() {
  const health = ref(null);
  const healthLoading = ref(false);
  const healthError = ref("");
  const healthCheckedAt = ref("");

  let controller = null;

  async function refreshHealth() {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

    healthLoading.value = true;
    healthError.value = "";

    try {
      const result = await getHealth(controller.signal);
      health.value = result;
      healthCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (error.name !== "AbortError") {
        healthError.value = error.message || "無法連線到後端 API";
      }
    } finally {
      healthLoading.value = false;
    }
  }

  onBeforeUnmount(() => {
    controller?.abort();
  });

  return {
    health,
    healthLoading,
    healthError,
    healthCheckedAt,
    refreshHealth,
  };
}
