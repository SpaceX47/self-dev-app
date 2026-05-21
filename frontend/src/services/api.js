// บริการ API — ใช้เชื่อมต่อกับ Backend FastAPI
import axios from 'axios'

// สร้าง axios instance ที่ใช้ same origin
const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json'
  }
})

// ==================== ผู้ใช้ (Users) ====================

// สร้างผู้ใช้ใหม่
export const createUser = (userData) => {
  return api.post('/users', userData)
}

// ดึงข้อมูลผู้ใช้
export const getUser = (userId) => {
  return api.get(`/users/${userId}`)
}

// อัพเดทข้อมูลผู้ใช้
export const updateUser = (userId, userData) => {
  return api.put(`/users/${userId}`, userData)
}

// ดึงค่า BMR/TDEE/งบแคลอรี่ต่อวัน
export const getUserBMR = (userId) => {
  return api.get(`/users/${userId}/bmr`)
}

// ==================== มื้ออาหาร (Meals) ====================

// อัพโหลดรูปอาหาร (multipart form)
export const uploadMeal = (userId, mealType, imageFile) => {
  const formData = new FormData()
  formData.append('meal_type', mealType)
  formData.append('image', imageFile)
  return api.post(`/users/${userId}/meals`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

// ดึงรายการมื้ออาหาร (ตามวันที่)
export const getMeals = (userId, mealDate) => {
  return api.get(`/users/${userId}/meals`, {
    params: { meal_date: mealDate }
  })
}

// ดึงสรุปแคลอรี่รายวัน
export const getDailySummary = (userId, targetDate) => {
  return api.get(`/users/${userId}/meals/daily-summary`, {
    params: { target_date: targetDate }
  })
}

// ==================== กิจกรรม (Activities) ====================

// สร้างกิจกรรมใหม่
export const createActivity = (userId, activityData) => {
  return api.post(`/users/${userId}/activities`, activityData)
}

// ดึงรายการกิจกรรม
export const getActivities = (userId) => {
  return api.get(`/users/${userId}/activities`)
}

// ==================== เป้าหมายรายสัปดาห์ (Weekly Goals) ====================

// สร้างเป้าหมายใหม่
export const createWeeklyGoal = (userId, goalData) => {
  return api.post(`/users/${userId}/weekly-goals`, goalData)
}

// ดึงรายการเป้าหมาย
export const getWeeklyGoals = (userId) => {
  return api.get(`/users/${userId}/weekly-goals`)
}

// ดึงความคืบหน้าและคำแนะนำ
export const getGoalProgress = (userId, goalId) => {
  return api.get(`/users/${userId}/weekly-goals/${goalId}/progress`)
}

export default api
