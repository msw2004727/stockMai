<script setup>
defineProps({
  first: {
    type: Object,
    default: null,
  },
  last: {
    type: Object,
    default: null,
  },
  pctChange: {
    type: String,
    default: null,
  },
});
</script>

<template>
  <div class="kline-meta">
    <p>區間：<strong>{{ first?.date }}</strong> ~ <strong>{{ last?.date }}</strong></p>
    <p>
      區間漲跌：
      <strong :class="Number(pctChange) >= 0 ? 'up' : 'down'">{{ pctChange }}%</strong>
    </p>
  </div>
</template>

<style scoped>
.kline-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #334155;
  font-size: 0.88rem;
}

.kline-meta p {
  margin: 0;
}

.up {
  color: #0f766e;
}

.down {
  color: #b45309;
}

@media (max-width: 760px) {
  .kline-meta {
    flex-direction: column;
  }
}
</style>
