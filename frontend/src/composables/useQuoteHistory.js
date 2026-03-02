import { onBeforeUnmount, ref } from "vue";

import { getStockHistory, getStockIndicators, getStockQuote } from "../api";
import { formatTimeLabel } from "../utils/formatters";

export function useQuoteHistory(initialSymbol = "2330") {
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

    quoteLoading.value = true;
    quoteError.value = "";
    historyError.value = "";
    indicatorsError.value = "";

    try {
      const quoteResult = await getStockQuote(symbol.value, controller.signal);
      quote.value = quoteResult;

      try {
        const historyResult = await getStockHistory(symbol.value, selectedDays.value, controller.signal);
        history.value = historyResult;
      } catch (error) {
        if (error.name !== "AbortError") {
          history.value = null;
          historyError.value = error.message || "無法查詢股價走勢";
        }
      }

      try {
        const indicatorsResult = await getStockIndicators(symbol.value, 60, controller.signal);
        indicators.value = indicatorsResult;
      } catch (error) {
        if (error.name !== "AbortError") {
          indicators.value = null;
          indicatorsError.value = error.message || "無法查詢技術指標";
        }
      }

      quoteCheckedAt.value = formatTimeLabel(new Date());
    } catch (error) {
      if (error.name !== "AbortError") {
        quoteError.value = error.message || "無法查詢股票報價";
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
    refreshQuote();
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
