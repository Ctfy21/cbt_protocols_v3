<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Расписания</h2>
        <p class="text-gray-600">Управление расписаниями для камер</p>
      </div>
      <div class="flex space-x-3">
        <button class="btn-outline" @click="refreshData">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Обновить
        </button>
        <button class="btn-primary" @click="showCreateModal = true">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Создать расписание
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка расписаний...</p>
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

    <!-- Schedules Grid -->
    <div v-if="schedules.length > 0 && !loading" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-for="schedule in schedules" :key="schedule.id" class="card">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-lg font-medium text-gray-900">{{ schedule.name }}</h3>
          <div class="flex items-center space-x-2">
            <span :class="getStatusClass(schedule.status)">
              {{ getStatusLabel(schedule.status) }}
            </span>
            <button class="text-primary-600 hover:text-primary-800" @click="viewSchedule(schedule)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="space-y-3">
            <p class="text-sm text-gray-600">{{ schedule.description }}</p>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-500">Сценариев:</span>
                <div class="font-medium">{{ schedule.scenarios.length }}</div>
              </div>
              <div>
                <span class="text-gray-500">Создано:</span>
                <div class="font-medium">{{ formatDate(schedule.created_at) }}</div>
              </div>
            </div>
            <div v-if="schedule.time_start && schedule.time_end" class="border-t pt-3">
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-gray-500">Начало:</span>
                  <span class="font-medium">{{ formatTimestamp(schedule.time_start) }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Конец:</span>
                  <span class="font-medium">{{ formatTimestamp(schedule.time_end) }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Камера:</span>
                  <span class="font-medium">{{ schedule.chamber_id || 'Не назначена' }}</span>
                </div>
                <div>
                  <span class="text-gray-500">Длительность:</span>
                  <span class="font-medium">{{ getDuration(schedule.time_start, schedule.time_end) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="schedules.length === 0 && !loading && !error" class="card">
      <div class="card-body text-center py-8">
        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Нет расписаний</h3>
        <p class="text-gray-600 mb-4">Создайте первое расписание для начала работы</p>
        <button class="btn-primary" @click="showCreateModal = true">
          Создать расписание
        </button>
      </div>
    </div>

    <!-- View Schedule Modal -->
    <div v-if="showViewModal && selectedSchedule" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showViewModal = false">
      <div class="relative top-10 mx-auto p-0 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">{{ selectedSchedule.name }}</h3>
            <button @click="showViewModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 max-h-[80vh] overflow-y-auto">
          <div class="mb-6">
            <p class="text-gray-600">{{ selectedSchedule.description }}</p>
            <div class="grid grid-cols-2 gap-4 mt-4 text-sm">
              <div>
                <span class="text-gray-500">ID:</span>
                <span class="font-medium">{{ selectedSchedule.id }}</span>
              </div>
              <div>
                <span class="text-gray-500">Статус:</span>
                <span :class="getStatusClass(selectedSchedule.status)">
                  {{ getStatusLabel(selectedSchedule.status) }}
                </span>
              </div>
              <div>
                <span class="text-gray-500">Камера:</span>
                <span class="font-medium">{{ selectedSchedule.chamber_id || 'Не назначена' }}</span>
              </div>
              <div>
                <span class="text-gray-500">Сценариев:</span>
                <span class="font-medium">{{ selectedSchedule.scenarios.length }}</span>
              </div>
              <div>
                <span class="text-gray-500">Создано:</span>
                <span class="font-medium">{{ formatDate(selectedSchedule.created_at) }}</span>
              </div>
              <div>
                <span class="text-gray-500">Обновлено:</span>
                <span class="font-medium">{{ formatDate(selectedSchedule.updated_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Scenarios List -->
          <div v-if="selectedSchedule.scenarios.length > 0" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Сценарии в расписании</h4>
            <div class="space-y-2">
              <div v-for="(scenarioId, index) in selectedSchedule.scenarios" :key="scenarioId" 
                   class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div>
                  <div class="font-medium text-gray-900">Сценарий {{ index + 1 }}</div>
                  <div class="text-sm text-gray-500">ID: {{ scenarioId }}</div>
                </div>
                <button class="btn-outline text-xs" @click="viewScenarioDetails(scenarioId)">
                  Подробности
                </button>
              </div>
            </div>
          </div>

          <!-- Timeline -->
          <div v-if="selectedSchedule.time_start && selectedSchedule.time_end" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Временная шкала</h4>
            <div class="bg-gray-50 rounded-lg p-4">
              <div class="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span class="text-gray-500">Начало:</span>
                  <div class="font-medium">{{ formatTimestamp(selectedSchedule.time_start) }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Конец:</span>
                  <div class="font-medium">{{ formatTimestamp(selectedSchedule.time_end) }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Общая длительность:</span>
                  <div class="font-medium">{{ getDuration(selectedSchedule.time_start, selectedSchedule.time_end) }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Осталось:</span>
                  <div class="font-medium">{{ getTimeRemaining(selectedSchedule.time_end) }}</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Schedule Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showCreateModal = false">
      <div class="relative top-20 mx-auto p-5 border w-11/12 max-w-md shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Создать расписание</h3>
          <div class="space-y-4">
            <div class="form-group">
              <label class="form-label">Название</label>
              <input type="text" v-model="newSchedule.name" class="form-input" placeholder="Название расписания">
            </div>
            <div class="form-group">
              <label class="form-label">Описание</label>
              <textarea v-model="newSchedule.description" class="form-input" rows="3" placeholder="Описание расписания"></textarea>
            </div>
            <div class="form-group">
              <label class="form-label">Сценарий</label>
              <select v-model="newSchedule.selectedScenario" class="form-input">
                <option value="">Выберите сценарий</option>
                <option v-for="scenario in availableScenarios" :key="scenario.id" :value="scenario.id">
                  {{ scenario.name }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Камера</label>
              <input type="text" v-model="newSchedule.chamber_id" class="form-input" placeholder="ID камеры (опционально)">
            </div>
            <div class="form-group">
              <label class="form-label">Время начала (Unix timestamp)</label>
              <input type="number" v-model="newSchedule.time_start" class="form-input" placeholder="Время начала">
            </div>
          </div>
          <div class="flex justify-end space-x-3 mt-6">
            <button class="btn-outline" @click="showCreateModal = false">Отмена</button>
            <button class="btn-primary" @click="createSchedule" :disabled="!newSchedule.name">Создать</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Types
interface Schedule {
  id: string
  name: string
  description: string
  status: string
  chamber_id: string | null
  time_start: number | null
  time_end: number | null
  created_at: number
  updated_at: number
  scenarios: string[]
}

interface Scenario {
  id: string
  name: string
  description: string
  created_at: number
  updated_at: number
  parameters: any[]
}

// Reactive data
const schedules = ref<Schedule[]>([])
const availableScenarios = ref<Scenario[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showViewModal = ref(false)
const showCreateModal = ref(false)
const selectedSchedule = ref<Schedule | null>(null)
const newSchedule = ref({
  name: '',
  description: '',
  selectedScenario: '',
  chamber_id: '',
  time_start: null as number | null
})

// API base URL
const API_BASE = 'http://localhost:8000'

// Methods
const fetchSchedules = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch(`${API_BASE}/schedules`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    schedules.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Неизвестная ошибка'
    console.error('Error fetching schedules:', err)
  } finally {
    loading.value = false
  }
}

const fetchScenarios = async () => {
  try {
    const response = await fetch(`${API_BASE}/scenarios`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    availableScenarios.value = data
  } catch (err) {
    console.error('Error fetching scenarios:', err)
  }
}

const createSchedule = async () => {
  try {
    const scheduleData = {
      name: newSchedule.value.name,
      description: newSchedule.value.description,
      scenarios: newSchedule.value.selectedScenario ? [newSchedule.value.selectedScenario] : [],
      time_start: newSchedule.value.time_start || undefined,
      chamber_id: newSchedule.value.chamber_id || undefined
    }
    
    const response = await fetch(`${API_BASE}/schedules`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(scheduleData)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // Reset form
    newSchedule.value = {
      name: '',
      description: '',
      selectedScenario: '',
      chamber_id: '',
      time_start: null
    }
    showCreateModal.value = false
    
    // Refresh data
    await fetchSchedules()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка создания расписания'
    console.error('Error creating schedule:', err)
  }
}

const viewSchedule = (schedule: Schedule) => {
  selectedSchedule.value = schedule
  showViewModal.value = true
}

const viewScenarioDetails = (scenarioId: string) => {
  // TODO: Implement scenario details viewing
  console.log('View scenario details:', scenarioId)
}

const getStatusClass = (status: string | null) => {
  if (!status) return 'status-offline'
  
  const classes = {
    'draft': 'status-offline',
    'ready': 'status-warning',
    'active': 'status-online',
    'completed': 'status-online',
    'cancelled': 'status-offline'
  }
  return classes[status as keyof typeof classes] || 'status-offline'
}

const getStatusLabel = (status: string | null) => {
  if (!status) return 'Неизвестно'
  
  const labels = {
    'draft': 'Черновик',
    'ready': 'Готово',
    'active': 'Активно',
    'completed': 'Завершено',
    'cancelled': 'Отменено'
  }
  return labels[status as keyof typeof labels] || 'Неизвестно'
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('ru-RU')
}

const formatTimestamp = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('ru-RU')
}

const getDuration = (start: number, end: number) => {
  const diffSeconds = end - start
  const days = Math.floor(diffSeconds / 86400)
  const hours = Math.floor((diffSeconds % 86400) / 3600)
  const minutes = Math.floor((diffSeconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}д ${hours}ч ${minutes}м`
  } else if (hours > 0) {
    return `${hours}ч ${minutes}м`
  } else {
    return `${minutes}м`
  }
}

const getTimeRemaining = (endTime: number) => {
  const now = Math.floor(Date.now() / 1000)
  if (endTime <= now) {
    return 'Завершено'
  }
  
  const diffSeconds = endTime - now
  const days = Math.floor(diffSeconds / 86400)
  const hours = Math.floor((diffSeconds % 86400) / 3600)
  const minutes = Math.floor((diffSeconds % 3600) / 60)
  
  if (days > 0) {
    return `${days}д ${hours}ч ${minutes}м`
  } else if (hours > 0) {
    return `${hours}ч ${minutes}м`
  } else {
    return `${minutes}м`
  }
}

const refreshData = async () => {
  await Promise.all([
    fetchSchedules(),
    fetchScenarios()
  ])
}

onMounted(() => {
  refreshData()
})
</script> 