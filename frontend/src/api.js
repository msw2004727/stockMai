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
    throw new Error(`Token request failed: HTTP ${response.status}`);
  }

  const payload = await response.json();
  const ttlMinutes = Number(payload?.expires_minutes ?? tokenExpiresMinutes);
  if (!payload?.access_token) {
    throw new Error("Token response missing access_token");
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

async function fetchProtected(path, signal) {
  const token = await ensureAccessToken(signal);
  let response = await fetch(`${apiBase}${path}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
    signal,
  });

  if (response.status === 401) {
    resetAccessToken();
    const refreshedToken = await ensureAccessToken(signal);
    response = await fetch(`${apiBase}${path}`, {
      headers: {
        Authorization: `Bearer ${refreshedToken}`,
      },
      signal,
    });
  }

  return response;
}

function throwApiError(feature, status, symbol = "") {
  if (status === 404 && symbol) {
    throw new Error(`${feature} not found: ${symbol}`);
  }
  if (status === 429) {
    throw new Error("Daily API quota exceeded. Please try again tomorrow.");
  }
  if (status === 401) {
    throw new Error("Authentication failed. Please refresh and try again.");
  }
  throw new Error(`${feature} failed: HTTP ${status}`);
}

export async function getHealth(signal) {
  const response = await fetch(`${apiBase}/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health check failed: HTTP ${response.status}`);
  }
  return response.json();
}

export async function getStockQuote(symbol, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetchProtected(`/stocks/quote?symbol=${encodeURIComponent(quoteSymbol)}`, signal);

  if (!response.ok) {
    throwApiError("Stock quote", response.status, quoteSymbol);
  }

  return response.json();
}

export async function getStockHistory(symbol, days = 5, signal) {
  const quoteSymbol = (symbol || "").trim();
  const response = await fetchProtected(
    `/stocks/history?symbol=${encodeURIComponent(quoteSymbol)}&days=${encodeURIComponent(days)}`,
    signal,
  );

  if (!response.ok) {
    throwApiError("Stock history", response.status, quoteSymbol);
  }

  return response.json();
}
