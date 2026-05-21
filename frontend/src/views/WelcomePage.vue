<script setup>
// หน้าต้อนรับ — แสดง Logo, ชื่อแอป, และปุ่มเริ่มต้นใช้งาน
import { useRouter } from 'vue-router'

const router = useRouter()

const startApp = () => {
  router.push('/setup')
}
</script>

<template>
  <div class="welcome-page">
    <!-- พื้นหลัง animated gradient -->
    <div class="bg-gradient"></div>
    <div class="bg-orbs">
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
    </div>

    <!-- เนื้อหาหลัก -->
    <div class="welcome-content">
      <!-- Logo -->
      <div class="logo-container">
        <div class="logo-circle">
          <div class="logo-inner">
            <span class="logo-emoji">🌟</span>
          </div>
        </div>
        <div class="logo-ring"></div>
      </div>

      <!-- ชื่อแอป -->
      <h1 class="app-title">
        <span class="title-gradient">Self-Dev</span>
      </h1>
      <p class="app-subtitle">ดูแลสุขภาพอัจฉริยะด้วย AI</p>

      <!-- ฟีเจอร์หลัก -->
      <div class="features">
        <div class="feature-item" style="animation-delay: 0.2s">
          <span class="feature-icon">📸</span>
          <span class="feature-text">ถ่ายรูปอาหาร วิเคราะห์แคลอรี่ด้วย AI</span>
        </div>
        <div class="feature-item" style="animation-delay: 0.4s">
          <span class="feature-icon">🏃</span>
          <span class="feature-text">บันทึกกิจกรรม ติดตามการเผาผลาญ</span>
        </div>
        <div class="feature-item" style="animation-delay: 0.6s">
          <span class="feature-icon">🎯</span>
          <span class="feature-text">ตั้งเป้าหมาย พัฒนาสุขภาพทุกสัปดาห์</span>
        </div>
      </div>

      <!-- ปุ่มเริ่มต้น -->
      <button class="start-button" @click="startApp">
        <span class="btn-text">เริ่มต้นใช้งาน</span>
        <span class="btn-arrow">→</span>
      </button>

      <p class="footer-text">ฟรี • ไม่มีโฆษณา • ปลอดภัย</p>
    </div>
  </div>
</template>

<style scoped>
.welcome-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  padding: 20px;
}

/* ==================== พื้นหลัง Gradient + Orbs ==================== */
.bg-gradient {
  position: fixed;
  inset: 0;
  background: linear-gradient(135deg, #0f0f23 0%, #1a1a3e 30%, #2d1b69 60%, #0f0f23 100%);
  background-size: 300% 300%;
  animation: gradientShift 12s ease infinite;
  z-index: -2;
}

.bg-orbs {
  position: fixed;
  inset: 0;
  z-index: -1;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.3;
}

.orb-1 {
  width: 300px;
  height: 300px;
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  top: -100px;
  right: -80px;
  animation: float 8s ease-in-out infinite;
}

.orb-2 {
  width: 250px;
  height: 250px;
  background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
  bottom: -80px;
  left: -60px;
  animation: float 10s ease-in-out infinite reverse;
}

.orb-3 {
  width: 180px;
  height: 180px;
  background: linear-gradient(135deg, #43e97b, #38f9d7);
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: float 12s ease-in-out infinite;
  opacity: 0.15;
}

/* ==================== เนื้อหา ==================== */
.welcome-content {
  text-align: center;
  max-width: 380px;
  width: 100%;
  animation: fadeIn 1s ease;
}

/* ==================== Logo ==================== */
.logo-container {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 32px;
}

.logo-circle {
  width: 120px;
  height: 120px;
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 40px rgba(102, 126, 234, 0.5);
  animation: float 4s ease-in-out infinite;
}

.logo-inner {
  width: 100px;
  height: 100px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-emoji {
  font-size: 48px;
  filter: drop-shadow(0 2px 8px rgba(0,0,0,0.3));
}

.logo-ring {
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 2px solid rgba(102, 126, 234, 0.3);
  animation: spin 10s linear infinite;
}

/* ==================== ข้อความ ==================== */
.app-title {
  font-size: 42px;
  font-weight: 800;
  margin-bottom: 8px;
  letter-spacing: -1px;
}

.title-gradient {
  background: linear-gradient(135deg, #fff 0%, #c7d2fe 50%, var(--accent-start) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-subtitle {
  font-size: 17px;
  color: var(--text-secondary);
  margin-bottom: 40px;
  font-weight: 300;
}

/* ==================== ฟีเจอร์ ==================== */
.features {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 40px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 14px;
  background: var(--glass-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm);
  padding: 14px 18px;
  animation: slideUp 0.6s ease backwards;
  text-align: left;
}

.feature-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.feature-text {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 400;
  line-height: 1.4;
}

/* ==================== ปุ่มเริ่มต้น ==================== */
.start-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  padding: 18px 32px;
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end), var(--accent-start));
  background-size: 200% 200%;
  animation: gradientShift 4s ease infinite;
  border: none;
  border-radius: var(--radius-md);
  color: white;
  font-family: 'Prompt', sans-serif;
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 6px 30px rgba(102, 126, 234, 0.5);
  touch-action: manipulation;
  margin-bottom: 20px;
}

.start-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 40px rgba(102, 126, 234, 0.7);
}

.start-button:active {
  transform: translateY(0);
}

.btn-arrow {
  font-size: 22px;
  transition: transform 0.3s ease;
}

.start-button:hover .btn-arrow {
  transform: translateX(4px);
}

.footer-text {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}
</style>
