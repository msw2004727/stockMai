<script setup>
defineProps({
  health: {
    type: Object,
    default: null,
  },
  healthLoading: {
    type: Boolean,
    default: false,
  },
  healthError: {
    type: String,
    default: "",
  },
  healthCheckedAt: {
    type: String,
    default: "",
  },
});

const emit = defineEmits(["refresh"]);
</script>

<template>
  <div class="actions">
    <button type="button" class="btn" :disabled="healthLoading" @click="emit('refresh')">
      {{ healthLoading ? "檢查中..." : "重新檢查健康度" }}
    </button>
    <span v-if="healthCheckedAt" class="checked-at">最後檢查：{{ healthCheckedAt }}</span>
  </div>

  <div v-if="healthError" class="card error">{{ healthError }}</div>

  <div v-else-if="health" class="grid">
    <article class="card">
      <p class="label">整體狀態</p>
      <p class="value" :class="health.status === 'ok' ? 'ok' : 'warn'">{{ health.status }}</p>
    </article>

    <article class="card">
      <p class="label">PostgreSQL</p>
      <p class="value" :class="health.services.postgres.ok ? 'ok' : 'warn'">
        {{ health.services.postgres.ok ? "連線正常" : "連線失敗" }}
      </p>
      <p class="sub">Latency: {{ health.services.postgres.latency_ms }} ms</p>
    </article>

    <article class="card">
      <p class="label">Redis</p>
      <p class="value" :class="health.services.redis.ok ? 'ok' : 'warn'">
        {{ health.services.redis.ok ? "連線正常" : "連線失敗" }}
      </p>
      <p class="sub">Latency: {{ health.services.redis.latency_ms }} ms</p>
    </article>
  </div>
</template>
