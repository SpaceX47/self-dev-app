// ตั้งค่า Vue Router พร้อม Navigation Guard
import { createRouter, createWebHistory } from 'vue-router'

import WelcomePage from '../views/WelcomePage.vue'
import ProfileSetup from '../views/ProfileSetup.vue'
import Dashboard from '../views/Dashboard.vue'
import FoodCapture from '../views/FoodCapture.vue'
import ActivityLog from '../views/ActivityLog.vue'
import WeeklyGoals from '../views/WeeklyGoals.vue'

const routes = [
  {
    path: '/',
    name: 'Welcome',
    component: WelcomePage,
    meta: { requiresAuth: false }
  },
  {
    path: '/setup',
    name: 'ProfileSetup',
    component: ProfileSetup,
    meta: { requiresAuth: false }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
    meta: { requiresAuth: true }
  },
  {
    path: '/food',
    name: 'FoodCapture',
    component: FoodCapture,
    meta: { requiresAuth: true }
  },
  {
    path: '/activity',
    name: 'ActivityLog',
    component: ActivityLog,
    meta: { requiresAuth: true }
  },
  {
    path: '/goals',
    name: 'WeeklyGoals',
    component: WeeklyGoals,
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Navigation Guard: ถ้ายังไม่มี user_id ให้กลับไปหน้า Welcome
router.beforeEach((to, from, next) => {
  const userId = localStorage.getItem('user_id')

  if (to.meta.requiresAuth && !userId) {
    next({ name: 'Welcome' })
  } else if (to.name === 'Welcome' && userId) {
    // ถ้ามี user_id แล้ว ให้ไปหน้า Dashboard เลย
    next({ name: 'Dashboard' })
  } else {
    next()
  }
})

export default router
