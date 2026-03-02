import { computed, ref } from "vue";

const width = 740;
const height = 300;
const padX = 22;
const padY = 24;
const volumeGap = 14;
const volumeHeight = 72;
const priceTop = padY;
const volumeBottom = height - padY;
const volumeTop = volumeBottom - volumeHeight;
const priceBottom = volumeTop - volumeGap;
const tooltipWidth = 184;
const tooltipHeight = 112;
const tooltipPad = 8;

function movingAverage(values, windowSize) {
  const result = new Array(values.length).fill(null);
  if (windowSize <= 0) {
    return result;
  }

  let sum = 0;
  for (let i = 0; i < values.length; i += 1) {
    sum += values[i];
    if (i >= windowSize) {
      sum -= values[i - windowSize];
    }
    if (i >= windowSize - 1) {
      result[i] = sum / windowSize;
    }
  }
  return result;
}

function clamp(n, min, max) {
  return Math.min(max, Math.max(min, n));
}

function shortDate(value) {
  if (!value || typeof value !== "string") {
    return "-";
  }
  const parts = value.split("-");
  if (parts.length !== 3) {
    return value;
  }
  return `${parts[1]}/${parts[2]}`;
}

function toCandleRows(rawOhlcRows) {
  return rawOhlcRows
    .map((row) => {
      if (!Array.isArray(row) || row.length < 6) {
        return null;
      }
      const [date, open, high, low, close, volume] = row;
      return {
        date,
        open: Number(open),
        high: Number(high),
        low: Number(low),
        close: Number(close),
        volume: Number(volume),
      };
    })
    .filter(Boolean);
}

