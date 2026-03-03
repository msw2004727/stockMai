const rawApiBase = import.meta.env.VITE_API_BASE ?? "/api";
const apiBase = rawApiBase.replace(/\/+$/, "");

const tokenUserId = (import.meta.env.VITE_API_USER_ID ?? "h5-demo-user").trim() || "h5-demo-user";
const tokenExpiresMinutes = Number(import.meta.env.VITE_API_TOKEN_EXPIRES_MINUTES ?? 60) || 60;
const tokenRefreshLeewayMs = 30 * 1000;

let accessToken = "";
let tokenExpiresAtMs = 0;
let tokenRequestPromise = null;

function resetAccessToken() {
  accessToken = "";
  tokenExpiresAtMs = 0;
}

async function requestAccessToken(signal) {
  const response = await fetch(`${apiBase}/auth/token`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      user_id: tokenUserId,
      expires_minutes: tokenExpiresMinutes,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Token 取得失敗（HTTP ${response.status}）`);
  }

  const payload = await response.json();
  const ttlMinutes = Number(payload?.expires_minutes ?? tokenExpiresMinutes);
  if (!payload?.access_token) {
    throw new Error("Token 回應缺少 access_token");
  }

  accessToken = payload.access_token;
  tokenExpiresAtMs = Date.now() + ttlMinutes * 60 * 1000;
  return accessToken;
}

async function ensureAccessToken(signal) {
  if (accessToken && Date.now() + tokenRefreshLeewayMs < tokenExpiresAtMs) {
    return accessToken;
  }

  if (!tokenRequestPromise) {
    tokenRequestPromise = requestAccessToken(signal).finally(() => {
      tokenRequestPromise = null;
    });
  }

  return tokenRequestPromise;
}

async function fetchProtected(
  path,
  { method = "GET", headers = {}, body = undefined, signal = undefined, cache = undefined } = {},
) {
  const token = await ensureAccessToken(signal);
  let response = await fetch(`${apiBase}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...headers,
    },
    body,
    signal,
    cache,
  });

  if (response.status === 401) {
    resetAccessToken();
    const refreshedToken = await ensureAccessToken(signal);
    response = await fetch(`${apiBase}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${refreshedToken}`,
        ...headers,
      },
      body,
      signal,
      cache,
    });
  }

  return response;
}

function throwApiError(feature, status, symbol = "") {
  if (status === 404 && symbol) {
    throw new Error(`${feature} 查無資料：${symbol}`);
  }
  if (status === 429) {
    throw new Error("今日 API 額度已用完，請明天再試。");
  }
  if (status === 401) {
    throw new Error("驗證失敗，請重新整理後再試。");
  }
  throw new Error(`${feature} 失敗（HTTP ${status}）`);
}

export async function getHealth(signal) {
  const response = await fetch(`${apiBase}/health`, { signal });
  if (!response.ok) {
    throw new Error(`健康檢查失敗（HTTP ${response.status}）`);
  }
  return response.json();
}

export async function getStockQuote(symbol, signal) {
  const quoteSymbol = (symbol || "").trim();
  const nonce = Date.now();
  const response = await fetchProtected(
    `/stocks/quote?symbol=${encodeURIComponent(quoteSymbol)}&_=${encodeURIComponent(nonce)}`,
    { signal, cache: "no-store" },
  );

  if (!response.ok) {
    throwApiError("股票報價", response.status, quoteSymbol);
  }

  return response.json();
}

export async function getStockHistory(symbol, days = 5, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetchProtected(
    `/stocks/history?symbol=${encodeURIComponent(quoteSymbol)}&days=${encodeURIComponent(days)}`,
    { signal },
  );

  if (!response.ok) {
    throwApiError("股價走勢", response.status, quoteSymbol);
  }

  return response.json();
}

export async function getStockIndicators(symbol, days = 60, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetchProtected(
    `/stocks/indicators?symbol=${encodeURIComponent(quoteSymbol)}&days=${encodeURIComponent(days)}`,
    { signal },
  );

  if (!response.ok) {
    throwApiError("技術指標", response.status, quoteSymbol);
  }

  return response.json();
}

export async function analyzeStock(symbol, userPrompt = "", providers = ["gpt5"], signal) {
  const quoteSymbol = (symbol || "").trim();
  const payload = {
    symbol: quoteSymbol,
    user_prompt: (userPrompt || "").trim(),
    providers: providers.length > 0 ? providers : ["gpt5"],
  };

  const analyzedResponse = await fetchProtected("/ai/analyze", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!analyzedResponse.ok) {
    throwApiError("AI 分析", analyzedResponse.status, quoteSymbol);
  }
  return analyzedResponse.json();
}

export async function getStrategyDecision(symbol, userPrompt = "", providers = ["gpt5"], signal) {
  const quoteSymbol = (symbol || "").trim();
  const payload = {
    symbol: quoteSymbol,
    user_prompt: (userPrompt || "").trim(),
    providers: providers.length > 0 ? providers : ["gpt5"],
  };

  const response = await fetchProtected("/strategy/decision", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throwApiError("策略決策", response.status, quoteSymbol);
  }

  return response.json();
}

export async function getStockSymbolSearch(query, limit = 8, signal) {
  const keyword = (query || "").trim();
  const cappedLimit = Math.min(Math.max(Number(limit) || 8, 1), 20);
  const response = await fetchProtected(
    `/stocks/search?q=${encodeURIComponent(keyword)}&limit=${encodeURIComponent(cappedLimit)}`,
    { signal },
  );

  if (!response.ok) {
    throwApiError("股票代號搜尋", response.status, keyword);
  }

  return response.json();
}

export async function resolveStockSymbol(query, limit = 5, signal) {
  const keyword = (query || "").trim();
  const cappedLimit = Math.min(Math.max(Number(limit) || 5, 1), 10);
  const response = await fetchProtected(
    `/stocks/resolve?q=${encodeURIComponent(keyword)}&limit=${encodeURIComponent(cappedLimit)}`,
    { signal },
  );

  if (!response.ok) {
    throwApiError("股票代號解析", response.status, keyword);
  }

  return response.json();
}

export async function getStockMarketMovers(limit = 6, signal) {
  const cappedLimit = Math.min(Math.max(Number(limit) || 6, 3), 20);
  const response = await fetchProtected(
    `/stocks/movers?limit=${encodeURIComponent(cappedLimit)}`,
    { signal, cache: "no-store" },
  );

  if (!response.ok) {
    throwApiError("市場排行", response.status);
  }

  return response.json();
}

