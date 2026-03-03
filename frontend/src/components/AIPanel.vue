<script setup>
import { computed, ref } from "vue";

import { useStockSymbolSearch } from "../composables/useStockSymbolSearch";
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";
import StrategyPanel from "./StrategyPanel.vue";

const props = defineProps({
  symbol: { type: String, default: "" },
  aiResult: { type: Object, default: null },
  aiLoading: { type: Boolean, default: false },
  aiError: { type: String, default: "" },
  aiCheckedAt: { type: String, default: "" },
  userPrompt: { type: String, default: "" },
  selectedProvider: { type: String, default: "gpt5" },
  providerOptions: { type: Array, default: () => ["gpt5", "claude", "grok", "deepseek"] },
  strategyResult: { type: Object, default: null },
  strategyLoading: { type: Boolean, default: false },
  strategyError: { type: String, default: "" },
  strategyCheckedAt: { type: String, default: "" },
});

const emit = defineEmits(["refresh", "update:symbol", "update:prompt", "change-provider"]);

const showDetail = ref(false);

const { searchResults, searchLoading, searchError, clearSearch, scheduleSearch } = useStockSymbolSearch();

function onSymbolInput(event) {
  const value = event.target.value;
  emit("update:symbol", value);
  scheduleSearch(value);
}

function onSelectSearchResult(item) {
  if (!item?.symbol) return;
  emit("update:symbol", item.symbol);
  clearSearch();
}

function onRefreshClick() {
  clearSearch();
  emit("refresh");
}

function onPromptInput(event) {
  emit("update:prompt", event.target.value);
}

function toSignalLabel(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") return "偏多";
  if (parsed === "bearish") return "偏空";
  return "中性";
}

function signalClass(signal) {
  const parsed = String(signal || "").toLowerCase();
  if (parsed === "bullish") return "rise";
  if (parsed === "bearish") return "fall";
  return "";
}

function providerLabel(provider) {
  const parsed = String(provider || "").toLowerCase();
  if (parsed === "gpt5") return "GPT-5";
  if (parsed === "claude") return "Claude";
  if (parsed === "grok") return "Grok";
  if (parsed === "deepseek") return "DeepSeek";
  return displayOrFallback(provider, "未知模型");
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  return Number(value).toFixed(digits);
}

function localize(value, fallback = "暫無資料") {
  return displayOrFallback(value, fallback);
}

function localizeError(value) {
  return localizeAiText(value) || "AI 分析失敗";
}

function toNum(value) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function shortTermEvidence(result) {
  if (!result) {
    return ["尚無可用資料，請先執行 AI 分析。"];
  }

  const evidence = [];
  const latest = result?.indicator_context?.latest || {};

  const sma5 = toNum(latest?.sma5);
  const sma20 = toNum(latest?.sma20);
  if (sma5 !== null && sma20 !== null) {
    const trendText =
      sma5 > sma20 ? "短均線在長均線上方，短線偏多。" : sma5 < sma20 ? "短均線在長均線下方，短線偏空。" : "短長均線接近，中性盤整。";
    evidence.push(`均線依據：SMA5 ${fmt(sma5, 2)}、SMA20 ${fmt(sma20, 2)}，${trendText}`);
  }

  const rsi14 = toNum(latest?.rsi14);
  if (rsi14 !== null) {
    const rsiText = rsi14 >= 70 ? "過熱" : rsi14 <= 30 ? "超賣" : rsi14 >= 55 ? "偏強" : rsi14 <= 45 ? "偏弱" : "中性";
    evidence.push(`動能依據：RSI14 ${fmt(rsi14, 1)}，目前 ${rsiText}。`);
  }

  const macd = toNum(latest?.macd);
  const macdSignal = toNum(latest?.macd_signal);
  if (macd !== null && macdSignal !== null) {
    const macdText = macd > macdSignal ? "MACD 高於訊號線，動能偏多。" : macd < macdSignal ? "MACD 低於訊號線，動能偏空。" : "MACD 接近訊號線，動能中性。";
    evidence.push(`趨勢依據：MACD ${fmt(macd, 2)}、Signal ${fmt(macdSignal, 2)}，${macdText}`);
  }

  const sentimentLabel = toSignalLabel(result?.sentiment_context?.market_sentiment);
  const sentimentSummary = localize(result?.sentiment_context?.summary, "");
  if (sentimentSummary) {
    evidence.push(`情緒依據：市場情緒 ${sentimentLabel}。${sentimentSummary}`);
  } else {
    evidence.push(`情緒依據：市場情緒 ${sentimentLabel}。`);
  }

  return evidence.slice(0, 6);
}

