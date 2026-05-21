<script setup>
// หน้าสร้างโปรไฟล์ — ฟอร์มกรอกข้อมูลส่วนตัวและเป้าหมายสุขภาพ
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { createUser } from '../services/api'

const router = useRouter()
const isLoading = ref(false)
const errorMsg = ref('')
const currentStep = ref(1) // แบ่งเป็น 2 ขั้นตอน

// ข้อมูลฟอร์ม
const form = reactive({
  name: '',
  email: '',
  password: '',
  weight_kg: '',
  height_cm: '',
  age: '',
  gender: 'male',
  goal: 'lose_weight'
})

// ตัวเลือกเพศ
const genderOptions = [
  { value: 'male', label: 'ชาย', icon: '👨' },
  { value: 'female', label: 'หญิง', icon: '👩' }
]

// ตัวเลือกเป้าหมาย
const goalOptions = [
  { value: 'lose_weight', label: 'ลดน้ำหนัก', icon: '🔥', desc: 'เผาผลาญไขมัน' },
  { value: 'maintain', label: 'รักษาน้ำหนัก', icon: '⚖️', desc: 'คงที่สมดุล' },
  { value: 'gain_muscle', label: 'เพิ่มกล้ามเนื้อ', icon: '💪', desc: 'สร้างกล้ามเนื้อ' }
]

// ไปขั้นตอนถัดไป
const nextStep = () => {
  if (!form.name || !form.email || !form.password) {
    errorMsg.value = 'กรุณากรอกข้อมูลให้ครบ'
    return
  }
  errorMsg.value = ''
  currentStep.value = 2
}

// ย้อนกลับ
const prevStep = () => {
  currentStep.value = 1
}

// ส่งข้อมูลสร้างผู้ใช้
const submitForm = async () => {
  if (!form.weight_kg || !form.height_cm || !form.age) {
    errorMsg.value = 'กรุณากรอกข้อมูลให้ครบ'
    return
  }

  isLoading.value = true
  errorMsg.value = ''

  try {
    const payload = {
      name: form.name,
      email: form.email,
      password: form.password,
      weight_kg: parseFloat(form.weight_kg),
      height_cm: parseFloat(form.height_cm),
      age: parseInt(form.age),
      gender: form.gender,
      goal: form.goal
    }

    const response = await createUser(payload)
    // เก็บ user_id ใน localStorage
    const userId = response.data.id || response.data.user_id
    localStorage.setItem('user_id', userId)
    localStorage.setItem('user_name', form.name)

    // ไปหน้า Dashboard
    router.push('/dashboard')
  } catch (error) {
    console.error('สร้างผู้ใช้ล้มเหลว:', error)
    errorMsg.value = error.response?.data?.detail || 'เกิดข้อผิดพลาด กรุณาลองใหม่อีกครั้ง'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="profile-page">
    <div class="bg-gradient"></div>

    <div class="profile-content">
      <!-- หัวข้อ -->
      <div class="header">
        <button v-if="currentStep === 2" class="back-btn" @click="prevStep">
          ← ย้อนกลับ
        </button>
        <div class="step-indicator">
          <div class="step" :class="{ active: currentStep >= 1 }">1</div>
          <div class="step-line" :class="{ active: currentStep >= 2 }"></div>
          <div class="step" :class="{ active: currentStep >= 2 }">2</div>
        </div>
        <h1 class="page-title">
          {{ currentStep === 1 ? 'สร้างโปรไฟล์' : 'ข้อมูลสุขภาพ' }}
        </h1>
        <p class="page-desc">
          {{ currentStep === 1 ? 'กรอกข้อมูลพื้นฐานของคุณ' : 'บอกเราเกี่ยวกับร่างกายคุณ' }}
        </p>
      </div>

      <!-- ข้อความ Error -->
      <div v-if="errorMsg" class="error-msg">
        <span>⚠️</span> {{ errorMsg }}
      </div>

      <!-- ขั้นตอนที่ 1: ข้อมูลพื้นฐาน -->
      <transition name="fade" mode="out-in">
        <div v-if="currentStep === 1" key="step1" class="form-section">
          <div class="form-group">
            <label class="form-label">👤 ชื่อของคุณ</label>
            <input
              v-model="form.name"
              type="text"
              class="form-input"
              placeholder="กรอกชื่อ"
            />
          </div>

          <div class="form-group">
            <label class="form-label">📧 อีเมล</label>
            <input
              v-model="form.email"
              type="email"
              class="form-input"
              placeholder="example@email.com"
            />
          </div>

          <div class="form-group">
            <label class="form-label">🔒 รหัสผ่าน</label>
            <input
              v-model="form.password"
              type="password"
              class="form-input"
              placeholder="ตั้งรหัสผ่าน"
            />
          </div>

          <button class="btn-primary" @click="nextStep">
            ถัดไป →
          </button>
        </div>

        <!-- ขั้นตอนที่ 2: ข้อมูลสุขภาพ -->
        <div v-else key="step2" class="form-section">
          <!-- น้ำหนัก ส่วนสูง อายุ -->
          <div class="metrics-grid">
            <div class="form-group">
              <label class="form-label">⚖️ น้ำหนัก (กก.)</label>
              <input
                v-model="form.weight_kg"
                type="number"
                class="form-input"
                placeholder="65"
                step="0.1"
              />
            </div>
            <div class="form-group">
              <label class="form-label">📏 ส่วนสูง (ซม.)</label>
              <input
                v-model="form.height_cm"
                type="number"
                class="form-input"
                placeholder="170"
              />
            </div>
          </div>

          <div class="form-group">
            <label class="form-label">🎂 อายุ (ปี)</label>
            <input
              v-model="form.age"
              type="number"
              class="form-input"
              placeholder="25"
            />
          </div>

          <!-- เลือกเพศ -->
          <div class="form-group">
            <label class="form-label">เพศ</label>
            <div class="selection-row">
              <button
                v-for="option in genderOptions"
                :key="option.value"
                class="select-card"
                :class="{ selected: form.gender === option.value }"
                @click="form.gender = option.value"
              >
                <span class="select-icon">{{ option.icon }}</span>
                <span class="select-label">{{ option.label }}</span>
              </button>
            </div>
          </div>

          <!-- เลือกเป้าหมาย -->
          <div class="form-group">
            <label class="form-label">🎯 เป้าหมายของคุณ</label>
            <div class="goal-cards">
              <button
                v-for="option in goalOptions"
                :key="option.value"
                class="goal-card"
                :class="{ selected: form.goal === option.value }"
                @click="form.goal = option.value"
              >
                <span class="goal-icon">{{ option.icon }}</span>
                <div class="goal-info">
                  <span class="goal-label">{{ option.label }}</span>
                  <span class="goal-desc">{{ option.desc }}</span>
                </div>
              </button>
            </div>
          </div>

          <!-- ปุ่มสร้างโปรไฟล์ -->
          <button
            class="btn-accent"
            :disabled="isLoading"
            @click="submitForm"
          >
            <span v-if="isLoading" class="loading-spinner"></span>
            <span v-else>🚀 เริ่มต้นเลย!</span>
          </button>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
.profile-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
}

.bg-gradient {
  position: fixed;
  inset: 0;
  background: linear-gradient(180deg, #1a1a3e 0%, #0f0f23 100%);
  z-index: -1;
}

.profile-content {
  max-width: 440px;
  margin: 0 auto;
  padding: 24px 20px 40px;
  animation: fadeIn 0.6s ease;
}

/* ==================== หัวข้อ ==================== */
.header {
  text-align: center;
  margin-bottom: 28px;
}

.back-btn {
  position: absolute;
  left: 20px;
  top: 24px;
  background: none;
  border: none;
  color: var(--text-secondary);
  font-family: 'Prompt', sans-serif;
  font-size: 14px;
  cursor: pointer;
  padding: 8px;
  touch-action: manipulation;
}

.step-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0;
  margin-bottom: 20px;
  padding-top: 16px;
}

.step {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-muted);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.4s ease;
}

