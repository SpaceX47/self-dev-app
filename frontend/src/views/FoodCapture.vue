<script setup>
// หน้าวิเคราะห์อาหารด้วย AI Vision (Food AI Vision)
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { uploadMeal, getUserBMR } from '../services/api'

const router = useRouter()
const userId = localStorage.getItem('user_id')

const mealType = ref('breakfast')
const selectedFile = ref(null)
const imagePreview = ref(null)
const isUploading = ref(false)
const uploadError = ref(null)
const analysisResult = ref(null)
const dailyBudget = ref(2000) // ค่าเริ่มต้นกรณีไม่มีข้อมูล
const currentQuota = ref(600) // ค่าเริ่มต้น

// สัดส่วนแคลอรี่แต่ละมื้อ
const quotaPercentages = {
  breakfast: 0.30,
  lunch: 0.40,
  dinner: 0.30,
  snack: 0.0
}

onMounted(async () => {
  if (!userId) {
    router.push('/')
    return
  }
  
  try {
    const res = await getUserBMR(userId)
    dailyBudget.value = res.data.daily_calorie_budget
    updateQuota()
  } catch (err) {
    console.error('ไม่สามารถดึงข้อมูล BMR ได้:', err)
  }
})

const updateQuota = () => {
  const pct = quotaPercentages[mealType.value]
  currentQuota.value = Math.round(dailyBudget.value * pct)
}

const onFileChange = (e) => {
  const file = e.target.files[0]
  if (!file) return

  selectedFile.value = file
  uploadError.value = null
  analysisResult.value = null

  // สร้าง preview
  const reader = new FileReader()
  reader.onload = (event) => {
    imagePreview.value = event.target.result
  }
  reader.readAsDataURL(file)
}

const triggerFileInput = () => {
  document.getElementById('file-input').click()
}

const handleUpload = async () => {
  if (!selectedFile.value) {
    uploadError.value = 'กรุณาเลือกหรือถ่ายรูปอาหารก่อน'
    return
  }

  isUploading.value = true
  uploadError.value = null
  analysisResult.value = null

  try {
    const res = await uploadMeal(userId, mealType.value, selectedFile.value)
    analysisResult.value = res.data
  } catch (err) {
    console.error('เกิดข้อผิดพลาดในการวิเคราะห์อาหาร:', err)
    uploadError.value = err.response?.data?.detail || 'เกิดข้อผิดพลาดจากเซิร์ฟเวอร์ กรุณาลองใหม่อีกครั้ง'
  } finally {
    isUploading.value = false
  }
}

const resetForm = () => {
  selectedFile.value = null
  imagePreview.value = null
  analysisResult.value = null
  uploadError.value = null
}
</script>

