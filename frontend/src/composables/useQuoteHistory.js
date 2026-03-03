import { onBeforeUnmount, onMounted, ref } from "vue";

import { getStockHistory, getStockIndicators, getStockQuote, getStockSymbolSearch } from "../api";
import { formatTimeLabel } from "../utils/formatters";

const SYMBOL_PATTERN = /^\d{4,6}$/;
const AUTO_REFRESH_INTERVAL_MS = 5000;

export function useQuoteHistory(initialSymbol = "") {
  const symbol = ref(initialSymbol);
  const quote = ref(null);
  const quoteLoading = ref(false);
  const quoteError = ref("");
  const quoteCheckedAt = ref("");

  const history = ref(null);
  const historyError = ref("");

  const indicators = ref(null);
  const indicatorsError = ref("");

  const selectedDays = ref(5);
  const dayOptions = [5, 20, 90, 180];

  let controller = null;
  let autoRefreshTimer = null;
  let silentRefreshing = false;

  function isAutoRefreshEligible() {
    if (!quote.value) return false;
    if (String(quote.value.market_state || "").toLowerCase() !== "trading") return false;
    if (quoteLoading.value) return false;
    if (typeof document !== "undefined" && document.visibilityState !== "visible") return false;
    return true;
  }

  async function refreshQuote(options = {}) {
    const silent = Boolean(options.silent);
    if (silent && silentRefreshing) {
      return;
    }

    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

    const parsedSymbol = String(symbol.value || "").trim();

    if (!silent) {
      quoteError.value = "";
      historyError.value = "";
      indicatorsError.value = "";
    }

    if (!parsedSymbol) {
      if (!silent) {
        quote.value = null;
        history.value = null;
        indicators.value = null;
        quoteCheckedAt.value = "";
        quoteError.value = "請先輸入股票代號";
      }
      return;
    }

    if (!silent) {
      // 新查詢先清掉舊資料，避免畫面保留上一檔股票資訊。
      quote.value = null;
      history.value = null;
      indicators.value = null;
      quoteCheckedAt.value = "";
      quoteLoading.value = true;
    } else {
      silentRefreshing = true;
    }

    try {
      let resolvedSymbol = parsedSymbol;
      if (!SYMBOL_PATTERN.test(resolvedSymbol)) {
        const searchPayload = await getStockSymbolSearch(resolvedSymbol, 1, controller.signal);
        const bestMatch = Array.isArray(searchPayload?.results) ? searchPayload.results[0] : null;
        if (!bestMatch?.symbol || !SYMBOL_PATTERN.test(String(bestMatch.symbol))) {
          throw new Error("查無相關股票，請輸入更完整的中文名稱或代號");
        }
        resolvedSymbol = String(bestMatch.symbol);
        symbol.value = resolvedSymbol;
      }

      const quoteResult = await getStockQuote(resolvedSymbol, controller.signal);
      quote.value = quoteResult;
      quoteError.value = "";

      try {
        const historyResult = await getStockHistory(resolvedSymbol, selectedDays.value, controller.signal);
        history.value = historyResult;
        historyError.value = "";
      } catch (error) {
        if (!silent && error.name !== "AbortError") {
          history.value = null;
          historyError.value = error.message || "股價歷史查詢失敗";
        }
      }

      try {
        const indicatorsResult = await getStockIndicators(resolvedSymbol, 60, controller.signal);
        indicators.value = indicatorsResult;
        indicatorsError.value = "";
      } catch (error) {
        if (!silent && error.name !== "AbortError") {
          indicators.value = null;
          indicatorsError.value = error.message || "技術指標查詢失敗";
        }
      }

      quoteCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (!silent && error.name !== "AbortError") {
        quoteError.value = error.message || "股票報價查詢失敗";
        quote.value = null;
        history.value = null;
        indicators.value = null;
      }
    } finally {
      if (silent) {
        silentRefreshing = false;
      } else {
        quoteLoading.value = false;
      }
    }
  }

  function triggerAutoRefresh() {
    if (!isAutoRefreshEligible()) {
      return;
    }
    refreshQuote({ silent: true });
  }

  function onVisibilityChange() {
    if (typeof document === "undefined") return;
    if (document.visibilityState === "visible") {
      triggerAutoRefresh();
    }
  }

  function setDayRange(days) {
    if (selectedDays.value === days) {
      return;
    }
    selectedDays.value = days;
    if (quote.value) {
      refreshQuote();
    }
  }

  onMounted(() => {
    if (typeof window !== "undefined") {
      autoRefreshTimer = window.setInterval(triggerAutoRefresh, AUTO_REFRESH_INTERVAL_MS);
    }
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisibilityChange);
    }
  });

  onBeforeUnmount(() => {
    controller?.abort();
    if (typeof window !== "undefined" && autoRefreshTimer !== null) {
      window.clearInterval(autoRefreshTimer);
      autoRefreshTimer = null;
    }
    if (typeof document !== "undefined") {
      document.removeEventListener("visibilitychange", onVisibilityChange);
    }
  });

  return {
    symbol,
    quote,
    quoteLoading,
    quoteError,
    quoteCheckedAt,
    history,
    historyError,
    indicators,
    indicatorsError,
    selectedDays,
    dayOptions,
    refreshQuote,
    setDayRange,
  };
}
