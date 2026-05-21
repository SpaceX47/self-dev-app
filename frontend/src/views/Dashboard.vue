<script setup>
// หน้า Dashboard — แสดงสรุปข้อมูลสุขภาพรายวัน
import { ref, computed, onMounted } from 'vue'
import { getUserBMR, getDailySummary, getMeals } from '../services/api'

const userId = localStorage.getItem('user_id')
const userName = localStorage.getItem('user_name') || 'คุณ'
const isLoading = ref(true)

// ข้อมูล BMR/TDEE
const bmrData = ref({
  bmr: 0,
  tdee: 0,
  daily_budget: 0
})

// สรุปแคลอรี่รายวัน
const dailySummary = ref({
  total_calories: 0,
  total_protein: 0,
  total_carbs: 0,
  total_fat: 0,
  meal_count: 0
})

// รายการมื้ออาหารวันนี้
const todayMeals = ref([])

// วันที่วันนี้ (format: YYYY-MM-DD)
const today = new Date().toISOString().split('T')[0]

// คำนวณเปอร์เซ็นต์แคลอรี่ที่ทานไป
const caloriePercentage = computed(() => {
  if (!bmrData.value.daily_budget) return 0
  const pct = (dailySummary.value.total_calories / bmrData.value.daily_budget) * 100
  return Math.min(pct, 100)
})

// แคลอรี่ที่เหลือ
const caloriesRemaining = computed(() => {
  const remaining = bmrData.value.daily_budget - dailySummary.value.total_calories
  return Math.max(0, Math.round(remaining))
})

// สีของ circular progress ตามเปอร์เซ็นต์
const progressColor = computed(() => {
  if (caloriePercentage.value > 90) return '#ff5252'
  if (caloriePercentage.value > 70) return '#ffab40'
  return '#00e676'
})

// คำนวณ stroke-dasharray สำหรับ SVG circle
const circumference = 2 * Math.PI * 70
const progressOffset = computed(() => {
  return circumference - (caloriePercentage.value / 100) * circumference
})

// แปลชื่อมื้ออาหาร
const mealTypeLabels = {
  breakfast: 'มื้อเช้า',
  lunch: 'มื้อกลางวัน',
  dinner: 'มื้อเย็น',
  snack: 'ของว่าง'
}

const mealTypeIcons = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍪'
}

// แมปสีตามเกรด
const gradeConfig = {
  Good: { color: 'var(--grade-good)', bg: 'rgba(0, 230, 118, 0.12)', label: 'ดีมาก' },
  Medium: { color: 'var(--grade-medium)', bg: 'rgba(255, 171, 64, 0.12)', label: 'ปานกลาง' },
  Bad: { color: 'var(--grade-bad)', bg: 'rgba(255, 82, 82, 0.12)', label: 'ควรปรับปรุง' }
}

const getGrade = (grade) => gradeConfig[grade] || gradeConfig['Medium']

// คำทักทายตามเวลา
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'สวัสดีตอนเช้า'
  if (hour < 17) return 'สวัสดีตอนบ่าย'
  return 'สวัสดีตอนเย็น'
})

