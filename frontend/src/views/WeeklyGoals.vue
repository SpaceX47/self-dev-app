<script setup>
// หน้าจัดการเป้าหมายรายสัปดาห์ (Weekly Goals)
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createWeeklyGoal, getWeeklyGoals, getGoalProgress } from '../services/api'

const router = useRouter()
const userId = localStorage.getItem('user_id')

// State
const activityType = ref('running')
const targetValue = ref(30)
const targetUnit = ref('km')
const goalsList = ref([])
const goalsWithProgress = ref([])
const isSubmitting = ref(false)
const isLoading = ref(false)
const errorMsg = ref(null)
const successMsg = ref(null)

// ประเภทกิจกรรมที่รองรับ
const activityTypes = [
  { id: 'running', label: 'วิ่ง', emoji: '🏃' },
  { id: 'walking', label: 'เดิน', emoji: '🚶' },
  { id: 'cycling', label: 'ปั่นจักรยาน', emoji: '🚴' },
  { id: 'swimming', label: 'ว่ายน้ำ', emoji: '🏊' },
  { id: 'weight_training', label: 'เวทเทรนนิ่ง', emoji: '🏋️' },
  { id: 'yoga', label: 'โยคะ', emoji: '🧘' },
  { id: 'other', label: 'อื่นๆ', emoji: '🤸' }
]

const unitOptions = [
  { value: 'km', label: 'กิโลเมตร (km)' },
  { value: 'minutes', label: 'นาที (minutes)' },
  { value: 'sessions', label: 'ครั้ง (sessions)' },
  { value: 'calories', label: 'แคลอรี่ (calories)' }
]

onMounted(async () => {
  if (!userId) {
    router.push('/')
    return
  }

  fetchGoals()
})

const fetchGoals = async () => {
  isLoading.value = true
  goalsWithProgress.value = []
  
  try {
    const goalsRes = await getWeeklyGoals(userId)
    goalsList.value = goalsRes.data

    // ดึงความคืบหน้าของแต่ละเป้าหมายแบบเรียลไทม์
    const progressPromises = goalsList.value.map(goal => 
      getGoalProgress(userId, goal.id)
        .then(res => res.data)
        .catch(err => {
          console.error(`ไม่สามารถโหลดความคืบหน้าของเป้าหมาย ${goal.id} ได้:`, err)
          return null;
        })
    )

    const results = await Promise.all(progressPromises)
    goalsWithProgress.value = results.filter(r => r !== null)
  } catch (err) {
    console.error('ไม่สามารถดึงเป้าหมายได้:', err)
  } finally {
    isLoading.value = false
  }
}

const handleSubmit = async () => {
  if (!targetValue.value || targetValue.value <= 0) {
    errorMsg.value = 'กรุณากรอกค่าเป้าหมายที่มากกว่า 0'
    return
  }

  isSubmitting.value = true
  errorMsg.value = null
  successMsg.value = null

  const payload = {
    activity_type: activityType.value,
    target_value: parseFloat(targetValue.value),
    target_unit: targetUnit.value
  }

  try {
    await createWeeklyGoal(userId, payload)
    successMsg.value = 'สร้างเป้าหมายรายสัปดาห์สำเร็จแล้ว!'
    
    // โหลดเป้าหมายใหม่ทั้งหมด
    fetchGoals()
    
    // ล้างข้อความสำเร็จหลังจาก 3 วินาที
    setTimeout(() => {
      successMsg.value = null
    }, 3000)
  } catch (err) {
    console.error('เกิดข้อผิดพลาดในการสร้างเป้าหมาย:', err)
    errorMsg.value = err.response?.data?.detail || 'เป้าหมายประเภทนี้ถูกสร้างขึ้นแล้วในสัปดาห์นี้'
  } finally {
    isSubmitting.value = false
  }
}

const getEmoji = (type) => {
  const item = activityTypes.find(t => t.id === type)
  return item ? item.emoji : '🎯'
}

const getLabel = (type) => {
  const item = activityTypes.find(t => t.id === type)
  return item ? item.label : type
}

