import { onBeforeUnmount, onMounted, ref } from "vue";

import {
  getStockHistory,
  getStockIndicators,
  getStockIntelDeep,
  getStockIntelOverview,
  getStockIntelStatus,
  getStockMarketMovers,
  getStockQuote,
  getStockSymbolSearch,
} from "../api";
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

  const marketMovers = ref(null);
  const marketMoversLoading = ref(false);
  const marketMoversError = ref("");

  const intelOverview = ref(null);
  const intelOverviewLoading = ref(false);
  const intelOverviewError = ref("");

  const intelDeep = ref(null);
  const intelDeepLoading = ref(false);
  const intelDeepError = ref("");

  const intelStatus = ref(null);
  const intelStatusError = ref("");

  const selectedDays = ref(5);
  const dayOptions = [5, 20, 90, 180];

  let controller = null;
  let moversController = null;
  let autoRefreshTimer = null;
  let silentRefreshing = false;

  function isAutoRefreshEligible() {
    if (!quote.value) return false;
    if (String(quote.value.market_state || "").toLowerCase() !== "trading") return false;
    if (quoteLoading.value) return false;
    if (typeof document !== "undefined" && document.visibilityState !== "visible") return false;
    return true;
  }

  function clearIntelState() {
    intelOverview.value = null;
    intelDeep.value = null;
    intelStatus.value = null;
    intelOverviewError.value = "";
    intelDeepError.value = "";
    intelStatusError.value = "";
  }

  async function refreshMarketMovers() {
    if (moversController) {
      moversController.abort();
    }
    moversController = new AbortController();

    marketMoversLoading.value = true;
    marketMoversError.value = "";

    try {
      const payload = await getStockMarketMovers(6, moversController.signal);
      marketMovers.value = payload;
    } catch (error) {
      if (error.name === "AbortError") {
        return;
      }
      marketMovers.value = null;
      marketMoversError.value = error.message || "市場排行資料載入失敗";
    } finally {
      marketMoversLoading.value = false;
    }
  }

  async function refreshIntel(symbolValue, signal, { silent }) {
    intelOverviewLoading.value = true;
    intelDeepLoading.value = true;
    intelOverviewError.value = "";
    intelDeepError.value = "";
    intelStatusError.value = "";

    const tasks = await Promise.allSettled([
      getStockIntelOverview(symbolValue, signal),
      getStockIntelDeep(symbolValue, signal),
      getStockIntelStatus(symbolValue, signal),
    ]);

    if (tasks[0].status === "fulfilled") {
      intelOverview.value = tasks[0].value;
    } else {
      intelOverview.value = null;
      if (!silent && tasks[0].reason?.name !== "AbortError") {
        intelOverviewError.value = tasks[0].reason?.message || "行情擴充資料載入失敗";
      }
    }

    if (tasks[1].status === "fulfilled") {
      intelDeep.value = tasks[1].value;
    } else {
      intelDeep.value = null;
      if (!silent && tasks[1].reason?.name !== "AbortError") {
        intelDeepError.value = tasks[1].reason?.message || "深度資料載入失敗";
      }
    }

    if (tasks[2].status === "fulfilled") {
      intelStatus.value = tasks[2].value;
    } else {
      intelStatus.value = null;
      if (!silent && tasks[2].reason?.name !== "AbortError") {
        intelStatusError.value = tasks[2].reason?.message || "資料可用性檢查失敗";
      }
    }
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
        clearIntelState();
        quoteCheckedAt.value = "";
        quoteError.value = "請先輸入股票代號或名稱。";
      }
      return;
    }

    if (!silent) {
      quote.value = null;
      history.value = null;
      indicators.value = null;
      clearIntelState();
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
          throw new Error("找不到對應的股票代號，請輸入更完整名稱或直接輸入代號。");
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
          historyError.value = error.message || "歷史資料載入失敗";
        }
      }

      try {
        const indicatorsResult = await getStockIndicators(resolvedSymbol, 60, controller.signal);
        indicators.value = indicatorsResult;
        indicatorsError.value = "";
      } catch (error) {
        if (!silent && error.name !== "AbortError") {
          indicators.value = null;
          indicatorsError.value = error.message || "技術指標載入失敗";
        }
      }

      const shouldFetchIntel =
        !silent ||
        !intelOverview.value ||
        String(intelOverview.value?.symbol || "").trim() !== resolvedSymbol;

      if (shouldFetchIntel) {
        await refreshIntel(resolvedSymbol, controller.signal, { silent });
      }
      quoteCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (!silent && error.name !== "AbortError") {
        quoteError.value = error.message || "股價查詢失敗";
        quote.value = null;
        history.value = null;
        indicators.value = null;
        clearIntelState();
      }
    } finally {
      intelOverviewLoading.value = false;
      intelDeepLoading.value = false;
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
    refreshMarketMovers();
    if (typeof window !== "undefined") {
      autoRefreshTimer = window.setInterval(triggerAutoRefresh, AUTO_REFRESH_INTERVAL_MS);
    }
    if (typeof document !== "undefined") {
      document.addEventListener("visibilitychange", onVisibilityChange);
    }
  });

  onBeforeUnmount(() => {
    controller?.abort();
    moversController?.abort();
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
    marketMovers,
    marketMoversLoading,
    marketMoversError,
    intelOverview,
    intelOverviewLoading,
    intelOverviewError,
    intelDeep,
    intelDeepLoading,
    intelDeepError,
    intelStatus,
    intelStatusError,
    selectedDays,
    dayOptions,
    refreshQuote,
    refreshMarketMovers,
    setDayRange,
  };
}