function parseSentimentSummary(summary) {
  const text = localize(summary, "尚無情緒摘要");
  const normalized = String(text || "").trim();
  const metrics = [];

  if (!normalized) {
    return { summary: "尚無情緒摘要", metrics };
  }

  const definitions = [
    {
      label: "情緒分數",
      icon: "score",
      patterns: [
        /分數\s*[=:]\s*([+\-]?\d+(?:\.\d+)?)/i,
        /\bscore\s*[=:]\s*([+\-]?\d+(?:\.\d+)?)/i,
      ],
    },
    {
      label: "漲跌幅",
      icon: "change",
      patterns: [
        /漲跌\s*[=:]\s*([+\-]?\d+(?:\.\d+)?%?)/i,
        /\bchange\s*[=:]\s*([+\-]?\d+(?:\.\d+)?%?)/i,
      ],
    },
    {
      label: "波動率",
      icon: "volatility",
      patterns: [
        /波動\s*[=:]\s*([+\-]?\d+(?:\.\d+)?%?)/i,
        /\bvol\s*[=:]\s*([+\-]?\d+(?:\.\d+)?%?)/i,
      ],
    },
    {
      label: "視窗天數",
      icon: "window",
      patterns: [
        /情緒視窗天數\s*[=:]\s*([+\-]?\d+(?:\.\d+)?)/i,
        /視窗天數\s*[=:]\s*([+\-]?\d+(?:\.\d+)?)/i,
        /\bwindow_days\s*[=:]\s*([+\-]?\d+(?:\.\d+)?)/i,
      ],
    },
  ];

  for (const def of definitions) {
    let matched = "";
    for (const pattern of def.patterns) {
      const result = normalized.match(pattern);
      if (result?.[1]) {
        matched = result[1];
        break;
      }
    }
    if (matched) {
      metrics.push({ label: def.label, value: matched, icon: def.icon });
    }
  }

  const cleanedSummary = normalized
    .replace(
      /[（(][^）)]*(?:分數|score|漲跌|change|波動|vol|情緒視窗天數|視窗天數|window_days)[^）)]*[）)]/gi,
      ""
    )
    .replace(/\s{2,}/g, " ")
    .trim();

  return {
    summary: cleanedSummary || "尚無情緒摘要",
    metrics,
  };
}

const sentimentInfo = computed(() => parseSentimentSummary(props.aiResult?.sentiment_context?.summary));

function buildAnalystNarratives(result) {
  if (!result) {
    return {
      bullish: "看多分析師：目前資料不足，無法建立完整偏多論述。若要提高可用性，建議先補齊近 20~60 日價格、成交量與主要指標，再觀察是否出現均線轉強與動能修復訊號。在資料不足時先小部位試單、嚴格停損，會比直接放大倉位更安全。",
      bearish: "看空分析師：目前資料不足，偏向保守。沒有足夠證據前，不應把短暫反彈視為反轉；若價格落在壓力區且量能不續，回落機率仍高。操作上建議先防守、降低部位與槓桿，等關鍵位站穩後再重新評估，避免在不確定區間反覆受損。",
      summary: "輕鬆總結：資料不足時，多空都不該太激進。先縮小部位、設好停損，再等市場自己給方向，會比硬猜高低點更穩。",
    };
  }

  const latest = result?.indicator_context?.latest || {};
  const sma5 = toNum(latest?.sma5);
  const sma20 = toNum(latest?.sma20);
  const rsi14 = toNum(latest?.rsi14);
  const macd = toNum(latest?.macd);
  const macdSignal = toNum(latest?.macd_signal);
  const consensusLabel = toSignalLabel(result?.consensus?.signal);
  const confidenceText = fmt(result?.consensus?.confidence, 2);
  const sentimentLabel = toSignalLabel(result?.sentiment_context?.market_sentiment);
  const sentimentSummary = localize(result?.sentiment_context?.summary, "目前情緒資料有限。");
  const volatilityLevel = localize(result?.sentiment_context?.volatility_level, "未知");
  const asOfDate = localize(result?.indicator_context?.as_of_date, "--");

  const maBullText =
    sma5 !== null && sma20 !== null
      ? sma5 >= sma20
        ? "短均線不弱於長均線，結構仍有撐"
        : "短均線暫弱，但未必代表趨勢終結"
      : "均線資料偏少，先以風控優先";
  const maBearText =
    sma5 !== null && sma20 !== null
      ? sma5 < sma20
        ? "短均線在長均線下方，壓力未解"
        : "即使短均線在上，也可能是假突破"
      : "均線資料偏少，先採防守假設";
  const rsiText =
    rsi14 !== null ? `RSI14 ${fmt(rsi14, 1)}` : "RSI14 資料不足";
  const macdText =
    macd !== null && macdSignal !== null
      ? `MACD ${fmt(macd, 2)} / Signal ${fmt(macdSignal, 2)}`
      : "MACD 資料不足";

  const bullish = `看多分析師：截至 ${asOfDate}，共識為「${consensusLabel}」、信心 ${confidenceText}，他認為市場仍有延續上行空間。均線觀察為 ${maBullText}；動能端 ${rsiText}、${macdText}，若沒有同步轉弱，多方節奏通常不會一次結束。情緒目前偏${sentimentLabel}、波動 ${volatilityLevel}，${sentimentSummary} 因此策略上偏向分批布局、回檔承接，但會把停損放在關鍵支撐下方，先控風險再爭取波段。`;

  const bearish = `看空分析師：同樣看截至 ${asOfDate} 的資料，他更重視「反彈是否有量能與結構支持」。目前共識「${consensusLabel}」信心 ${confidenceText} 並非壓倒性，代表方向仍可能反覆。均線面 ${maBearText}；動能面 ${rsiText}、${macdText} 若出現背離，回落風險會放大。情緒偏${sentimentLabel}、波動 ${volatilityLevel}，${sentimentSummary} 所以他主張先降槓桿、少追高，跌破支撐就先防守，等趨勢明確再調整部位。`;

  const summary =
    "輕鬆總結：看多派看的是延續機會，看空派盯的是回落風險。其實兩邊都同意，先把停損、部位上限與進出條件寫好，再跟著市場動作走，比主觀押方向更穩。";

  return { bullish, bearish, summary };
}