export function useKlineSeries(rawOhlcSource) {
  const candles = computed(() => {
    const raw = typeof rawOhlcSource === "function" ? rawOhlcSource() : rawOhlcSource?.value;
    return toCandleRows(raw || []);
  });

  const domain = computed(() => {
    if (candles.value.length === 0) {
      return { min: 0, max: 1 };
    }
    const lows = candles.value.map((c) => c.low);
    const highs = candles.value.map((c) => c.high);
    let min = Math.min(...lows);
    let max = Math.max(...highs);
    if (min === max) {
      min -= 1;
      max += 1;
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
    const usable = priceBottom - priceTop;
    const ratio = (price - domain.value.min) / (domain.value.max - domain.value.min);
    return priceBottom - ratio * usable;
  }

  const volumeMax = computed(() => {
    if (candles.value.length === 0) {
      return 1;
    }
    return Math.max(...candles.value.map((c) => c.volume), 1);
  });

  function toVolumeY(volume) {
    const ratio = volume / volumeMax.value;
    return volumeBottom - ratio * volumeHeight;
  }

  function toPolyline(values, yMapper) {
    return values
      .map((value, index) => {
        if (value == null) {
          return null;
        }
        return `${toX(index, candles.value.length)},${yMapper(value)}`;
      })
      .filter(Boolean)
      .join(" ");
  }

  const candleWidth = computed(() => {
    const n = candles.value.length;
    if (n <= 1) {
      return 10;
    }
    const spacing = (width - padX * 2) / (n - 1);
    return Math.max(4, Math.min(14, spacing * 0.58));
  });

  const bars = computed(() =>
    candles.value.map((candle, index) => {
      const x = toX(index, candles.value.length);
      const yHigh = toY(candle.high);
      const yLow = toY(candle.low);
      const yOpen = toY(candle.open);
      const yClose = toY(candle.close);
      const bodyTop = Math.min(yOpen, yClose);
      const bodyHeight = Math.max(1.2, Math.abs(yOpen - yClose));
      const isUp = candle.close >= candle.open;
      const volumeY = toVolumeY(candle.volume);

      return {
        ...candle,
        x,
        yHigh,
        yLow,
        bodyTop,
        bodyHeight,
        isUp,
        volumeY,
        volumeHeight: Math.max(1.2, volumeBottom - volumeY),
      };
    }),
  );

  const closeValues = computed(() => candles.value.map((c) => c.close));
  const volumeValues = computed(() => candles.value.map((c) => c.volume));

  const closeMa5 = computed(() => movingAverage(closeValues.value, 5));
  const closeMa20 = computed(() => movingAverage(closeValues.value, 20));
  const volumeMa5 = computed(() => movingAverage(volumeValues.value, 5));

  const ma5Points = computed(() => toPolyline(closeMa5.value, toY));
  const ma20Points = computed(() => toPolyline(closeMa20.value, toY));
  const volumeMa5Points = computed(() => toPolyline(volumeMa5.value, toVolumeY));

  const first = computed(() => candles.value[0] || null);
  const last = computed(() => candles.value[candles.value.length - 1] || null);

  function pctChange() {
    if (!first.value || !last.value || first.value.close === 0) {
      return null;
    }
    const delta = ((last.value.close - first.value.close) / first.value.close) * 100;
    return delta.toFixed(2);
  }

  const hoveredIndex = ref(-1);
  const lockedIndex = ref(-1);

  function getNearestIndex(event) {
    const element = event.currentTarget;
    if (!element || candles.value.length === 0) {
      return -1;
    }
    const rect = element.getBoundingClientRect();
    const xPx = event.clientX - rect.left;
    const x = (xPx / rect.width) * width;
    const n = candles.value.length;
    const usable = width - padX * 2;
    const ratio = usable === 0 ? 0 : (x - padX) / usable;
    return clamp(Math.round(ratio * (n - 1)), 0, n - 1);
  }

  function onMouseMove(event) {
    if (lockedIndex.value >= 0) {
      return;
    }
    hoveredIndex.value = getNearestIndex(event);
  }

  function onMouseLeave() {
    if (lockedIndex.value >= 0) {
      return;
    }
    hoveredIndex.value = -1;
  }

  function onClick(event) {
    const idx = getNearestIndex(event);
    if (idx < 0) {
      return;
    }
    if (lockedIndex.value === idx) {
      lockedIndex.value = -1;
      return;
    }
    lockedIndex.value = idx;
  }

  const activeIndex = computed(() => (lockedIndex.value >= 0 ? lockedIndex.value : hoveredIndex.value));

  const activeBar = computed(() => {
    if (activeIndex.value < 0 || activeIndex.value >= bars.value.length) {
      return null;
    }
    return bars.value[activeIndex.value];
  });

  const activeCloseMa5 = computed(() => {
    if (activeIndex.value < 0 || activeIndex.value >= closeMa5.value.length) {
      return null;
    }
    return closeMa5.value[activeIndex.value];
  });

  const activeCloseMa20 = computed(() => {
    if (activeIndex.value < 0 || activeIndex.value >= closeMa20.value.length) {
      return null;
    }
    return closeMa20.value[activeIndex.value];
  });

  const activeVolumeMa5 = computed(() => {
    if (activeIndex.value < 0 || activeIndex.value >= volumeMa5.value.length) {
      return null;
    }
    return volumeMa5.value[activeIndex.value];
  });

  const tooltip = computed(() => {
    if (!activeBar.value) {
      return null;
    }
    const bar = activeBar.value;
    const x = clamp(bar.x + 10, tooltipPad, width - tooltipWidth - tooltipPad);
    const y = clamp(bar.bodyTop - tooltipHeight - 8, tooltipPad, priceBottom - tooltipHeight - tooltipPad);
    return { x, y };
  });

  const dateTicks = computed(() => {
    if (bars.value.length === 0) {
      return [];
    }
    const lastIdx = bars.value.length - 1;
    const midIdx = Math.floor(lastIdx / 2);
    const indexes = Array.from(new Set([0, midIdx, lastIdx]));
    return indexes.map((idx) => ({
      x: bars.value[idx].x,
      label: shortDate(bars.value[idx].date),
    }));
  });

  const priceTicks = computed(() => {
    const min = domain.value.min;
    const max = domain.value.max;
    const mid = (min + max) / 2;
    return [max, mid, min].map((value) => ({
      value: value.toFixed(2),
      y: toY(value),
    }));
  });

  return {
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
  };
}
