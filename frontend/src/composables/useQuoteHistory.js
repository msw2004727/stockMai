import { onBeforeUnmount, ref } from "vue";

import { getStockHistory, getStockIndicators, getStockQuote, getStockSymbolSearch } from "../api";
import { formatTimeLabel } from "../utils/formatters";

const SYMBOL_PATTERN = /^\d{4,6}$/;

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
  const dayOptions = [5, 20];

  let controller = null;

  async function refreshQuote() {
    if (controller) {
      controller.abort();
    }
    controller = new AbortController();

    const parsedSymbol = String(symbol.value || "").trim();
    quoteError.value = "";
    historyError.value = "";
    indicatorsError.value = "";

    if (!parsedSymbol) {
      quote.value = null;
      history.value = null;
      indicators.value = null;
      quoteCheckedAt.value = "";
      quoteError.value = "請先輸入股票代號";
      return;
    }

    // 新查詢先清掉舊資料，避免畫面保留上一檔股票資訊。
    quote.value = null;
    history.value = null;
    indicators.value = null;
    quoteCheckedAt.value = "";
    quoteLoading.value = true;

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

      try {
        const historyResult = await getStockHistory(resolvedSymbol, selectedDays.value, controller.signal);
        history.value = historyResult;
      } catch (error) {
        if (error.name !== "AbortError") {
          history.value = null;
          historyError.value = error.message || "股價歷史查詢失敗";
        }
      }

      try {
        const indicatorsResult = await getStockIndicators(resolvedSymbol, 60, controller.signal);
        indicators.value = indicatorsResult;
      } catch (error) {
        if (error.name !== "AbortError") {
          indicators.value = null;
          indicatorsError.value = error.message || "技術指標查詢失敗";
        }
      }

      quoteCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (error.name !== "AbortError") {
        quoteError.value = error.message || "股票報價查詢失敗";
        quote.value = null;
        history.value = null;
        indicators.value = null;
      }
    } finally {
      quoteLoading.value = false;
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

  onBeforeUnmount(() => {
    controller?.abort();
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