const analystNarratives = computed(() => buildAnalystNarratives(props.aiResult));
</script>

<template>
  <h2 class="section-title section-title-chip">AI 分析</h2>
  <p class="hint">先在行情頁查詢股價，再執行 AI 分析會更準確。</p>

  <div class="ai-control-grid">
    <div class="field-box ai-control-target">
      <p class="field-title title-chip">分析標的</p>
      <div class="query-row">
        <input
          :value="symbol"
          class="input"
          type="text"
          maxlength="20"
          inputmode="text"
          placeholder="輸入台股代號或中文名稱"
          :disabled="aiLoading"
          @input="onSymbolInput"
          @keydown.enter.prevent="onRefreshClick"
        />
        <button type="button" class="btn" :disabled="aiLoading" @click="onRefreshClick">
          {{ aiLoading ? "分析中..." : "執行 AI 分析" }}
        </button>
        <span v-if="aiCheckedAt" class="checked-at no-wrap">更新時間：{{ aiCheckedAt }}</span>
      </div>
      <p v-if="searchLoading" class="sub">正在搜尋代號...</p>
      <p v-else-if="searchError" class="sub warn-text">{{ searchError }}</p>
      <ul v-else-if="searchResults.length" class="search-list" role="listbox" aria-label="股票代號建議">
        <li v-for="item in searchResults" :key="item.symbol" class="search-item-wrap">
          <button
            type="button"
            class="search-item"
            @mousedown.prevent="onSelectSearchResult(item)"
            @click="onSelectSearchResult(item)"
          >
            <span class="search-symbol">{{ item.symbol }}</span>
            <span class="search-name">{{ item.name }}</span>
          </button>
        </li>
      </ul>
    </div>

    <div class="field-box ai-control-provider">
      <p class="field-title title-chip">AI 核心</p>
      <div class="period-row provider-grid">
        <button
          v-for="provider in providerOptions"
          :key="provider"
          type="button"
          class="period-btn"
          :class="{ active: selectedProvider === provider }"
          :disabled="aiLoading"
          @click="emit('change-provider', provider)"
        >
          {{ providerLabel(provider) }}
        </button>
      </div>
    </div>

    <div class="field-box ai-control-prompt">
      <p class="field-title title-chip">你想要 AI 著重的分析重點</p>
      <textarea
        :value="userPrompt"
        class="textarea"
        rows="2"
        placeholder="例如：短線壓力支撐、進出場節奏、停損停利建議"
        :disabled="aiLoading"
        @input="onPromptInput"
      ></textarea>
    </div>
  </div>

  <div class="stack-block">
    <StrategyPanel
      :symbol="symbol"
      :strategy-result="strategyResult"
      :strategy-loading="strategyLoading"
      :strategy-error="strategyError"
      :strategy-checked-at="strategyCheckedAt"
    />
  </div>

  <div v-if="aiError" class="card error stack-block">{{ localizeError(aiError) }}</div>

  <div v-else-if="aiResult">
    <article class="card full-span stack-block">
      <p class="label title-chip">AI 共識結果</p>
      <p class="value" :class="signalClass(aiResult.consensus?.signal)" style="margin-top:8px;">
        {{ toSignalLabel(aiResult.consensus?.signal) }}
        <span style="font-size:1rem;font-weight:600;">（信心 {{ fmt(aiResult.consensus?.confidence, 2) }}）</span>
      </p>
      <p class="sub" style="margin-top:8px;">{{ localize(aiResult.consensus?.summary) }}</p>
      <p class="sub" style="margin-top:4px;font-size:0.82rem;">
        主要來源：{{ providerLabel(aiResult.consensus?.source_provider || "") }}
        ・ 回退：{{ aiResult.fallback_used ? "有" : "無" }}
      </p>
    </article>

    <article class="card full-span stack-block">
      <p class="label title-chip">多空分析師觀點</p>

      <div class="analyst-field analyst-bull">
        <p class="analyst-title">看多分析師</p>
        <p class="analyst-body">{{ analystNarratives.bullish }}</p>
      </div>

      <div class="analyst-field analyst-bear">
        <p class="analyst-title">看空分析師</p>
        <p class="analyst-body">{{ analystNarratives.bearish }}</p>
      </div>

      <div class="analyst-divider" role="separator" aria-hidden="true"></div>
      <p class="analyst-summary-title">輕鬆總結</p>
      <p class="analyst-summary">{{ analystNarratives.summary }}</p>
    </article>

    <button class="detail-toggle stack-block" @click="showDetail = !showDetail">
      {{ showDetail ? "收合AI反饋數據" : "展開AI反饋數據" }}
    </button>

    <template v-if="showDetail">
      <div class="detail-stack stack-block">
        <article class="card full-span">
          <p class="label title-chip">AI依據資料分析</p>
          <ul class="short-term-evidence">
            <li v-for="(line, idx) in shortTermEvidence(aiResult)" :key="`short-evidence-${idx}`">
              {{ line }}
            </li>
          </ul>
        </article>

        <article class="card full-span">
          <p class="label title-chip">市場情緒</p>
          <p class="sub" style="margin-top:6px;">
            <span :class="signalClass(aiResult.sentiment_context?.market_sentiment)" style="font-weight:700;">
              {{ toSignalLabel(aiResult.sentiment_context?.market_sentiment) }}
            </span>
            ・ 波動：{{ localize(aiResult.sentiment_context?.volatility_level, "--") }}
          </p>
          <div v-if="sentimentInfo.metrics.length" class="sentiment-metrics">
            <div v-for="item in sentimentInfo.metrics" :key="item.label" class="sentiment-chip">
              <span class="sentiment-icon" :class="`sentiment-icon-${item.icon}`" aria-hidden="true"></span>
              <span class="sentiment-chip-label">{{ item.label }}</span>
              <span class="sentiment-chip-value">{{ item.value }}</span>
            </div>
          </div>
          <p class="sub">{{ sentimentInfo.summary }}</p>
        </article>

        <article class="card full-span">
          <p class="label title-chip">技術指標快照</p>
          <p class="sub" style="margin-top:6px;">
            來源：{{ localize(aiResult.indicator_context?.history_source, "--") }}
            ・ 日期：{{ localize(aiResult.indicator_context?.as_of_date, "--") }}
          </p>
          <p class="sub">
            SMA5：{{ fmt(aiResult.indicator_context?.latest?.sma5, 2) }}
            ／ SMA20：{{ fmt(aiResult.indicator_context?.latest?.sma20, 2) }}
          </p>
          <p class="sub">
            RSI14：{{ fmt(aiResult.indicator_context?.latest?.rsi14, 1) }}
            ／ MACD：{{ fmt(aiResult.indicator_context?.latest?.macd, 2) }}
          </p>
        </article>

        <article v-for="item in aiResult.results" :key="item.provider" class="card">
          <p class="label title-chip">{{ providerLabel(item.provider) }}</p>
          <p class="value" :class="item.ok ? (signalClass(item.data?.signal) || 'ok') : 'warn'" style="margin-top:6px;font-size:1rem;">
            {{ item.ok ? toSignalLabel(item.data?.signal) : "失敗" }}
          </p>
          <p class="sub" v-if="item.ok">{{ localize(item.data?.summary) }}</p>
          <p class="sub" v-else>{{ localizeError(item.error) }}</p>
          <p class="sub" v-if="item.ok" style="font-size:0.82rem;">信心：{{ fmt(item.data?.confidence, 2) }}</p>
        </article>

        <article class="card full-span feedback-reminder-card">
          <p class="feedback-reminder-text">提醒：目前測試版參考資料不多，分析僅供參考。</p>
        </article>
      </div>
    </template>
  </div>
</template>
