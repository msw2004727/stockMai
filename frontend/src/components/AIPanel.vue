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
      bullish: "看多分析師：目前資料不足，暫時無法建立完整偏多論述，建議先補齊行情與指標資料後再判讀。",
      bearish: "看空分析師：目前資料不足，暫時無法建立完整偏空論述，建議先補齊行情與指標資料後再判讀。",
      summary: "輕鬆總結：先把資料補齊，再來討論多空，會比硬猜方向更有勝率。",
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
  const sourceLabel = localize(result?.indicator_context?.history_source, "--");
  const asOfDate = localize(result?.indicator_context?.as_of_date, "--");

  const maBullComment =
    sma5 !== null && sma20 !== null
      ? sma5 > sma20
        ? "短均線在長均線之上，代表短線結構仍偏強"
        : "短均線尚未站穩長均線，但若能快速翻揚仍可能形成回升波"
      : "均線資料不足，需保留彈性看法";

  const maBearComment =
    sma5 !== null && sma20 !== null
      ? sma5 < sma20
        ? "短均線落在長均線下方，代表上方壓力仍重"
        : "即使短均線在上，若無法持續放量也可能只是短暫反彈"
      : "均線資料不足，需優先防守";

  const rsiBullComment =
    rsi14 !== null
      ? rsi14 >= 55
        ? "動能維持在偏強區，回檔後仍有機會再攻"
        : "雖未進入強勢區，但也尚未全面轉弱，可觀察轉強訊號"
      : "RSI 資料不足，先以價格行為為主";

  const rsiBearComment =
    rsi14 !== null
      ? rsi14 <= 45
        ? "動能偏弱，容易出現反彈後再下的節奏"
        : "即便 RSI 不低，也可能在高檔鈍化後反轉"
      : "RSI 資料不足，需提高警戒";

  const macdBullComment =
    macd !== null && macdSignal !== null
      ? macd >= macdSignal
        ? "MACD 仍在訊號線之上，偏多趨勢有延續空間"
        : "MACD 暫時落後訊號線，但只要快速翻正仍可視為洗盤"
      : "MACD 資料不足，需搭配量價確認";

  const macdBearComment =
    macd !== null && macdSignal !== null
      ? macd < macdSignal
        ? "MACD 低於訊號線，代表反彈動能不足"
        : "MACD 雖在上方，但若柱體縮短代表多方力道正在流失"
      : "MACD 資料不足，先採保守假設";

  const bullish = [
    `看多分析師會先從結構判讀：截至 ${asOfDate}，共識訊號為「${consensusLabel}」，信心 ${confidenceText}。在他看來，只要不是明確偏空，市場就仍存在上攻與輪動機會。`,
    `均線方面，SMA5 ${fmt(sma5, 2)}、SMA20 ${fmt(sma20, 2)}，${maBullComment}。這通常意味著短線資金並未全面撤退，回檔容易吸引承接買盤。`,
    `動能方面，RSI14 ${fmt(rsi14, 1)}，${rsiBullComment}；MACD ${fmt(macd, 2)}、Signal ${fmt(macdSignal, 2)}，${macdBullComment}。看多派會把這組訊號解讀為「趨勢雖有波動，但尚未失去主導權」。`,
    `情緒與波動方面，目前市場情緒偏向${sentimentLabel}、波動等級 ${volatilityLevel}。${sentimentSummary} 看多方會認為只要利空沒有擴大，價格仍可透過整理後再上攻。`,
    `實務策略上，看多分析師通常不建議一次重壓，而是分批進場、分段驗證。第一筆部位偏試單，若突破關鍵壓力且量能延續，再逐步加碼；若跌破前低或跌破關鍵均線，則紀律停損。`,
    `他的核心觀點是：偏多不是盲目樂觀，而是在可控風險下，讓數據證明趨勢延續。資料來源（${sourceLabel}）若持續更新，勝率會比單靠情緒追價更穩定。`,
  ].join("");

  const bearish = [
    `看空分析師的出發點是「先保本再求勝」。他同樣看到截至 ${asOfDate} 的共識訊號為「${consensusLabel}」，但會提醒：只要信心不是壓倒性，行情就可能在區間裡反覆震盪，追高容易吃虧。`,
    `均線面上，SMA5 ${fmt(sma5, 2)}、SMA20 ${fmt(sma20, 2)}，${maBearComment}。在看空派眼裡，這代表上方壓力帶仍在，任何反彈都要先假設為「壓力測試」，不是直接認定反轉。`,
    `動能面上，RSI14 ${fmt(rsi14, 1)}，${rsiBearComment}；MACD ${fmt(macd, 2)}、Signal ${fmt(macdSignal, 2)}，${macdBearComment}。看空派會特別關注「價漲量縮」與「指標背離」，這兩者常是轉弱前兆。`,
    `情緒面目前偏向${sentimentLabel}、波動等級 ${volatilityLevel}。${sentimentSummary} 看空分析師會解讀為：市場可能過度樂觀或過度敏感，消息面一變，回落速度可能比上漲更快。`,
    `實務上他傾向先設停利停損再談進場。若價格無法站穩壓力、或回測支撐失敗，就減碼或轉防守；即使做多，也要求部位更小、槓桿更低，避免一次錯判造成大幅回撤。`,
    `他的核心觀點是：風險管理要先於方向判斷。即便最後行情上漲，只要過程中風險配置不當，報酬也可能被回撤吃掉。`,
  ].join("");

  const summary =
    "輕鬆總結：看多派認為結構還有延續空間，看空派提醒反彈不一定等於反轉。兩邊其實都同意一件事：先訂好停損與部位上限，再讓市場證明方向，會比一次重壓更安心。";

  return { bullish, bearish, summary };
}

const analystNarratives = computed(() => buildAnalystNarratives(props.aiResult));
</script>

<template>
  <h2 class="section-title section-title-chip">AI 分析</h2>
  <p class="hint">先在行情頁查詢股價，再執行 AI 分析會更準確。</p>

  <div class="field-box">
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

  <div class="field-box">
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

  <div class="field-box">
    <p class="field-title title-chip">你想要 AI 著重的分析重點</p>
    <textarea
      :value="userPrompt"
      class="textarea"
      rows="3"
      placeholder="例如：短線壓力支撐、進出場節奏、停損停利建議"
      :disabled="aiLoading"
      @input="onPromptInput"
    ></textarea>
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
          <p class="sub warn-text" style="margin-top:8px;font-size:0.82rem;">
            提醒：目前此版本參考資料不多，此分析僅供參考，待後續改版。
          </p>
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
      </div>
    </template>
  </div>
</template>
