import { createRouter, createWebHistory } from 'vue-router'
import Chambers from '../views/Chambers.vue'
import Scenarios from '../views/Scenarios.vue'
import Schedules from '../views/Schedules.vue'

const routes = [
  {
    path: '/',
    name: 'Chambers',
    component: Chambers
  },
  {
    path: '/scenarios',
    name: 'Scenarios',
    component: Scenarios
  },
  {
    path: '/schedules',
    name: 'Schedules',
    component: Schedules
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

export default router 