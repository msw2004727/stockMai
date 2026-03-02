const rawApiBase = import.meta.env.VITE_API_BASE ?? "/api";
const apiBase = rawApiBase.replace(/\/+$/, "");

export async function getHealth(signal) {
  const response = await fetch(`${apiBase}/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health check failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function getStockQuote(symbol, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetch(`${apiBase}/stocks/quote?symbol=${encodeURIComponent(quoteSymbol)}`, {
    signal,
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`查無股票代號：${quoteSymbol}`);
    }
    throw new Error(`Stock quote failed: HTTP ${response.status}`);
  }

  return response.json();
}

export async function getStockHistory(symbol, days = 5, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetch(
    `${apiBase}/stocks/history?symbol=${encodeURIComponent(quoteSymbol)}&days=${encodeURIComponent(days)}`,
    { signal },
  );

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error(`查無股票歷史資料：${quoteSymbol}`);
    }
    throw new Error(`Stock history failed: HTTP ${response.status}`);
  }

  return response.json();
}
