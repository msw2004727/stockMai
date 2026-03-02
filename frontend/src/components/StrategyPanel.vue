<script setup>
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
    return "買進";
  }
  if (parsed === "sell") {
    return "賣出";
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
    return "技術指標（價格與趨勢訊號）";
  }
  if (parsed === "sentiment") {
    return "情緒判讀（近期價格行為推估）";
  }
  if (parsed === "ai_consensus") {
    return "AI 共識（多模型綜合判斷）";
  }
  return key;
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
    return "N/A";
  }
  return Number(value).toFixed(digits);
}
</script>

<template>
  <article class="card full-span">
    <p class="label">策略決策（MVP）</p>
    <p class="sub no-wrap">
      標的：{{ symbol || "N/A" }}
      <span v-if="strategyCheckedAt">・更新：{{ strategyCheckedAt }}</span>
    </p>

    <p v-if="strategyLoading" class="sub">計算中...</p>
    <p v-else-if="strategyError" class="sub warn">{{ strategyError }}</p>

    <template v-else-if="strategyResult">
      <p class="value">
        {{ toActionLabel(strategyResult.action) }}
        （信心 {{ fmt(strategyResult.confidence, 2) }}）
      </p>
      <p class="sub">風險等級：{{ toRiskLabel(strategyResult.risk_level) }}</p>
      <p class="sub">綜合分數：{{ fmt(strategyResult.weighted_score, 3) }}</p>

      <div class="divider"></div>
      <p class="label">構成分數（用來說明決策來源）</p>
      <p
        v-for="(item, key) in strategyResult.components || {}"
        :key="`component-${key}`"
        class="sub"
      >
        {{ componentLabel(key) }}：{{ signalLabel(item.label) }}（分數 {{ fmt(item.score, 3) }}）
      </p>

      <div class="divider"></div>
      <p class="label">決策理由</p>
      <p
        v-for="(reason, idx) in strategyResult.reasons || []"
        :key="`reason-${idx}`"
        class="sub"
      >
        {{ idx + 1 }}. {{ reason }}
      </p>
    </template>

    <p v-else class="sub">尚未產生策略結果。</p>
  </article>
</template>