.step.active {
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.step-line {
  width: 60px;
  height: 3px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  transition: all 0.4s ease;
}

.step-line.active {
  background: linear-gradient(90deg, var(--primary-start), var(--primary-end));
}

.page-title {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 6px;
}

.page-desc {
  font-size: 15px;
  color: var(--text-secondary);
}

/* ==================== Error ==================== */
.error-msg {
  background: rgba(255, 82, 82, 0.15);
  border: 1px solid rgba(255, 82, 82, 0.3);
  border-radius: var(--radius-sm);
  padding: 12px 16px;
  margin-bottom: 20px;
  font-size: 14px;
  color: #ff5252;
  display: flex;
  align-items: center;
  gap: 8px;
  animation: scaleIn 0.3s ease;
}

/* ==================== ฟอร์ม ==================== */
.form-section {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* ==================== เลือกเพศ ==================== */
.selection-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.select-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 18px 16px;
  background: var(--glass-bg);
  border: 2px solid var(--glass-border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Prompt', sans-serif;
  touch-action: manipulation;
}

.select-card.selected {
  border-color: var(--primary-start);
  background: rgba(102, 126, 234, 0.15);
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.2);
}

.select-icon {
  font-size: 28px;
}

.select-label {
  font-size: 14px;
  font-weight: 500;
}

/* ==================== เลือกเป้าหมาย ==================== */
.goal-cards {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.goal-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px;
  background: var(--glass-bg);
  border: 2px solid var(--glass-border);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.3s ease;
  font-family: 'Prompt', sans-serif;
  text-align: left;
  touch-action: manipulation;
}

.goal-card.selected {
  border-color: var(--accent-end);
  background: rgba(245, 87, 108, 0.12);
  color: white;
  box-shadow: 0 4px 15px rgba(245, 87, 108, 0.2);
}

.goal-icon {
  font-size: 30px;
  flex-shrink: 0;
}

.goal-info {
  display: flex;
  flex-direction: column;
}

.goal-label {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.goal-desc {
  font-size: 12px;
  color: var(--text-muted);
}

.btn-accent:disabled,
.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}
</style>
