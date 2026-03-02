<script setup>
import { displayOrFallback, localizeAiText } from "../utils/aiTextLocalizer";

defineProps({
  symbol: { type: String, default: "" },
  strategyResult: { type: Object, default: null },
  strategyLoading: { type: Boolean, default: false },
  strategyError: { type: String, default: "" },
  strategyCheckedAt: { type: String, default: "" },
});

function toActionLabel(action) {
  const parsed = String(action || "").toLowerCase();
  if (parsed === "buy") return "偏  多";
  if (parsed === "sell") return "偏  空";
  return "觀  望";
}

function actionClass(action) {
  const parsed = String(action || "").toLowerCase();
  if (parsed === "buy") return "action-buy";
  if (parsed === "sell") return "action-sell";
  return "action-hold";
}

function toRiskLabel(level) {
  const parsed = String(level || "").toLowerCase();
  if (parsed === "low") return "低";
  if (parsed === "high") return "高";
  return "中";
}

function componentLabel(key) {
  const parsed = String(key || "").toLowerCase();
  if (parsed === "indicators") return "技術指標";
  if (parsed === "sentiment") return "市場情緒";
  if (parsed === "ai_consensus") return "AI 共識";
  return displayOrFallback(key, "未知");
}

function signalLabel(value) {
  const parsed = String(value || "").toLowerCase();
  if (parsed === "bullish") return "偏多";
  if (parsed === "bearish") return "偏空";
  return "中性";
}

function signalClass(value) {
  const parsed = String(value || "").toLowerCase();
  if (parsed === "bullish") return "rise";
  if (parsed === "bearish") return "fall";
  return "";
}

function componentActionClass(value) {
  const parsed = String(value || "").toLowerCase();
  if (parsed === "bullish") return "action-buy";
  if (parsed === "bearish") return "action-sell";
  return "action-hold";
}

function confidencePct(confidence) {
  const v = parseFloat(confidence);
  if (isNaN(v)) return 0;
  return Math.round(Math.min(Math.max(v, 0), 1) * 100);
}

function componentScorePct(item) {
  const v = parseFloat(item?.score ?? 0);
  if (isNaN(v)) return 0;
  return Math.round(Math.min(Math.abs(v), 1) * 100);
}

function fmt(value, digits = 2) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "－";
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
    <p class="label">策略決策</p>
    <p class="sub no-wrap" style="font-size:0.82rem;">
      標的：{{ symbol || "未輸入" }}
      <span v-if="strategyCheckedAt">・更新：{{ strategyCheckedAt }}</span>
    </p>

    <p v-if="strategyLoading" class="sub" style="margin-top:12px;">策略計算中...</p>
    <p v-else-if="strategyError" class="sub warn" style="margin-top:12px;">{{ localizeError(strategyError) }}</p>

    <template v-else-if="strategyResult">

      <!-- Action Badge -->
      <div class="strategy-action-row">
        <div class="action-badge" :class="actionClass(strategyResult.action)">
          {{ toActionLabel(strategyResult.action) }}
        </div>
      </div>

      <!-- 信心進度條 -->
      <div class="confidence-row">
        <span class="confidence-label">信心</span>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="actionClass(strategyResult.action)"
            :style="{ width: confidencePct(strategyResult.confidence) + '%' }"
          ></div>
        </div>
        <span class="confidence-pct">{{ confidencePct(strategyResult.confidence) }}%</span>
      </div>

      <!-- 風險 + 分數 -->
      <div class="strategy-meta-row">
        <span class="sub">風險：{{ toRiskLabel(strategyResult.risk_level) }}</span>
        <span class="sub">分數：{{ fmt(strategyResult.weighted_score, 3) }}</span>
      </div>

      <div class="divider"></div>

      <!-- 分項評估進度條 -->
      <p class="field-title">分項評估</p>
      <div
        v-for="(item, key) in strategyResult.components || {}"
        :key="`comp-${key}`"
        class="component-row"
      >
        <span class="component-name">{{ componentLabel(key) }}</span>
        <div class="progress-track">
          <div
            class="progress-fill"
            :class="componentActionClass(item.label)"
            :style="{ width: componentScorePct(item) + '%' }"
          ></div>
        </div>
        <span class="component-signal" :class="signalClass(item.label)">
          {{ signalLabel(item.label) }}
        </span>
      </div>

      <div class="divider"></div>

      <!-- 決策理由 -->
      <p class="field-title">決策理由</p>
      <p
        v-for="(reason, idx) in strategyResult.reasons || []"
        :key="`reason-${idx}`"
        class="sub"
      >
        {{ idx + 1 }}. {{ localize(reason) }}
      </p>

    </template>

    <p v-else class="sub" style="margin-top:12px;">尚未執行策略決策。</p>
  </article>
</template>
