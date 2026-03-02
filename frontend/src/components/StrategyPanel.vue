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
    <p class="sub">
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

