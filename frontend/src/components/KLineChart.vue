<script setup>
import { reactive } from "vue";

import KlineLegend from "./kline/KlineLegend.vue";
import KlineMeta from "./kline/KlineMeta.vue";
import KlineSvgLayer from "./kline/KlineSvgLayer.vue";
import { useKlineSeries } from "../composables/useKlineSeries";

const props = defineProps({
  ohlc: {
    type: Array,
    default: () => [],
  },
});

const {
  width,
  height,
  padX,
  priceTop,
  volumeBottom,
  priceBottom,
  volumeGap,
  tooltipWidth,
  tooltipHeight,
  candles,
  candleWidth,
  bars,
  first,
  last,
  closeTrendPoints,
  ma5Points,
  ma20Points,
  volumeMa5Points,
  dateTicks,
  priceTicks,
  activeBar,
  activeCloseMa5,
  activeCloseMa20,
  activeVolumeMa5,
  tooltip,
  onMouseMove,
  onMouseLeave,
  onClick,
  pctChange,
} = useKlineSeries(() => props.ohlc);

const layerVisible = reactive({
  candles: true,
  closeTrend: true,
  ma5: true,
  ma20: true,
  volume: true,
  volumeMa5: true,
});

const layerOptions = [
  { key: "candles", label: "K 線" },
  { key: "closeTrend", label: "收盤走勢" },
  { key: "ma5", label: "MA5" },
  { key: "ma20", label: "MA20" },
  { key: "volume", label: "成交量" },
  { key: "volumeMa5", label: "量 MA5" },
];

function toggleLayer(key) {
  layerVisible[key] = !layerVisible[key];
}
</script>

<template>
  <div v-if="candles.length < 2" class="chart-empty">資料不足，暫時無法繪製 K 線圖。</div>
  <div v-else class="kline-wrap">
    <div class="display-toggle">
      <span class="display-label">顯示項目</span>
      <button
        v-for="item in layerOptions"
        :key="item.key"
        type="button"
        class="display-chip"
        :class="{ active: layerVisible[item.key] }"
        @click="toggleLayer(item.key)"
      >
        {{ item.label }}
      </button>
    </div>

    <KlineSvgLayer
      :width="width"
      :height="height"
      :pad-x="padX"
      :price-top="priceTop"
      :volume-bottom="volumeBottom"
      :price-bottom="priceBottom"
      :volume-gap="volumeGap"
      :tooltip-width="tooltipWidth"
      :tooltip-height="tooltipHeight"
      :bars="bars"
      :candle-width="candleWidth"
      :close-trend-points="closeTrendPoints"
      :ma5-points="ma5Points"
      :ma20-points="ma20Points"
      :volume-ma5-points="volumeMa5Points"
      :date-ticks="dateTicks"
      :price-ticks="priceTicks"
      :active-bar="activeBar"
      :active-close-ma5="activeCloseMa5"
      :active-close-ma20="activeCloseMa20"
      :active-volume-ma5="activeVolumeMa5"
      :tooltip="tooltip"
      :show-candles="layerVisible.candles"
      :show-close-trend="layerVisible.closeTrend"
      :show-ma5="layerVisible.ma5"
      :show-ma20="layerVisible.ma20"
      :show-volume="layerVisible.volume"
      :show-volume-ma5="layerVisible.volumeMa5"
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @click="onClick"
    />

    <KlineLegend
      :show-close-trend="layerVisible.closeTrend"
      :show-ma5="layerVisible.ma5"
      :show-ma20="layerVisible.ma20"
      :show-volume-ma5="layerVisible.volume && layerVisible.volumeMa5"
    />
    <KlineMeta :first="first" :last="last" :pct-change="pctChange()" />
    <p class="hint-tip">滑鼠移動可看單日 OHLC 與量能，點一下可鎖定 tooltip，再點一次取消。</p>
  </div>
</template>

<style scoped>
.kline-wrap {
  margin-top: 8px;
}

.display-toggle {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
}

.display-label {
  color: var(--muted);
  font-size: 0.82rem;
  font-weight: 700;
}

.display-chip {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-card);
  color: var(--muted);
  padding: 4px 10px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
}

.display-chip.active {
  border-color: var(--brand);
  color: var(--brand);
}

.hint-tip {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 0.82rem;
}

.chart-empty {
  margin-top: 8px;
  color: var(--warn);
}
</style>

