import { onBeforeUnmount, ref } from "vue";

import { getStockSymbolSearch } from "../api";

const SYMBOL_PATTERN = /^\d{4,6}$/;

export function useStockSymbolSearch() {
  const searchResults = ref([]);
  const searchLoading = ref(false);
  const searchError = ref("");

  let controller = null;
  let debounceTimer = null;
  let requestCounter = 0;

  function clearSearch() {
    searchResults.value = [];
    searchLoading.value = false;
    searchError.value = "";
    if (controller) {
      controller.abort();
      controller = null;
    }
    if (debounceTimer) {
      clearTimeout(debounceTimer);
      debounceTimer = null;
    }
  }

  function scheduleSearch(rawInput) {
    const query = String(rawInput || "").trim();
    searchError.value = "";

    if (!query || SYMBOL_PATTERN.test(query)) {
      searchResults.value = [];
      searchLoading.value = false;
      return;
    }

    if (debounceTimer) {
      clearTimeout(debounceTimer);
    }
    debounceTimer = setTimeout(() => {
      runSearch(query);
    }, 220);
  }

  async function runSearch(query) {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();
    const requestId = ++requestCounter;

    searchLoading.value = true;
    searchError.value = "";
    try {
      const payload = await getStockSymbolSearch(query, 8, controller.signal);
      if (requestId !== requestCounter) {
        return;
      }
      searchResults.value = Array.isArray(payload?.results) ? payload.results : [];
      if (searchResults.value.length === 0) {
        searchError.value = "查無相關代號，請輸入更完整名稱";
      }
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      searchResults.value = [];
      searchError.value = error.message || "代號搜尋失敗";
    } finally {
      if (requestId === requestCounter) {
        searchLoading.value = false;
      }
    }
  }

  onBeforeUnmount(() => {
    clearSearch();
  });

  return {
    searchResults,
    searchLoading,
    searchError,
    clearSearch,
    scheduleSearch,
  };
}

