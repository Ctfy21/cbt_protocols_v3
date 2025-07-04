<template>
  <div id="app" class="flex h-screen bg-gray-50">
    <!-- Sidebar -->
    <div class="w-64 bg-white shadow-lg">
      <div class="p-4 border-b border-gray-200">
        <h1 class="text-xl font-bold text-gray-900">Фитотрон</h1>
        <p class="text-sm text-gray-500">Система управления</p>
      </div>
      
      <nav class="mt-6">
        <div class="px-3">
          <router-link
            to="/chambers"
            class="sidebar-link"
            :class="$route.name === 'Chambers' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
            </svg>
            Камеры
          </router-link>
          
          <router-link
            to="/scenarios"
            class="sidebar-link"
            :class="$route.name === 'Scenarios' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
            </svg>
            Сценарии
          </router-link>
          
          <router-link
            to="/schedules"
            class="sidebar-link"
            :class="$route.name === 'Schedules' ? 'sidebar-link-active' : 'sidebar-link-inactive'"
          >
            <svg class="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
            </svg>
            Расписания
          </router-link>
        </div>
      </nav>
      
      <!-- System Status -->
      <div class="absolute bottom-0 w-64 p-4 border-t border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="w-2 h-2 bg-success-500 rounded-full mr-2"></div>
            <span class="text-sm text-gray-600">API подключен</span>
          </div>
          <span class="text-xs text-gray-400">{{ currentTime }}</span>
        </div>
      </div>
    </div>
    
    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <!-- Header -->
      <header class="bg-white shadow-sm border-b border-gray-200">
        <div class="px-6 py-4">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-semibold text-gray-900">{{ pageTitle }}</h2>
            <div class="flex items-center space-x-4">
              <div class="text-sm text-gray-500">
                Пользователь: <span class="font-medium">Администратор</span>
              </div>
              <button class="btn-outline">
                Выйти
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
import { useRoute } from 'vue-router'

const route = useRoute()
const currentTime = ref('')

const pageTitle = computed(() => {
  const titles: { [key: string]: string } = {
    'Chambers': 'Управление камерами',
    'Scenarios': 'Сценарии',
    'Schedules': 'Расписания'
  }
  return titles[route.name as string] || 'Фитотрон'
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('ru-RU', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
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
