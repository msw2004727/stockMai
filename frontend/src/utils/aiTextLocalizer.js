export const AI_TEXT_REPLACEMENTS = [
  [/\bprice_action_heuristic\b/gi, "價格行為啟發式"],
  [/No recent market data available for sentiment inference\.?/gi, "近期沒有可用市場資料，暫時無法推估市場情緒。"],
  [/Heuristic sentiment is bullish/gi, "啟發式情緒判讀為偏多"],
  [/Heuristic sentiment is bearish/gi, "啟發式情緒判讀為偏空"],
  [/Heuristic sentiment is neutral/gi, "啟發式情緒判讀為中性"],
  [/sentiment\s+window_days\s*=\s*0/gi, "情緒視窗天數 = 0"],
  [/\bwindow_days\s*=\s*0/gi, "視窗天數 = 0"],
  [/\bunknown\b/gi, "未知"],
  [/\bnone\b/gi, "無"],
  [/\bN\/A\b/gi, "暫無資料"],
];

export function localizeAiText(value) {
  if (value === null || value === undefined) {
    return "";
  }

  let text = String(value);
  for (const [pattern, replacement] of AI_TEXT_REPLACEMENTS) {
    text = text.replace(pattern, replacement);
  }

  text = text.replace(/\bscore\s*=\s*([+\-]?\d+(?:\.\d+)?)/gi, "分數=$1");
  text = text.replace(/\bchange\s*=\s*([+\-]?\d+(?:\.\d+)?%?)/gi, "漲跌=$1");
  text = text.replace(/\bvol\s*=\s*([+\-]?\d+(?:\.\d+)?%?)/gi, "波動=$1");

  return text.trim();
}

export function displayOrFallback(value, fallback = "暫無資料") {
  const text = localizeAiText(value);
  return text || fallback;
}