// โหลดข้อมูล
onMounted(async () => {
  try {
    const [bmrRes, summaryRes, mealsRes] = await Promise.allSettled([
      getUserBMR(userId),
      getDailySummary(userId, today),
      getMeals(userId, today)
    ])

    if (bmrRes.status === 'fulfilled') {
      bmrData.value = bmrRes.value.data
    }

    if (summaryRes.status === 'fulfilled') {
      dailySummary.value = summaryRes.value.data
    }

    if (mealsRes.status === 'fulfilled') {
      todayMeals.value = mealsRes.value.data || []
    }
  } catch (error) {
    console.error('โหลดข้อมูล Dashboard ล้มเหลว:', error)
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div class="dashboard-page">
    <div class="page-container">
      <!-- หัวข้อ + ทักทาย -->
      <div class="header-section">
        <div class="greeting">
          <p class="greeting-text">{{ greeting }} 👋</p>
          <h1 class="user-name">{{ userName }}</h1>
        </div>
        <div class="date-badge">
          <span class="date-text">{{ new Date().toLocaleDateString('th-TH', { day: 'numeric', month: 'short' }) }}</span>
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="isLoading" class="loading-state">
        <div class="loading-spinner" style="width: 40px; height: 40px; border-width: 3px;"></div>
        <p style="margin-top: 16px; color: var(--text-muted);">กำลังโหลดข้อมูล...</p>
      </div>

      <template v-else>
        <!-- Circular Progress - แคลอรี่วันนี้ -->
        <div class="calorie-section glass-card">
          <div class="calorie-ring">
            <svg width="160" height="160" viewBox="0 0 160 160">
              <!-- วงพื้นหลัง -->
              <circle
                cx="80" cy="80" r="70"
                fill="none"
                stroke="rgba(255,255,255,0.06)"
                stroke-width="10"
              />
              <!-- วง progress -->
              <circle
                cx="80" cy="80" r="70"
                fill="none"
                :stroke="progressColor"
                stroke-width="10"
                stroke-linecap="round"
                :stroke-dasharray="circumference"
                :stroke-dashoffset="progressOffset"
                transform="rotate(-90 80 80)"
                class="progress-ring"
              />
            </svg>
            <div class="calorie-center">
              <span class="calorie-value">{{ Math.round(dailySummary.total_calories) }}</span>
              <span class="calorie-unit">kcal</span>
              <span class="calorie-label">ทานไปแล้ว</span>
            </div>
          </div>

          <div class="calorie-info-row">
            <div class="calorie-info-item">
              <span class="info-number remaining">{{ caloriesRemaining }}</span>
              <span class="info-label">เหลืออีก (kcal)</span>
            </div>
            <div class="calorie-divider"></div>
            <div class="calorie-info-item">
              <span class="info-number budget">{{ Math.round(bmrData.daily_budget) }}</span>
              <span class="info-label">งบต่อวัน (kcal)</span>
            </div>
          </div>
        </div>

        <!-- BMR / TDEE Card -->
        <div class="stats-row">
          <div class="stat-card glass-card">
            <span class="stat-emoji">🔥</span>
            <span class="stat-value">{{ Math.round(bmrData.bmr) }}</span>
            <span class="stat-label">BMR</span>
          </div>
          <div class="stat-card glass-card">
            <span class="stat-emoji">⚡</span>
            <span class="stat-value">{{ Math.round(bmrData.tdee) }}</span>
            <span class="stat-label">TDEE</span>
          </div>
          <div class="stat-card glass-card">
            <span class="stat-emoji">🍽️</span>
            <span class="stat-value">{{ dailySummary.meal_count || 0 }}</span>
            <span class="stat-label">มื้อวันนี้</span>
          </div>
        </div>

        <!-- สารอาหาร -->
        <div class="macros-section glass-card">
          <h3 class="section-title">📊 สารอาหารวันนี้</h3>
          <div class="macros-grid">
            <div class="macro-item">
              <div class="macro-bar-container">
                <div class="macro-bar protein" :style="{ width: Math.min(dailySummary.total_protein * 2, 100) + '%' }"></div>
              </div>
              <div class="macro-info">
                <span class="macro-name">โปรตีน</span>
                <span class="macro-value">{{ Math.round(dailySummary.total_protein || 0) }}g</span>
              </div>
            </div>
            <div class="macro-item">
              <div class="macro-bar-container">
                <div class="macro-bar carbs" :style="{ width: Math.min(dailySummary.total_carbs * 0.8, 100) + '%' }"></div>
              </div>
              <div class="macro-info">
                <span class="macro-name">คาร์โบไฮเดรต</span>
                <span class="macro-value">{{ Math.round(dailySummary.total_carbs || 0) }}g</span>
              </div>
            </div>
            <div class="macro-item">
              <div class="macro-bar-container">
                <div class="macro-bar fat" :style="{ width: Math.min(dailySummary.total_fat * 2, 100) + '%' }"></div>
              </div>
              <div class="macro-info">
                <span class="macro-name">ไขมัน</span>
                <span class="macro-value">{{ Math.round(dailySummary.total_fat || 0) }}g</span>
              </div>
            </div>
          </div>
        </div>

        <!-- รายการมื้ออาหารวันนี้ -->
        <div class="meals-section">
          <h3 class="section-title">🍱 มื้ออาหารวันนี้</h3>

          <div v-if="todayMeals.length === 0" class="empty-state glass-card">
            <span class="empty-icon">📷</span>
            <p class="empty-text">ยังไม่ได้บันทึกอาหารวันนี้</p>
            <p class="empty-subtext">ถ่ายรูปอาหารเพื่อเริ่มติดตาม!</p>
          </div>

          <div v-else class="meal-list">
            <div
              v-for="(meal, index) in todayMeals"
              :key="meal.id || index"
              class="meal-card glass-card"
              :style="{ animationDelay: index * 0.1 + 's' }"
            >
              <div class="meal-header">
                <span class="meal-type-icon">{{ mealTypeIcons[meal.meal_type] || '🍽️' }}</span>
                <div class="meal-type-info">
                  <span class="meal-type-name">{{ mealTypeLabels[meal.meal_type] || meal.meal_type }}</span>
                  <span class="meal-food-name">{{ meal.food_name || 'อาหาร' }}</span>
                </div>
                <div
                  class="meal-grade"
                  :style="{
                    color: getGrade(meal.grade).color,
                    background: getGrade(meal.grade).bg
                  }"
                >
                  {{ getGrade(meal.grade).label }}
                </div>
              </div>

              <div class="meal-nutrients">
                <span class="nutrient">🔥 {{ Math.round(meal.calories || 0) }} kcal</span>
                <span class="nutrient">💪 {{ Math.round(meal.protein || 0) }}g</span>
                <span class="nutrient">🌾 {{ Math.round(meal.carbs || 0) }}g</span>
                <span class="nutrient">🧈 {{ Math.round(meal.fat || 0) }}g</span>
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
  background: var(--bg-dark);
  min-height: 100vh;
}

/* ==================== หัวข้อ ==================== */
.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-top: 8px;
}

