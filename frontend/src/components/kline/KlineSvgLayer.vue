<script setup>
const props = defineProps({
  width: { type: Number, required: true },
  height: { type: Number, required: true },
  padX: { type: Number, required: true },
  priceTop: { type: Number, required: true },
  volumeBottom: { type: Number, required: true },
  priceBottom: { type: Number, required: true },
  volumeGap: { type: Number, required: true },
  tooltipWidth: { type: Number, required: true },
  tooltipHeight: { type: Number, required: true },
  bars: { type: Array, default: () => [] },
  candleWidth: { type: Number, required: true },
  closeTrendPoints: { type: String, default: "" },
  ma5Points: { type: String, default: "" },
  ma20Points: { type: String, default: "" },
  volumeMa5Points: { type: String, default: "" },
  dateTicks: { type: Array, default: () => [] },
  priceTicks: { type: Array, default: () => [] },
  activeBar: { type: Object, default: null },
  activeCloseMa5: { type: Number, default: null },
  activeCloseMa20: { type: Number, default: null },
  activeVolumeMa5: { type: Number, default: null },
  tooltip: { type: Object, default: null },
  showCandles: { type: Boolean, default: true },
  showVolume: { type: Boolean, default: true },
  showCloseTrend: { type: Boolean, default: true },
  showMa5: { type: Boolean, default: true },
  showMa20: { type: Boolean, default: true },
  showVolumeMa5: { type: Boolean, default: true },
});

const emit = defineEmits(["mousemove", "mouseleave", "click", "touchmove", "touchend"]);

function fmtPrice(value) {
  return Number.isFinite(value) ? value.toFixed(2) : "-";
}

function fmtVolume(value) {
  if (!Number.isFinite(value)) {
    return "-";
  }
  return new Intl.NumberFormat("zh-TW").format(value);
}
</script>

