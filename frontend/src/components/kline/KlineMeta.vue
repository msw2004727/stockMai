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
      <strong :class="Number(pctChange) >= 0 ? 'rise' : 'fall'">{{ pctChange }}%</strong>
    </p>
  </div>
</template>

<style scoped>
.kline-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: var(--muted);
  font-size: 0.88rem;
}

.kline-meta p {
  margin: 0;
}

@media (max-width: 767px) {
  .kline-meta {
    flex-direction: column;
  }
}
</style>

