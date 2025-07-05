<template>
  <div id="app" class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="w-64 bg-white shadow-lg">
      <div class="p-4 border-b border-gray-200">
        <h1 class="text-xl font-bold text-gray-900">Фитотрон</h1>
        <p class="text-sm text-gray-500">Система управления</p>
        
        <!-- Selected Chamber Info -->
        <div v-if="selectedChamber" class="mt-3 p-2 bg-primary-50 rounded-lg">
          <div class="flex items-center">
            <svg class="w-4 h-4 text-primary-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
            </svg>
            <div class="flex-1">
              <div class="text-xs font-medium text-primary-700">Активная камера</div>
              <div class="text-sm font-semibold text-primary-900">{{ selectedChamber.name }}</div>
            </div>
            <button @click="goToHome" class="text-primary-600 hover:text-primary-800" title="Сменить камеру">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4"></path>
              </svg>
            </button>
          </div>
        </div>
      </div>
      
      <nav class="mt-6">
        <div class="px-3">
          <router-link
            to="/"
            class="sidebar-link"
            :class="$route.name === 'Chambers' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 9h6v6H9z"></path>
            </svg>
            Выбор камеры
          </router-link>
          
          <!-- Show navigation only if chamber is selected -->
          <template v-if="hasSelectedChamber">
            <div class="mt-4 mb-2 px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Рабочие разделы
            </div>
            
            <router-link
              to="/scenarios"
              class="sidebar-link"
              :class="$route.name === 'Scenarios' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
            >
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v18m0 0l-4-4m4 4l4-4M3 12h18"></path>
              </svg>
              Библиотека сценариев
            </router-link>
            
            <router-link
              to="/schedules"
              class="sidebar-link"
              :class="$route.name === 'Schedules' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
            >
              <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
              Планировщик экспериментов
            </router-link>
          </template>
          
          <!-- Warning if no chamber selected and not on chambers page -->
          <div v-if="!hasSelectedChamber && $route.name !== 'Chambers'" class="mt-4 p-3 bg-warning-50 border border-warning-200 rounded-lg">
            <div class="flex items-center">
              <svg class="w-4 h-4 text-warning-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
              </svg>
              <div class="text-xs text-warning-800">
                <div class="font-medium">Камера не выбрана</div>
                <button @click="goToHome" class="text-warning-700 underline">Выбрать камеру</button>
              </div>
            </div>
          </div>
        </div>
      </nav>
      
      <!-- System Status -->
      <div class="absolute bottom-0 w-64 p-4 border-t border-gray-200">
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="flex items-center">
              <div class="w-2 h-2 bg-success-500 rounded-full mr-2 animate-pulse"></div>
              <span class="text-sm text-gray-600">Система активна</span>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-xs text-gray-400">API v1.0</span>
            <span class="text-xs text-gray-400">{{ currentTime }}</span>
          </div>
          <div v-if="selectedChamber" class="text-xs text-gray-400">
            Камера: {{ selectedChamber.settings?.light_sectors || 0 }}L / {{ selectedChamber.settings?.watering_sectors || 0 }}W
          </div>
        </div>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="bg-white shadow-sm border-b border-gray-200">
        <div class="px-6 py-4">
          <div class="flex items-center justify-between">
            <div>
              <h2 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h2>
              <p class="text-sm text-gray-500">{{ pageDescription }}</p>
            </div>
            <div class="flex items-center space-x-4">
              <div v-if="selectedChamber" class="text-sm text-gray-500">
                Камера: <span class="font-medium">{{ selectedChamber.name }}</span>
              </div>
              <div class="text-sm text-gray-500">
                Исследователь: <span class="font-medium">Администратор</span>
              </div>
              <div class="flex items-center space-x-2">
                <div class="w-2 h-2 bg-green-500 rounded-full"></div>
                <span class="text-sm text-gray-600">Подключено</span>
              </div>
              <button class="btn-outline">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"></path>
                </svg>
                Выход
              </button>
            </div>
          </div>
        </div>
      </header>
      
      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useChambers } from './composables/useChambers'

const route = useRoute()
const router = useRouter()
const currentTime = ref('')

// Use chambers composable
const { selectedChamber, hasSelectedChamber } = useChambers()

const pageTitle = computed(() => {
  const titles: { [key: string]: string } = {
    'Chambers': 'Выбор камеры',
    'Scenarios': 'Библиотека сценариев',
    'Schedules': 'Планировщик экспериментов'
  }
  return titles[route.name as string] || 'Фитотрон'
})

const pageDescription = computed(() => {
  const descriptions: { [key: string]: string } = {
    'Chambers': 'Выберите камеру для начала работы с системой управления',
    'Scenarios': '24-часовые циклы выращивания для научных экспериментов',
    'Schedules': 'Создание и управление расписаниями для научных исследований'
  }
  return descriptions[route.name as string] || 'Система управления'
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const goToHome = () => {
  router.push('/')
}

let timeInterval: ReturnType<typeof setInterval>

onMounted(() => {
  updateTime()
  timeInterval = setInterval(updateTime, 60000) // Update every minute
})

onUnmounted(() => {
  if (timeInterval) {
    clearInterval(timeInterval)
  }
})
</script>

<style scoped>
.logo {
  height: 6em;
  padding: 1.5em;
  will-change: filter;
  transition: filter 300ms;
}
.logo:hover {
  filter: drop-shadow(0 0 2em #646cffaa);
}
.logo.vue:hover {
  filter: drop-shadow(0 0 2em #42b883aa);
}
</style>
