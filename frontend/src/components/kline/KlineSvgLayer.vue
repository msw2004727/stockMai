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
});

const emit = defineEmits(["mousemove", "mouseleave", "click"]);

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
    aria-label="股票 K 線圖"
    @mousemove="emit('mousemove', $event)"
    @mouseleave="emit('mouseleave')"
    @click="emit('click', $event)"
  >
    <g>
      <line
        v-for="tick in priceTicks"
        :key="`price-grid-${tick.value}`"
        :x1="padX"
        :x2="width - padX"
        :y1="tick.y"
        :y2="tick.y"
        stroke="rgba(15, 23, 42, 0.08)"
        stroke-width="1"
      />
      <text
        v-for="tick in priceTicks"
        :key="`price-label-${tick.value}`"
        :x="8"
        :y="tick.y + 4"
        fill="#64748b"
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
      stroke="rgba(15, 23, 42, 0.18)"
      stroke-width="1"
    />

    <polyline
      v-if="ma5Points"
      :points="ma5Points"
      fill="none"
      stroke="#0369a1"
      stroke-width="1.8"
      stroke-linecap="round"
    />
    <polyline
      v-if="ma20Points"
      :points="ma20Points"
      fill="none"
      stroke="#be185d"
      stroke-width="1.8"
      stroke-linecap="round"
      stroke-dasharray="5 4"
    />

    <line
      v-for="(bar, idx) in bars"
      :key="`${bar.date}-w-${idx}`"
      :x1="bar.x"
      :x2="bar.x"
      :y1="bar.yHigh"
      :y2="bar.yLow"
      :stroke="bar.isUp ? '#0f766e' : '#b45309'"
      stroke-width="1.6"
    />
    <rect
      v-for="(bar, idx) in bars"
      :key="`${bar.date}-b-${idx}`"
      :x="bar.x - candleWidth / 2"
      :y="bar.bodyTop"
      :width="candleWidth"
      :height="bar.bodyHeight"
      :fill="bar.isUp ? 'rgba(15,118,110,0.78)' : 'rgba(180,83,9,0.78)'"
      :stroke="bar.isUp ? '#0f766e' : '#b45309'"
      stroke-width="0.8"
      rx="1.2"
    />

    <rect
      v-for="(bar, idx) in bars"
      :key="`${bar.date}-v-${idx}`"
      :x="bar.x - candleWidth / 2"
      :y="bar.volumeY"
      :width="candleWidth"
      :height="bar.volumeHeight"
      :fill="bar.isUp ? 'rgba(15,118,110,0.35)' : 'rgba(180,83,9,0.35)'"
    />

    <polyline
      v-if="volumeMa5Points"
      :points="volumeMa5Points"
      fill="none"
      stroke="#ea580c"
      stroke-width="1.6"
      stroke-linecap="round"
    />

    <text
      v-for="tick in dateTicks"
      :key="`date-tick-${tick.label}-${tick.x}`"
      :x="tick.x"
      :y="height - 6"
      text-anchor="middle"
      fill="#64748b"
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
      stroke="rgba(11, 79, 108, 0.5)"
      stroke-width="1"
      stroke-dasharray="3 3"
    />

    <g v-if="activeBar && tooltip">
      <rect
        :x="tooltip.x"
        :y="tooltip.y"
        :width="tooltipWidth"
        :height="tooltipHeight"
        fill="rgba(15, 23, 42, 0.88)"
        rx="8"
      />
      <text :x="tooltip.x + 10" :y="tooltip.y + 18" fill="#f8fafc" font-size="11.5">{{ activeBar.date }}</text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 34" fill="#e2e8f0" font-size="11">
        O {{ fmtPrice(activeBar.open) }} / H {{ fmtPrice(activeBar.high) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 50" fill="#e2e8f0" font-size="11">
        L {{ fmtPrice(activeBar.low) }} / C {{ fmtPrice(activeBar.close) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 66" fill="#cbd5e1" font-size="11">
        Vol {{ fmtVolume(activeBar.volume) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 82" fill="#cbd5e1" font-size="11">
        MA5 {{ fmtPrice(activeCloseMa5) }} / MA20 {{ fmtPrice(activeCloseMa20) }}
      </text>
      <text :x="tooltip.x + 10" :y="tooltip.y + 98" fill="#cbd5e1" font-size="11">
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
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: linear-gradient(180deg, rgba(250, 250, 250, 0.96), rgba(240, 248, 255, 0.9));
  cursor: crosshair;
}
</style>