.greeting-text {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 2px;
}

.user-name {
  font-size: 26px;
  font-weight: 700;
}

.date-badge {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-sm);
  padding: 8px 14px;
  backdrop-filter: blur(10px);
}

.date-text {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

/* ==================== Loading ==================== */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

/* ==================== Circular Progress ==================== */
.calorie-section {
  text-align: center;
  padding: 28px 20px;
  margin-bottom: 16px;
  animation: slideUp 0.5s ease;
}

.calorie-ring {
  position: relative;
  width: 160px;
  height: 160px;
  margin: 0 auto 20px;
}

.progress-ring {
  transition: stroke-dashoffset 1.5s ease;
  filter: drop-shadow(0 0 6px currentColor);
}

.calorie-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.calorie-value {
  font-size: 32px;
  font-weight: 800;
  line-height: 1;
}

.calorie-unit {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 400;
}

.calorie-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 4px;
}

.calorie-info-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.calorie-info-item {
  text-align: center;
}

.calorie-divider {
  width: 1px;
  height: 36px;
  background: rgba(255, 255, 255, 0.1);
}

.info-number {
  display: block;
  font-size: 22px;
  font-weight: 700;
}

.info-number.remaining {
  color: var(--grade-good);
}

.info-number.budget {
  color: var(--primary-start);
}

.info-label {
  font-size: 11px;
  color: var(--text-muted);
}

/* ==================== Stats Row ==================== */
.stats-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 16px;
  animation: slideUp 0.6s ease;
}

.stat-card {
  text-align: center;
  padding: 14px 10px;
}

.stat-emoji {
  font-size: 22px;
  display: block;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  display: block;
}

.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  display: block;
  margin-top: 2px;
}

/* ==================== สารอาหาร ==================== */
.macros-section {
  margin-bottom: 16px;
  animation: slideUp 0.7s ease;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
}

.macros-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.macro-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.macro-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.macro-name {
  font-size: 13px;
  color: var(--text-secondary);
}

.macro-value {
  font-size: 14px;
  font-weight: 600;
}

.macro-bar-container {
  width: 100%;
  height: 6px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.macro-bar {
  height: 100%;
  border-radius: 3px;
  transition: width 1.2s ease;
}

.macro-bar.protein {
  background: linear-gradient(90deg, #667eea, #764ba2);
}

.macro-bar.carbs {
  background: linear-gradient(90deg, #f093fb, #f5576c);
}

.macro-bar.fat {
  background: linear-gradient(90deg, #43e97b, #38f9d7);
}

/* ==================== มื้ออาหาร ==================== */
.meals-section {
  animation: slideUp 0.8s ease;
}

.empty-state {
  text-align: center;
  padding: 32px 20px;
}

.empty-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: 13px;
  color: var(--text-muted);
}

.meal-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.meal-card {
  padding: 16px;
  animation: slideUp 0.5s ease backwards;
}

.meal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.meal-type-icon {
  font-size: 28px;
  flex-shrink: 0;
}

.meal-type-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.meal-type-name {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.meal-food-name {
  font-size: 15px;
  font-weight: 600;
}

.meal-grade {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}

.meal-nutrients {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.nutrient {
  font-size: 12px;
  color: var(--text-secondary);
  background: rgba(255, 255, 255, 0.04);
  padding: 4px 8px;
  border-radius: 6px;
}
</style>
