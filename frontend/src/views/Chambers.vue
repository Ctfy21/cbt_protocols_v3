<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Управление камерами</h2>
        <p class="text-gray-600">Просмотр и управление камерами системы</p>
      </div>
      <button class="btn-primary" @click="refreshData">
        <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
        </svg>
        Обновить
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка данных...</p>
      </div>
    </div>

    <!-- Error State -->
    <div v-if="error" class="card">
      <div class="card-body">
        <div class="bg-danger-50 border border-danger-200 rounded-lg p-4">
          <div class="flex items-center">
            <svg class="w-5 h-5 text-danger-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
            <span class="text-danger-800">Ошибка загрузки: {{ error }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Chamber Info -->
    <div v-if="chamber && !loading" class="card">
      <div class="card-header">
        <h3 class="text-lg font-medium text-gray-900">{{ chamber.name }}</h3>
        <span class="status-online">Активна</span>
      </div>
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 class="font-medium text-gray-900 mb-3">Информация о камере</h4>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">ID:</span>
                <span class="text-sm font-medium">{{ chamber.id }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">Название:</span>
                <span class="text-sm font-medium">{{ chamber.name }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">Создана:</span>
                <span class="text-sm font-medium">{{ formatDate(chamber.created_at) }}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">Обновлена:</span>
                <span class="text-sm font-medium">{{ formatDate(chamber.updated_at) }}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 class="font-medium text-gray-900 mb-3">Статус системы</h4>
            <div class="space-y-2">
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">Подключение к API:</span>
                <span class="status-online">Активно</span>
              </div>
              <div class="flex justify-between">
                <span class="text-sm text-gray-600">Последняя синхронизация:</span>
                <span class="text-sm font-medium">{{ formatDate(Date.now() / 1000) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- API Status -->
    <div class="card">
      <div class="card-header">
        <h3 class="text-lg font-medium text-gray-900">Состояние API</h3>
      </div>
      <div class="card-body">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="text-center">
            <div class="text-2xl font-bold text-primary-600">{{ apiStats.chambers }}</div>
            <div class="text-sm text-gray-600">Камер</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-success-600">{{ apiStats.schedules }}</div>
            <div class="text-sm text-gray-600">Расписаний</div>
          </div>
          <div class="text-center">
            <div class="text-2xl font-bold text-warning-600">{{ apiStats.scenarios }}</div>
            <div class="text-sm text-gray-600">Сценариев</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive data
const chamber = ref<any>(null)
const loading = ref(false)
const error = ref<string | null>(null)
const apiStats = ref({
  chambers: 0,
  schedules: 0,
  scenarios: 0
})

// API base URL
const API_BASE = 'http://localhost:8000'

// Methods
const fetchChamber = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch(`${API_BASE}/chamber`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    chamber.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Неизвестная ошибка'
    console.error('Error fetching chamber:', err)
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const [chambersRes, schedulesRes, scenariosRes] = await Promise.all([
      fetch(`${API_BASE}/chamber`),
      fetch(`${API_BASE}/schedules`),
      fetch(`${API_BASE}/scenarios`)
    ])
    
    if (chambersRes.ok) {
      apiStats.value.chambers = 1 // Single chamber endpoint
    }
    
    if (schedulesRes.ok) {
      const schedules = await schedulesRes.json()
      apiStats.value.schedules = schedules.length
    }
    
    if (scenariosRes.ok) {
      const scenarios = await scenariosRes.json()
      apiStats.value.scenarios = scenarios.length
    }
  } catch (err) {
    console.error('Error fetching stats:', err)
  }
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('ru-RU')
}

const refreshData = async () => {
  await Promise.all([
    fetchChamber(),
    fetchStats()
  ])
}

onMounted(() => {
  refreshData()
})
</script> 