<template>
  <svg
    :viewBox="`0 0 ${width} ${height}`"
    class="kline-svg"
    role="img"
    aria-label="K 線圖"
    @mousemove="emit('mousemove', $event)"
    @mouseleave="emit('mouseleave')"
    @click="emit('click', $event)"
    @touchmove.prevent="emit('touchmove', $event)"
    @touchend.prevent="emit('touchend', $event)"
  >
    <g>
      <line
        v-for="tick in priceTicks"
        :key="`price-grid-${tick.value}`"
        :x1="padX"
        :x2="width - padX"
        :y1="tick.y"
        :y2="tick.y"
        class="grid-line"
        stroke-width="1"
      />
      <text
        v-for="tick in priceTicks"
        :key="`price-label-${tick.value}`"
        :x="8"
        :y="tick.y + 4"
        class="tick-text"
        font-size="10.5"
      >
        {{ tick.value }}
      </text>
    </g>

    <line
      :x1="padX"
      :x2="width - padX"
      :y1="priceBottom + volumeGap / 2"
      :y2="priceBottom + volumeGap / 2"
      class="divider-line"
      stroke-width="1"
    />

    <polyline
      v-if="showCloseTrend && closeTrendPoints"
      :points="closeTrendPoints"
      fill="none"
      class="close-trend-line"
      stroke-width="1.8"
      stroke-linecap="round"
    />

    <polyline
      v-if="showMa5 && ma5Points"
      :points="ma5Points"
      fill="none"
      class="ma5-line"
      stroke-width="1.8"
      stroke-linecap="round"
    />
    <polyline
      v-if="showMa20 && ma20Points"
      :points="ma20Points"
      fill="none"
      class="ma20-line"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-dasharray="5 4"
    />

    <template v-if="showCandles">
      <line
        v-for="(bar, idx) in bars"
        :key="`${bar.date}-w-${idx}`"
        :x1="bar.x"
        :x2="bar.x"
        :y1="bar.yHigh"
        :y2="bar.yLow"
        :class="bar.isUp ? 'wick-up' : 'wick-down'"
        stroke-width="1.6"
      />
      <rect
        v-for="(bar, idx) in bars"
        :key="`${bar.date}-b-${idx}`"
        :x="bar.x - candleWidth / 2"
        :y="bar.bodyTop"
        :width="candleWidth"
        :height="bar.bodyHeight"
        :class="bar.isUp ? 'body-up' : 'body-down'"
        stroke-width="0.8"
        rx="1.2"
      />
    </template>

    <template v-if="showVolume">
      <rect
        v-for="(bar, idx) in bars"
        :key="`${bar.date}-v-${idx}`"
        :x="bar.x - candleWidth / 2"
        :y="bar.volumeY"
        :width="candleWidth"
        :height="bar.volumeHeight"
        :class="bar.isUp ? 'vol-up' : 'vol-down'"
      />

      <polyline
        v-if="showVolumeMa5 && volumeMa5Points"
        :points="volumeMa5Points"
        fill="none"
        class="vma5-line"
        stroke-width="1.6"
        stroke-linecap="round"
      />
    </template>

    <text
      v-for="tick in dateTicks"
      :key="`date-tick-${tick.label}-${tick.x}`"
      :x="tick.x"
      :y="height - 6"
      text-anchor="middle"
      class="tick-text"
      font-size="10.5"
    >
      {{ tick.label }}
    </text>

    <line
      v-if="activeBar"
      :x1="activeBar.x"
      :x2="activeBar.x"
      :y1="priceTop"
      :y2="volumeBottom"
      class="crosshair"
      stroke-width="1"
      stroke-dasharray="3 3"
    />

    <g v-if="activeBar && tooltip">
      <rect
        :x="tooltip.x"
        :y="tooltip.y"
        :width="tooltipWidth"
        :height="tooltipHeight"
        class="tooltip-bg"
        rx="8"
      />
      <text :x="tooltip.x + 10" :y="tooltip.y + 18" class="tooltip-title" font-size="11.5">{{ activeBar.date }}</text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 34" class="tooltip-sub" font-size="11">
        O {{ fmtPrice(activeBar.open) }} / H {{ fmtPrice(activeBar.high) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 50" class="tooltip-sub" font-size="11">
        L {{ fmtPrice(activeBar.low) }} / C {{ fmtPrice(activeBar.close) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 66" class="tooltip-dim" font-size="11">
        Vol {{ fmtVolume(activeBar.volume) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 82" class="tooltip-dim" font-size="11">
        MA5 {{ fmtPrice(activeCloseMa5) }} / MA20 {{ fmtPrice(activeCloseMa20) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 98" class="tooltip-dim" font-size="11">
        V-MA5 {{ fmtVolume(activeVolumeMa5) }}
      </text>
    </g>
  </svg>
</template>

<style scoped>
.kline-svg {
  width: 100%;
  height: auto;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--chart-bg);
  cursor: crosshair;
}

.grid-line {
  stroke: var(--chart-grid);
}

.tick-text {
  fill: var(--chart-tick);
}

.divider-line {
  stroke: var(--chart-divider);
}

.close-trend-line {
  stroke: var(--trend-line-color);
}

.ma5-line {
  stroke: var(--ma5-color);
}

.ma20-line {
  stroke: var(--ma20-color);
}

.vma5-line {
  stroke: var(--vma5-color);
}

.wick-up {
  stroke: var(--up-color);
}

.wick-down {
  stroke: var(--down-color);
}

.body-up {
  fill: var(--up-fill);
  stroke: var(--up-color);
}

.body-down {
  fill: var(--down-fill);
  stroke: var(--down-color);
}

.vol-up {
  fill: var(--up-vol);
}

.vol-down {
  fill: var(--down-vol);
}

.crosshair {
  stroke: var(--crosshair);
}

.tooltip-bg {
  fill: var(--tooltip-bg);
}

.tooltip-title {
  fill: var(--tooltip-text);
}

.tooltip-sub {
  fill: var(--tooltip-sub);
}

.tooltip-dim {
  fill: var(--tooltip-dim);
}
</style>