const getUnitLabel = (unit) => {
  const item = unitOptions.find(u => u.value === unit)
  return item ? item.label.split(' ')[0] : unit
}
</script>

<template>
  <div class="page-container weekly-goals">
    <!-- Header -->
    <header class="header">
      <h1 class="page-title">Weekly Goals</h1>
      <p class="page-subtitle">ตั้งเป้าหมายและพัฒนาสุขภาพรายสัปดาห์</p>
    </header>

    <!-- ตั้งค่าเป้าหมายใหม่ -->
    <div class="glass-card form-card">
      <h2 class="section-title">🎯 ตั้งเป้าหมายใหม่สัปดาห์นี้</h2>
      
      <div class="form-row">
        <!-- เลือกประเภทกิจกรรม -->
        <div class="form-group col-2">
          <label class="form-label">ประเภทกิจกรรม</label>
          <select v-model="activityType" class="form-select">
            <option v-for="act in activityTypes" :key="act.id" :value="act.id">
              {{ act.emoji }} {{ act.label }}
            </option>
          </select>
        </div>
      </div>

      <div class="form-row">
        <!-- ค่าเป้าหมาย -->
        <div class="form-group col">
          <label class="form-label">ค่าเป้าหมาย</label>
          <input 
            type="number" 
            v-model.number="targetValue" 
            min="1" 
            class="form-input" 
            required 
          />
        </div>

        <!-- หน่วย -->
        <div class="form-group col">
          <label class="form-label">หน่วยเป้าหมาย</label>
          <select v-model="targetUnit" class="form-select">
            <option v-for="unit in unitOptions" :key="unit.value" :value="unit.value">
              {{ unit.label }}
            </option>
          </select>
        </div>
      </div>

      <p v-if="errorMsg" class="error-msg">⚠️ {{ errorMsg }}</p>
      <p v-if="successMsg" class="success-msg">🎉 {{ successMsg }}</p>

      <button 
        class="btn-primary submit-btn" 
        :disabled="isSubmitting" 
        @click="handleSubmit"
      >
        <span v-if="isSubmitting" class="loading-spinner"></span>
        <span v-else>ตั้งเป้าหมายรายสัปดาห์</span>
      </button>
    </div>

    <!-- รายการเป้าหมายและความคืบหน้า -->
    <div class="goals-section">
      <h2 class="section-title">📊 ความคืบหน้าสัปดาห์นี้</h2>

      <!-- กำลังโหลด -->
      <div v-if="isLoading" class="loading-container">
        <span class="loading-spinner"></span>
        <p>กำลังโหลดเป้าหมายสุขภาพ...</p>
      </div>

      <!-- ไม่มีเป้าหมาย -->
      <div v-else-if="goalsWithProgress.length === 0" class="empty-goals">
        <span class="empty-icon">🎯</span>
        <p class="empty-text">ยังไม่มีเป้าหมายสำหรับสัปดาห์นี้</p>
        <p class="empty-subtext">คุณสามารถเริ่มสร้างเป้าหมายได้โดยใช้ฟอร์มด้านบน</p>
      </div>

      <!-- รายการเป้าหมาย -->
      <div v-else class="goals-list">
        <div 
          v-for="progress in goalsWithProgress" 
          :key="progress.goal.id" 
          class="glass-card goal-item"
        >
          <div class="goal-header">
            <div class="goal-title-wrapper">
              <span class="goal-emoji">{{ getEmoji(progress.goal.activity_type) }}</span>
              <div>
                <h3 class="goal-name">เป้าหมาย{{ getLabel(progress.goal.activity_type) }}</h3>
                <p class="goal-dates">
                  {{ progress.goal.week_start_date }} ถึง {{ progress.goal.week_end_date }}
                </p>
              </div>
            </div>
            <div class="goal-completion-badge" :class="{ completed: progress.goal.is_completed }">
              {{ progress.goal.is_completed ? 'สำเร็จแล้ว! 🎉' : 'กำลังดำเนินการ' }}
            </div>
          </div>

          <!-- แถบแสดงความคืบหน้า -->
          <div class="progress-container">
            <div class="progress-bar-wrapper">
              <div 
                class="progress-bar-fill" 
                :style="{ width: progress.progress_percentage + '%' }"
                :class="{ completed: progress.goal.is_completed }"
              ></div>
            </div>
            <div class="progress-details">
              <span class="progress-percent">{{ progress.progress_percentage }}%</span>
              <span class="progress-values">
                {{ progress.goal.current_value.toFixed(1) }} / {{ progress.goal.target_value.toFixed(1) }} {{ getUnitLabel(progress.goal.target_unit) }}
              </span>
            </div>
          </div>

          <!-- ระบบแนะนำอัจฉริยะจาก AI -->
          <div class="recommendation-box" :class="{ completed: progress.goal.is_completed }">
            <span class="rec-icon">💡</span>
            <p class="rec-text">{{ progress.message }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.header {
  margin-bottom: 24px;
  text-align: center;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  margin-bottom: 6px;
  background: linear-gradient(135deg, var(--primary-start), var(--accent-start));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.page-subtitle {
  font-size: 13px;
  color: var(--text-secondary);
}

.section-title {
  font-size: 16px;
  font-weight: 700;
  margin-bottom: 16px;
  color: var(--text-primary);
}

.form-card {
  margin-bottom: 24px;
  animation: slideUp 0.5s ease;
}

/* ฟอร์ม */
.form-row {
  display: flex;
  gap: 12px;
}

.col {
  flex: 1;
}

.col-2 {
  flex: 2;
}

.error-msg {
  color: var(--grade-bad);
  font-size: 13px;
  text-align: center;
  margin-bottom: 12px;
}

.success-msg {
  color: var(--grade-good);
  font-size: 13px;
  text-align: center;
  margin-bottom: 12px;
}

/* รายการเป้าหมาย */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40px;
  color: var(--text-muted);
  gap: 12px;
}

.empty-goals {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  background: rgba(255, 255, 255, 0.02);
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: var(--radius-md);
}

.empty-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.empty-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.empty-subtext {
  font-size: 12px;
}

.goals-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.goal-item {
  animation: scaleIn 0.4s ease;
}

.goal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.goal-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.goal-emoji {
  font-size: 26px;
  background: rgba(255, 255, 255, 0.06);
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.goal-name {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.goal-dates {
  font-size: 11px;
  color: var(--text-muted);
}

.goal-completion-badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
  font-weight: 600;
}

.goal-completion-badge.completed {
  background: rgba(0, 230, 118, 0.15);
  color: var(--grade-good);
}

/* แถบ Progress */
.progress-container {
  margin-bottom: 16px;
}

.progress-bar-wrapper {
  background: rgba(255, 255, 255, 0.08);
  height: 10px;
  border-radius: 5px;
  overflow: hidden;
  margin-bottom: 6px;
}

.progress-bar-fill {
  background: linear-gradient(90deg, var(--primary-start), var(--primary-end));
  height: 100%;
  border-radius: 5px;
  transition: width 0.5s ease-out;
}

.progress-bar-fill.completed {
  background: linear-gradient(90deg, var(--grade-good), #00b0ff);
}

.progress-details {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.progress-percent {
  font-weight: 700;
  color: var(--text-primary);
}

.progress-values {
  color: var(--text-secondary);
}

/* กล่องคำแนะนำ */
.recommendation-box {
  background: rgba(102, 126, 234, 0.08);
  border: 1px solid rgba(102, 126, 234, 0.15);
  border-radius: var(--radius-sm);
  padding: 12px;
  display: flex;
  gap: 8px;
  align-items: flex-start;
}

.recommendation-box.completed {
  background: rgba(0, 230, 118, 0.08);
  border-color: rgba(0, 230, 118, 0.15);
}

.rec-icon {
  font-size: 15px;
  flex-shrink: 0;
}

.rec-text {
  font-size: 12px;
  line-height: 1.4;
  color: var(--text-secondary);
}
</style>
