<script setup>
defineProps({
  showCloseTrend: { type: Boolean, default: true },
  showMa5: { type: Boolean, default: true },
  showMa20: { type: Boolean, default: true },
  showVolumeMa5: { type: Boolean, default: true },
});
</script>

<template>
  <div class="legend">
    <span v-if="showCloseTrend"><i class="legend-line trend"></i> 收盤走勢</span>
    <span v-if="showMa5"><i class="legend-line ma5"></i> MA5</span>
    <span v-if="showMa20"><i class="legend-line ma20"></i> MA20</span>
    <span v-if="showVolumeMa5"><i class="legend-line vma5"></i> 量 MA5</span>
  </div>
</template>

<style scoped>
.legend {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: var(--muted);
  font-size: 0.82rem;
  flex-wrap: wrap;
}

.legend span {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.legend-line {
  display: inline-block;
  width: 16px;
  height: 2px;
}

.legend-line.trend {
  background: var(--trend-line-color);
}

.legend-line.ma5 {
  background: var(--ma5-color);
}

.legend-line.ma20 {
  background: repeating-linear-gradient(90deg, var(--ma20-color) 0 8px, transparent 8px 12px);
}

.legend-line.vma5 {
  background: var(--vma5-color);
}
</style>

