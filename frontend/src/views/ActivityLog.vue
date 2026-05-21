<script setup>
// หน้าบันทึกกิจกรรมการออกกำลังกาย (Activity Tracker)
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { createActivity, getActivities, getUser } from '../services/api'

const router = useRouter()
const userId = localStorage.getItem('user_id')

// State
const activityType = ref('running')
const durationMinutes = ref(30)
const distanceKm = ref(null)
const notes = ref('')
const activityDate = ref(new Date().toISOString().substr(0, 10))
const userWeight = ref(70) // ค่าเริ่มต้นกรณีโหลดไม่สำเร็จ
const activitiesList = ref([])
const isSubmitting = ref(false)
const errorMsg = ref(null)
const successMsg = ref(null)

// ประเภทกิจกรรมที่รองรับ พร้อมค่า MET
const activityTypes = [
  { id: 'running', label: 'วิ่ง', emoji: '🏃', met: 9.8, hasDistance: true },
  { id: 'walking', label: 'เดิน', emoji: '🚶', met: 3.5, hasDistance: true },
  { id: 'cycling', label: 'ปั่นจักรยาน', emoji: '🚴', met: 7.5, hasDistance: true },
  { id: 'swimming', label: 'ว่ายน้ำ', emoji: '🏊', met: 8.0, hasDistance: false },
  { id: 'weight_training', label: 'เวทเทรนนิ่ง', emoji: '🏋️', met: 6.0, hasDistance: false },
  { id: 'yoga', label: 'โยคะ', emoji: '🧘', met: 3.0, hasDistance: false },
  { id: 'other', label: 'อื่นๆ', emoji: '🤸', met: 4.0, hasDistance: false }
]

const currentActivityInfo = computed(() => {
  return activityTypes.find(t => t.id === activityType.value)
})

// คำนวณแคลอรี่ที่เผาผลาญโดยประมาณในแบบ Real-time
const estimatedCalories = computed(() => {
  const met = currentActivityInfo.value?.met || 4.0
  const hours = durationMinutes.value / 60
  return Math.round(met * userWeight.value * hours)
})

onMounted(async () => {
  if (!userId) {
    router.push('/')
    return
  }

  // ดึงข้อมูลผู้ใช้เพื่อเอาน้ำหนักตัวมาคำนวณแคลอรี่
  try {
    const userRes = await getUser(userId)
    userWeight.value = userRes.data.weight_kg
  } catch (err) {
    console.error('ไม่สามารถดึงน้ำหนักผู้ใช้ได้:', err)
  }

  fetchActivities()
})

const fetchActivities = async () => {
  try {
    const res = await getActivities(userId)
    activitiesList.value = res.data
  } catch (err) {
    console.error('ไม่สามารถดึงข้อมูลประวัติกิจกรรมได้:', err)
  }
}

const handleSubmit = async () => {
  if (!durationMinutes.value || durationMinutes.value <= 0) {
    errorMsg.value = 'ระยะเวลาต้องมากกว่า 0 นาที'
    return
  }

  isSubmitting.value = true
  errorMsg.value = null
  successMsg.value = null

  const payload = {
    activity_type: activityType.value,
    duration_minutes: parseInt(durationMinutes.value),
    activity_date: activityDate.value,
    distance_km: currentActivityInfo.value.hasDistance && distanceKm.value ? parseFloat(distanceKm.value) : null,
    notes: notes.value || null
  }

  try {
    await createActivity(userId, payload)
    successMsg.value = 'บันทึกกิจกรรมสำเร็จแล้ว!'
    
    // รีเซ็ตฟอร์ม
    durationMinutes.value = 30
    distanceKm.value = null
    notes.value = ''
    
    // โหลดประวัติใหม่
    fetchActivities()
    
    // หายไปใน 3 วินาที
    setTimeout(() => {
      successMsg.value = null
    }, 3000)
  } catch (err) {
    console.error('เกิดข้อผิดพลาดในการบันทึกกิจกรรม:', err)
    errorMsg.value = err.response?.data?.detail || 'เกิดข้อผิดพลาดในการบันทึกข้อมูล'
  } finally {
    isSubmitting.value = false
  }
}

const getEmoji = (type) => {
  const item = activityTypes.find(t => t.id === type)
  return item ? item.emoji : '🏋️'
}

const getLabel = (type) => {
  const item = activityTypes.find(t => t.id === type)
  return item ? item.label : type
}

const formatDate = (dateStr) => {
  const options = { weekday: 'short', day: 'numeric', month: 'short' }
  return new Date(dateStr).toLocaleDateString('th-TH', options)
}
</script>