<template>
  <div class="page-container food-capture">
    <!-- Header -->
    <header class="header">
      <h1 class="page-title"> Food AI Vision</h1>
      <p class="page-subtitle">ถ่ายรูปอาหารเพื่อวิเคราะห์โภชนาการด้วย AI</p>
    </header>

    <!-- ฟอร์มหลัก -->
    <div class="glass-card capture-card" v-if="!analysisResult">
      <!-- เลือกประเภทมื้ออาหาร -->
      <div class="form-group">
        <label class="form-label">มื้ออาหาร</label>
        <div class="meal-selector">
          <button 
            type="button" 
            class="meal-btn" 
            :class="{ active: mealType === 'breakfast' }"
            @click="mealType = 'breakfast'; updateQuota()"
          >
            🍳 เช้า (30%)
          </button>
          <button 
            type="button" 
            class="meal-btn" 
            :class="{ active: mealType === 'lunch' }"
            @click="mealType = 'lunch'; updateQuota()"
          >
            🍜 กลางวัน (40%)
          </button>
          <button 
            type="button" 
            class="meal-btn" 
            :class="{ active: mealType === 'dinner' }"
            @click="mealType = 'dinner'; updateQuota()"
          >
            🥗 เย็น (30%)
          </button>
          <button 
            type="button" 
            class="meal-btn" 
            :class="{ active: mealType === 'snack' }"
            @click="mealType = 'snack'; updateQuota()"
          >
            🧁 ว่าง
          </button>
        </div>
        <p v-if="mealType !== 'snack'" class="quota-info">
          โควต้าเป้าหมายมื้อนี้ของคุณ: <span class="highlight">{{ currentQuota }} kcal</span>
        </p>
        <p v-else class="quota-info">
          ของว่างไม่มีโควต้าแคลอรี่เฉพาะมื้อ
        </p>
      </div>

      <!-- พื้นที่กล้อง / อัพโหลดรูป -->
      <div class="upload-area" :class="{ 'has-preview': imagePreview }" @click="triggerFileInput">
        <input 
          id="file-input" 
          type="file" 
          accept="image/*" 
          capture="environment" 
          class="hidden-input" 
          @change={onFileChange} 
        />
        
        <div v-if="!imagePreview" class="upload-placeholder">
          <span class="camera-icon">📸</span>
          <span class="upload-text">กดเพื่อถ่ายรูป หรือ เลือกรูปอาหาร</span>
          <span class="upload-hint">รองรับรูปถ่ายอาหารทุกประเภท</span>
        </div>
        
        <div v-else class="preview-container">
          <img :src="imagePreview" alt="Food preview" class="preview-img" />
          <div class="change-img-overlay">
            <span>เปลี่ยนรูปอาหาร</span>
          </div>
        </div>
      </div>

      <p v-if="uploadError" class="error-msg">⚠️ {{ uploadError }}</p>

      <!-- ปุ่มส่งวิเคราะห์ -->
      <button 
        class="btn-primary start-analysis-btn" 
        :disabled="isUploading || !selectedFile" 
        @click="handleUpload"
      >
        <template v-if="isUploading">
          <span class="loading-spinner"></span>
          <span>กำลังประมวลผลด้วย AI Vision...</span>
        </template>
        <template v-else>
          <span>ส่งรูปให้ AI วิเคราะห์ 🚀</span>
        </template>
      </button>
    </div>

    <!-- ผลลัพธ์วิเคราะห์จาก AI -->
    <div class="glass-card result-card scale-in" v-else>
      <div class="result-header">
        <div class="result-img-container">
          <img :src="imagePreview" alt="Analyzed food" class="result-preview-img" />
          <div class="grade-badge" :class="analysisResult.grade">
            {{ analysisResult.grade === 'good' ? 'เกรด Good 🎉' : analysisResult.grade === 'medium' ? 'เกรด Medium ⚠️' : 'เกรด Bad ❌' }}
          </div>
        </div>
        <h2 class="food-name">{{ analysisResult.food_name }}</h2>
        <p class="meal-meta">{{ mealType === 'breakfast' ? 'มื้อเช้า' : mealType === 'lunch' ? 'มื้อกลางวัน' : mealType === 'dinner' ? 'มื้อเย็น' : 'ของว่าง' }} • {{ analysisResult.meal_date }}</p>
      </div>

      <!-- แคลอรี่เปรียบเทียบ -->
      <div class="calorie-comparison">
        <div class="cal-box current">
          <span class="cal-val">{{ Math.round(analysisResult.calories) }}</span>
          <span class="cal-lbl">แคลอรี่จริง (kcal)</span>
        </div>
        <div class="cal-divider">vs</div>
        <div class="cal-box quota">
          <span class="cal-val">{{ mealType !== 'snack' ? currentQuota : '-' }}</span>
          <span class="cal-lbl">โควต้ามื้อ (kcal)</span>
        </div>
      </div>

      <!-- เกรดและการประเมินอย่างละเอียด -->
      <div class="grade-feedback" :class="analysisResult.grade">
        <p class="feedback-text">
          <strong v-if="analysisResult.grade === 'good'">ยอดเยี่ยม! 👍</strong>
          <strong v-else-if="analysisResult.grade === 'medium'">พอใช้ได้ ⚠️</strong>
          <strong v-else>แคลอรี่สูงเกินไป ❌</strong>
          
          <span v-if="analysisResult.grade === 'good'"> มื้อนี้สารอาหารครบถ้วนและปริมาณแคลอรี่พอดีกับโควต้า</span>
          <span v-else-if="analysisResult.grade === 'medium'"> ปริมาณแคลอรี่เกินเล็กน้อย หรืออัตราส่วนโปรตีนยังไม่สมดุล</span>
          <span v-else> ปริมาณแคลอรี่สูงกว่าเป้าหมายมื้อนี้มากเกินไป แนะนำให้ควบคุมปริมาณในมื้อถัดไป</span>
        </p>
      </div>

      <!-- รายละเอียดสารอาหาร (Macros) -->
      <div class="macros-grid">
        <div class="macro-card protein">
          <span class="macro-emoji">🍗</span>
          <span class="macro-val">{{ analysisResult.protein_g }}g</span>
          <span class="macro-lbl">โปรตีน</span>
        </div>
        <div class="macro-card carbs">
          <span class="macro-emoji">🍞</span>
          <span class="macro-val">{{ analysisResult.carbs_g }}g</span>
          <span class="macro-lbl">คาร์บ</span>
        </div>
        <div class="macro-card fat">
          <span class="macro-emoji">🥑</span>
          <span class="macro-val">{{ analysisResult.fat_g }}g</span>
          <span class="macro-lbl">ไขมัน</span>
        </div>
      </div>

      <!-- ปุ่มต่างๆ -->
      <div class="button-group">
        <button class="btn-primary" @click="router.push('/dashboard')">
          กลับสู่หน้าหลัก
        </button>
        <button class="btn-accent secondary-btn" @click="resetForm">
          บันทึกมื้ออื่นต่อ
        </button>
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

