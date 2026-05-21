<script setup>
// คอมโพเนนต์หลักของแอป — รวม router-view และ bottom navigation
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

// แสดง bottom nav เฉพาะหน้าที่ต้องการ
const showBottomNav = computed(() => {
  const pagesWithNav = ['Dashboard', 'FoodCapture', 'ActivityLog', 'WeeklyGoals']
  return pagesWithNav.includes(route.name)
})

// รายการเมนู bottom navigation
const navItems = [
  { name: 'Dashboard', icon: '🏠', label: 'หน้าหลัก' },
  { name: 'FoodCapture', icon: '📸', label: 'ถ่ายอาหาร' },
  { name: 'ActivityLog', icon: '🏃', label: 'กิจกรรม' },
  { name: 'WeeklyGoals', icon: '🎯', label: 'เป้าหมาย' }
]

const navigateTo = (name) => {
  router.push({ name })
}
</script>

<template>
  <div class="app-container">
    <!-- พื้นที่แสดงหน้าต่างๆ พร้อม transition -->
    <router-view v-slot="{ Component, route: viewRoute }">
      <transition :name="viewRoute.meta.transition || 'fade'" mode="out-in">
        <component :is="Component" :key="viewRoute.path" />
      </transition>
    </router-view>

    <!-- Bottom Navigation Bar แบบ iOS -->
    <nav v-if="showBottomNav" class="bottom-nav">
      <div class="nav-inner">
        <button
          v-for="item in navItems"
          :key="item.name"
          class="nav-item"
          :class="{ active: route.name === item.name }"
          @click="navigateTo(item.name)"
        >
          <span class="nav-icon">{{ item.icon }}</span>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="route.name === item.name" class="nav-indicator"></span>
        </button>
      </div>
    </nav>
  </div>
</template>

<style>
/* ==================== Global Styles ==================== */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --primary-start: #667eea;
  --primary-end: #764ba2;
  --accent-start: #f093fb;
  --accent-end: #f5576c;
  --bg-dark: #0f0f23;
  --bg-card: rgba(255, 255, 255, 0.05);
  --bg-card-hover: rgba(255, 255, 255, 0.1);
  --text-primary: #ffffff;
  --text-secondary: rgba(255, 255, 255, 0.7);
  --text-muted: rgba(255, 255, 255, 0.4);
  --glass-bg: rgba(255, 255, 255, 0.08);
  --glass-border: rgba(255, 255, 255, 0.12);
  --grade-good: #00e676;
  --grade-medium: #ffab40;
  --grade-bad: #ff5252;
  --radius-sm: 12px;
  --radius-md: 16px;
  --radius-lg: 24px;
  --radius-xl: 32px;
  --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.4);
  --nav-height: 80px;
}

html, body {
  font-family: 'Prompt', sans-serif;
  background: var(--bg-dark);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

#app {
  min-height: 100vh;
}

/* ==================== Page Transitions ==================== */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.slide-left-enter-active,
.slide-left-leave-active {
  transition: all 0.35s ease;
}
.slide-left-enter-from {
  opacity: 0;
  transform: translateX(30px);
}
.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* ==================== Glassmorphism Card ==================== */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-md);
}

/* ==================== Gradient Buttons ==================== */
.btn-primary {
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 14px 28px;
  font-family: 'Prompt', sans-serif;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
  width: 100%;
  touch-action: manipulation;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
}

.btn-primary:active {
  transform: translateY(0);
}

.btn-accent {
  background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
  color: white;
  border: none;
  border-radius: var(--radius-sm);
  padding: 14px 28px;
  font-family: 'Prompt', sans-serif;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.4);
  width: 100%;
  touch-action: manipulation;
}

.btn-accent:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 87, 108, 0.6);
}

/* ==================== Form Inputs ==================== */
.form-input {
  width: 100%;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: 'Prompt', sans-serif;
  font-size: 15px;
  transition: all 0.3s ease;
  outline: none;
  touch-action: manipulation;
}

.form-input:focus {
  border-color: var(--primary-start);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.form-input::placeholder {
  color: var(--text-muted);
}

.form-select {
  width: 100%;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: 'Prompt', sans-serif;
  font-size: 15px;
  transition: all 0.3s ease;
  outline: none;
  appearance: none;
  cursor: pointer;
}

.form-select:focus {
  border-color: var(--primary-start);
  background: rgba(255, 255, 255, 0.1);
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.form-group {
  margin-bottom: 16px;
}

/* ==================== Scrollbar ==================== */
::-webkit-scrollbar {
  width: 4px;
}
::-webkit-scrollbar-track {
  background: transparent;
}
::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

/* ==================== Utility ==================== */
.page-container {
  min-height: 100vh;
  padding: 20px;
  padding-bottom: calc(var(--nav-height) + 20px);
  max-width: 480px;
  margin: 0 auto;
}

.loading-spinner {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s ease infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scaleIn {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@keyframes shimmer {
  0% { background-position: -200% center; }
  100% { background-position: 200% center; }
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
</style>

<style scoped>
/* ==================== App Container ==================== */
.app-container {
  position: relative;
  min-height: 100vh;
}

/* ==================== Bottom Navigation ==================== */
.bottom-nav {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: var(--nav-height);
  background: rgba(15, 15, 35, 0.92);
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  z-index: 1000;
  padding-bottom: env(safe-area-inset-bottom, 0);
}

.nav-inner {
  display: flex;
  justify-content: space-around;
  align-items: center;
  height: 100%;
  max-width: 480px;
  margin: 0 auto;
  padding: 0 8px;
}

.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
  transition: all 0.3s ease;
  position: relative;
  font-family: 'Prompt', sans-serif;
  touch-action: manipulation;
  min-width: 70px;
}

.nav-item.active {
  color: var(--text-primary);
}

.nav-icon {
  font-size: 22px;
  transition: transform 0.3s ease;
}

.nav-item.active .nav-icon {
  transform: scale(1.15);
}

.nav-label {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.nav-indicator {
  position: absolute;
  top: 2px;
  width: 24px;
  height: 3px;
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  border-radius: 2px;
  animation: scaleIn 0.3s ease;
}
</style>
