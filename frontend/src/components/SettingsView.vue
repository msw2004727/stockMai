<script setup>
import HealthPanel from "./HealthPanel.vue";
import { useTheme } from "../composables/useTheme";

const { theme, toggleTheme } = useTheme();

defineProps({
  health: { type: Object, default: null },
  healthLoading: { type: Boolean, default: false },
  healthError: { type: String, default: "" },
  healthCheckedAt: { type: String, default: "" },
});

const emit = defineEmits(["refresh-health"]);
</script>

<template>
  <div class="view-container">
    <!-- System Status -->
    <div class="panel">
      <h2 class="section-title">系統狀態</h2>
      <HealthPanel
        :health="health"
        :health-loading="healthLoading"
        :health-error="healthError"
        :health-checked-at="healthCheckedAt"
        @refresh="emit('refresh-health')"
      />
    </div>

    <!-- Theme Toggle -->
    <div class="panel">
      <h2 class="section-title">外觀設定</h2>
      <div class="settings-row">
        <div class="settings-row-label">
          <span>深色模式</span>
          <span class="settings-row-desc">深色背景，適合夜間使用</span>
        </div>
        <button
          type="button"
          class="toggle-switch"
          :class="{ active: theme === 'dark' }"
          role="switch"
          :aria-checked="theme === 'dark'"
          :aria-label="theme === 'dark' ? '深色模式已開啟' : '深色模式已關閉'"
          @click="toggleTheme"
        >
          <span class="toggle-knob"></span>
        </button>
      </div>
    </div>

    <!-- Account (placeholder) -->
    <div class="panel">
      <h2 class="section-title">帳號</h2>
      <button type="button" class="google-btn" disabled>
        <svg width="18" height="18" viewBox="0 0 24 24">
          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
          <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
          <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
        </svg>
        Google 登入
      </button>
      <p class="coming-soon">即將推出</p>
    </div>

    <!-- Version -->
    <p class="version-info">stockMai v0.1.0 MVP</p>
  </div>
</template>
