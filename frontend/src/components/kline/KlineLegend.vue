<template>
  <div class="legend">
    <span><i class="legend-line ma5"></i> MA5</span>
    <span><i class="legend-line ma20"></i> MA20</span>
    <span><i class="legend-line vma5"></i> 成交量 MA5</span>
  </div>
</template>

<style scoped>
.legend {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 14px;
  color: #475569;
  font-size: 0.82rem;
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

.legend-line.ma5 {
  background: #0369a1;
}

.legend-line.ma20 {
  background: repeating-linear-gradient(90deg, #be185d 0 8px, transparent 8px 12px);
}

.legend-line.vma5 {
  background: #ea580c;
}

@media (max-width: 760px) {
  .legend {
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style>