.capture-card, .result-card {
  margin-bottom: 20px;
  animation: slideUp 0.5s ease;
}

/* เลือกประเภทมื้อ */
.meal-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 6px;
  margin-bottom: 12px;
}

.meal-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  padding: 10px 4px;
  font-family: 'Prompt', sans-serif;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.meal-btn.active {
  background: linear-gradient(135deg, var(--primary-start), var(--primary-end));
  border-color: transparent;
  color: white;
  box-shadow: 0 4px 10px rgba(102, 126, 234, 0.3);
}

.quota-info {
  font-size: 13px;
  color: var(--text-muted);
}

.quota-info .highlight {
  color: var(--accent-start);
  font-weight: 700;
}

/* กล้อง/อัพโหลด */
.upload-area {
  background: rgba(255, 255, 255, 0.04);
  border: 2px dashed rgba(255, 255, 255, 0.15);
  border-radius: var(--radius-md);
  height: 220px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  overflow: hidden;
  position: relative;
  margin-bottom: 20px;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: var(--primary-start);
  background: rgba(255, 255, 255, 0.06);
}

.upload-area.has-preview {
  border-style: solid;
  border-color: var(--glass-border);
}

.hidden-input {
  display: none;
}

.upload-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 20px;
}

.camera-icon {
  font-size: 44px;
  margin-bottom: 12px;
  animation: float 4s ease-in-out infinite;
}

.upload-text {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.upload-hint {
  font-size: 12px;
  color: var(--text-muted);
}

.preview-container {
  width: 100%;
  height: 100%;
  position: relative;
}

.preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.change-img-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.upload-area:hover .change-img-overlay {
  opacity: 1;
}

.change-img-overlay span {
  font-size: 14px;
  font-weight: 600;
  color: white;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  backdrop-filter: blur(5px);
  border: 1px solid rgba(255,255,255,0.3);
}

.error-msg {
  color: var(--grade-bad);
  font-size: 13px;
  margin-bottom: 16px;
  text-align: center;
}

.start-analysis-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

/* ผลลัพธ์วิเคราะห์ */
.result-header {
  text-align: center;
  margin-bottom: 20px;
}

.result-img-container {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  margin: 0 auto 16px;
  position: relative;
  border: 3px solid var(--glass-border);
  overflow: visible;
}

.result-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.grade-badge {
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%);
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  color: white;
  white-space: nowrap;
  box-shadow: var(--shadow-sm);
}

.grade-badge.good { background: var(--grade-good); }
.grade-badge.medium { background: var(--grade-medium); color: #000; }
.grade-badge.bad { background: var(--grade-bad); }

.food-name {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 4px;
}

.meal-meta {
  font-size: 13px;
  color: var(--text-muted);
}

/* เปรียบเทียบแคลอรี่ */
.calorie-comparison {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border-radius: var(--radius-sm);
  padding: 16px;
  margin-bottom: 16px;
}

.cal-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.cal-val {
  font-size: 26px;
  font-weight: 800;
}

.current .cal-val {
  color: var(--text-primary);
}

.quota .cal-val {
  color: var(--text-secondary);
}

.cal-lbl {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.cal-divider {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 700;
  padding: 0 16px;
}

/* เกรดและคำแนะนำ */
.grade-feedback {
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.5;
  margin-bottom: 20px;
  border-left: 4px solid;
}

.grade-feedback.good {
  background: rgba(0, 230, 118, 0.1);
  border-color: var(--grade-good);
  color: #c8e6c9;
}

.grade-feedback.medium {
  background: rgba(255, 171, 64, 0.1);
  border-color: var(--grade-medium);
  color: #ffe0b2;
}

.grade-feedback.bad {
  background: rgba(255, 82, 82, 0.1);
  border-color: var(--grade-bad);
  color: #ffcdd2;
}

/* Macros Grid */
.macros-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 24px;
}

.macro-card {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 12px 6px;
}

.macro-emoji {
  font-size: 18px;
  margin-bottom: 4px;
}

.macro-val {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.macro-lbl {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

/* ปุ่มควบคุม */
.button-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.secondary-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-primary);
  box-shadow: none;
}

.secondary-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}
</style>