<template>
  <div class="page-container activity-log">
    <!-- Header -->
    <header class="header">
      <h1 class="page-title">Activity Tracker</h1>
      <p class="page-subtitle">บันทึกการออกกำลังกายและคำนวณแคลอรี่</p>
    </header>

    <!-- ฟอร์มบันทึกกิจกรรม -->
    <div class="glass-card form-card">
      <h2 class="section-title">🏃 บันทึกกิจกรรมวันนี้</h2>
      
      <!-- เลือกประเภทกิจกรรม -->
      <div class="form-group">
        <label class="form-label">ประเภทกิจกรรม</label>
        <div class="activity-grid">
          <button
            v-for="act in activityTypes"
            :key="act.id"
            type="button"
            class="activity-btn"
            :class="{ active: activityType === act.id }"
            @click="activityType = act.id; distanceKm = null"
          >
            <span class="act-emoji">{{ act.emoji }}</span>
            <span class="act-lbl">{{ act.label }}</span>
          </button>
        </div>
      </div>

      <!-- รายละเอียดกิจกรรม -->
      <div class="form-row">
        <div class="form-group col">
          <label class="form-label">ระยะเวลา (นาที)</label>
          <input 
            type="number" 
            v-model.number="durationMinutes" 
            min="1" 
            class="form-input" 
            required 
          />
        </div>

        <div v-if="currentActivityInfo.hasDistance" class="form-group col">
          <label class="form-label">ระยะทาง (กม.)</label>
          <input 
            type="number" 
            v-model.number="distanceKm" 
            min="0" 
            step="0.1" 
            class="form-input" 
            placeholder="เช่น 5.2" 
          />
        </div>
      </div>

      <div class="form-row">
        <div class="form-group col">
          <label class="form-label">วันที่ทำกิจกรรม</label>
          <input 
            type="date" 
            v-model="activityDate" 
            class="form-input" 
            required 
          />
        </div>
      </div>

      <div class="form-group">
        <label class="form-label">บันทึกเพิ่มเติม (ไม่บังคับ)</label>
        <input 
          type="text" 
          v-model="notes" 
          placeholder="เช่น สถิติใหม่วันนี้, รู้สึกเหนื่อยมาก" 
          class="form-input" 
        />
      </div>

      <!-- แสดงแคลอรี่ประมาณการ -->
      <div class="calorie-estimate">
        <div class="est-content">
          <span class="est-lbl">แคลอรี่ที่เผาผลาญโดยประมาณ:</span>
          <span class="est-val">🔥 ~{{ estimatedCalories }} kcal</span>
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
        <span v-else>บันทึกกิจกรรม</span>
      </button>
    </div>

    <!-- ประวัติกิจกรรมล่าสุด -->
    <div class="glass-card history-card">
      <h2 class="section-title">📅 ประวัติกิจกรรมล่าสุด</h2>
      
      <div v-if="activitiesList.length === 0" class="empty-history">
        <span class="empty-icon">🏖️</span>
        <p class="empty-text">ยังไม่มีประวัติกิจกรรมช่วงนี้</p>
      </div>

      <div v-else class="history-list">
        <div 
          v-for="item in activitiesList.slice(0, 10)" 
          :key="item.id" 
          class="history-item"
        >
          <div class="item-left">
            <span class="item-emoji">{{ getEmoji(item.activity_type) }}</span>
            <div class="item-details">
              <span class="item-name">{{ getLabel(item.activity_type) }}</span>
              <span class="item-time">
                {{ formatDate(item.activity_date) }} 
                <span v-if="item.notes" class="item-note">• {{ item.notes }}</span>
              </span>
            </div>
          </div>
          
          <div class="item-right">
            <span class="item-val">{{ item.duration_minutes }} นาที</span>
            <span class="item-sub-val" v-if="item.distance_km">{{ item.distance_km }} กม.</span>
            <span class="item-cal">🔥 -{{ Math.round(item.calories_burned) }} kcal</span>
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

.form-card, .history-card {
  margin-bottom: 20px;
  animation: slideUp 0.5s ease;
}

/* ตารางปุ่มเลือกกิจกรรม */
.activity-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.activity-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  padding: 12px 6px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
}

.activity-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.activity-btn.active {
  background: linear-gradient(135deg, var(--accent-start), var(--accent-end));
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
}

.act-emoji {
  font-size: 20px;
}

.act-lbl {
  font-size: 10px;
  font-weight: 500;
}

/* ฟอร์ม 2 คอลัมน์ */
.form-row {
  display: flex;
  gap: 12px;
}

.col {
  flex: 1;
}

/* คำนวณแคลอรี่ */
.calorie-estimate {
  background: rgba(245, 87, 108, 0.08);
  border: 1px solid rgba(245, 87, 108, 0.15);
  border-radius: var(--radius-sm);
  padding: 14px;
  margin: 16px 0;
  text-align: center;
}

.est-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.est-lbl {
  font-size: 13px;
  color: var(--text-secondary);
}

.est-val {
  font-size: 15px;
  font-weight: 700;
  color: var(--accent-end);
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

/* ประวัติกิจกรรม */
.empty-history {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 36px;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 13px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  transition: background 0.3s ease;
}

.history-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.item-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-emoji {
  font-size: 24px;
  background: rgba(255, 255, 255, 0.05);
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}

.item-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.item-time {
  font-size: 11px;
  color: var(--text-muted);
}

.item-note {
  font-style: italic;
}

.item-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
}

.item-val {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.item-sub-val {
  font-size: 11px;
  color: var(--text-secondary);
}

.item-cal {
  font-size: 12px;
  font-weight: 700;
  color: var(--accent-end);
}
</style>
