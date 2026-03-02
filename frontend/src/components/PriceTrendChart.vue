<script setup>
import { computed } from "vue";

const props = defineProps({
  points: {
    type: Array,
    default: () => [],
  },
});

const width = 740;
const height = 220;
const padX = 20;
const padY = 24;

const closes = computed(() => props.points.map((p) => p.close));

const domain = computed(() => {
  if (closes.value.length === 0) {
    return { min: 0, max: 1 };
  }
  const min = Math.min(...closes.value);
  const max = Math.max(...closes.value);
  if (min === max) {
    return { min: min - 1, max: max + 1 };
  }
  return { min, max };
});

function toX(index, total) {
  if (total <= 1) {
    return width / 2;
  }
  const usable = width - padX * 2;
  return padX + (index / (total - 1)) * usable;
}

function toY(price) {
  const usable = height - padY * 2;
  const ratio = (price - domain.value.min) / (domain.value.max - domain.value.min);
  return height - padY - ratio * usable;
}

const polylinePoints = computed(() =>
  props.points.map((point, index) => `${toX(index, props.points.length)},${toY(point.close)}`).join(" "),
);

const areaPoints = computed(() => {
  if (!polylinePoints.value) {
    return "";
  }
  const firstX = toX(0, props.points.length);
  const lastX = toX(props.points.length - 1, props.points.length);
  const baseline = height - padY;
  return `${firstX},${baseline} ${polylinePoints.value} ${lastX},${baseline}`;
});

const dots = computed(() =>
  props.points.map((point, index) => ({
    x: toX(index, props.points.length),
    y: toY(point.close),
    date: point.date,
    close: point.close,
  })),
);

const firstPoint = computed(() => props.points[0] || null);
const lastPoint = computed(() => props.points[props.points.length - 1] || null);
</script>

<template>
  <div v-if="points.length < 2" class="chart-empty">資料不足，暫時無法繪製趨勢圖。</div>
  <div v-else class="chart-wrap">
    <svg :viewBox="`0 0 ${width} ${height}`" class="chart-svg" role="img" aria-label="最近收盤價趨勢圖">
      <defs>
        <linearGradient id="trendArea" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" class="trend-stop-start" stop-opacity="0.28" />
          <stop offset="100%" class="trend-stop-end" stop-opacity="0.04" />
        </linearGradient>
      </defs>
      <polyline :points="areaPoints" fill="url(#trendArea)" stroke="none" />
      <polyline :points="polylinePoints" fill="none" class="trend-line" stroke-width="3.2" stroke-linecap="round" />
      <circle
        v-for="point in dots"
        :key="point.date"
        :cx="point.x"
        :cy="point.y"
        r="3.3"
        class="trend-dot"
      />
    </svg>

    <div class="chart-meta">
      <p>
        起點：<strong>{{ firstPoint.date }}</strong> / {{ firstPoint.close }}
      </p>
      <p>
        終點：<strong>{{ lastPoint.date }}</strong> / {{ lastPoint.close }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.chart-wrap {
  margin-top: 8px;
}

.chart-svg {
  width: 100%;
  height: auto;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--trend-bg);
}

.trend-stop-start {
  stop-color: var(--trend-fill);
}

.trend-stop-end {
  stop-color: var(--trend-fill);
}

.trend-line {
  stroke: var(--trend-fill);
}

.trend-dot {
  fill: var(--brand);
}

.chart-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-top: 8px;
  color: var(--muted);
  font-size: 0.88rem;
}

.chart-meta p {
  margin: 0;
}

.chart-empty {
  margin-top: 8px;
  color: var(--warn);
}

@media (max-width: 767px) {
  .chart-meta {
    flex-direction: column;
  }
}
</style>
