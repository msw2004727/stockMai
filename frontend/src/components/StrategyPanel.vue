<script setup>
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";

defineProps({
  symbol: {
    type: String,
    default: "",
  },
  strategyResult: {
    type: Object,
    default: null,
  },
  strategyLoading: {
    type: Boolean,
    default: false,
  },
  strategyError: {
    type: String,
    default: "",
  },
  strategyCheckedAt: {
    type: String,
    default: "",
  },
});

function toActionLabel(action) {
  const parsed = String(action || "").toLowerCase();
  if (parsed === "buy") {
    return "偏多";
  }
  if (parsed === "sell") {
    return "偏空";
  }
  return "觀望";
}

function toRiskLabel(level) {
  const parsed = String(level || "").toLowerCase();
  if (parsed === "low") {
    return "低";
  }
  if (parsed === "high") {
    return "高";
  }
  return "中";
}

function componentLabel(key) {
  const parsed = String(key || "").toLowerCase();
  if (parsed === "indicators") {
    return "技術指標";
  }
  if (parsed === "sentiment") {
    return "市場情緒";
  }
  if (parsed === "ai_consensus") {
    return "AI 共識";
  }
  return displayOrFallback(key, "未知");
}

function signalLabel(value) {
  const parsed = String(value || "").toLowerCase();
  if (parsed === "bullish") {
    return "偏多";
  }
  if (parsed === "bearish") {
    return "偏空";
  }
  return "中性";
}

function fmt(value, digits = 4) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "暫無資料";
  }
  return Number(value).toFixed(digits);
}

function localize(value, fallback = "暫無資料") {
  return displayOrFallback(value, fallback);
}

function localizeError(value) {
  return localizeAiText(value) || "策略決策失敗";
}
</script>

<template>
  <article class="card full-span">
    <p class="label">策略決策（MVP）</p>
    <p class="sub no-wrap">
      標的：{{ symbol || "未輸入" }}
      <span v-if="strategyCheckedAt">，更新：{{ strategyCheckedAt }}</span>
    </p>

    <p v-if="strategyLoading" class="sub">策略計算中...</p>
    <p v-else-if="strategyError" class="sub warn">{{ localizeError(strategyError) }}</p>

    <template v-else-if="strategyResult">
      <div class="field-box compact-box">
        <p class="field-title">總結</p>
        <p class="value">{{ toActionLabel(strategyResult.action) }}（信心 {{ fmt(strategyResult.confidence, 2) }}）</p>
        <p class="sub">風險等級：{{ toRiskLabel(strategyResult.risk_level) }}</p>
        <p class="sub">綜合分數：{{ fmt(strategyResult.weighted_score, 3) }}</p>
      </div>

      <div class="field-box compact-box">
        <p class="field-title">分項分數</p>
        <p v-for="(item, key) in strategyResult.components || {}" :key="`component-${key}`" class="sub">
          {{ componentLabel(key) }}：{{ signalLabel(item.label) }}（{{ fmt(item.score, 3) }}）
        </p>
      </div>

      <div class="field-box compact-box">
        <p class="field-title">決策理由</p>
        <p v-for="(reason, idx) in strategyResult.reasons || []" :key="`reason-${idx}`" class="sub">
          {{ idx + 1 }}. {{ localize(reason) }}
        </p>
      </div>
    </template>

    <p v-else class="sub">尚未執行策略決策。</p>
  </article>
</template>
