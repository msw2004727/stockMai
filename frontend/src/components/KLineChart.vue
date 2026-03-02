<script setup>
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
</script>

<template>
  <div v-if="candles.length < 2" class="chart-empty">資料不足，暫時無法繪製 K 線圖。</div>
  <div v-else class="kline-wrap">
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
      @mousemove="onMouseMove"
      @mouseleave="onMouseLeave"
      @click="onClick"
    />

    <KlineLegend />
    <KlineMeta :first="first" :last="last" :pct-change="pctChange()" />
    <p class="hint-tip">
      滑鼠移動可查看資料，點擊可鎖定 tooltip，再點一次解除。
    </p>
  </div>
</template>

<style scoped>
.kline-wrap {
  margin-top: 8px;
}

.hint-tip {
  margin: 7px 0 0;
  color: #64748b;
  font-size: 0.82rem;
}

.chart-empty {
  margin-top: 8px;
  color: #7c2d12;
}
</style>
