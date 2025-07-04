<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Сценарии</h2>
        <p class="text-gray-600">Управление сценариями с параметрами выращивания</p>
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
          Создать сценарий
        </button>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка сценариев...</p>
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

    <!-- Scenarios Grid -->
    <div v-if="scenarios.length > 0 && !loading" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div v-for="scenario in scenarios" :key="scenario.id" class="card">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-lg font-medium text-gray-900">{{ scenario.name }}</h3>
          <div class="flex space-x-2">
            <button class="text-primary-600 hover:text-primary-800" @click="viewScenario(scenario)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="space-y-3">
            <p class="text-sm text-gray-600">{{ scenario.description }}</p>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-500">Параметров:</span>
                <div class="font-medium">{{ scenario.parameters.length }}</div>
              </div>
              <div>
                <span class="text-gray-500">Создан:</span>
                <div class="font-medium">{{ formatDate(scenario.created_at) }}</div>
              </div>
            </div>
            <div v-if="scenario.parameters.length > 0" class="border-t pt-3">
              <h4 class="text-sm font-medium text-gray-900 mb-2">Пример параметров (первый час):</h4>
              <div class="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span class="text-gray-500">Температура:</span>
                  <span class="font-medium">{{ scenario.parameters[0].temperature }}°C</span>
                </div>
                <div>
                  <span class="text-gray-500">Влажность:</span>
                  <span class="font-medium">{{ scenario.parameters[0].humidity }}%</span>
                </div>
                <div>
                  <span class="text-gray-500">CO₂:</span>
                  <span class="font-medium">{{ scenario.parameters[0].co2_level }} ppm</span>
                </div>
                <div>
                  <span class="text-gray-500">Освещение:</span>
                  <span class="font-medium">{{ scenario.parameters[0].light_sectors.length }} секторов</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="scenarios.length === 0 && !loading && !error" class="card">
      <div class="card-body text-center py-8">
        <svg class="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Нет сценариев</h3>
        <p class="text-gray-600 mb-4">Создайте первый сценарий для начала работы</p>
        <button class="btn-primary" @click="showCreateModal = true">
          Создать сценарий
        </button>
      </div>
    </div>

    <!-- View Scenario Modal -->
    <div v-if="showViewModal && selectedScenario" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showViewModal = false">
      <div class="relative top-10 mx-auto p-0 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
          <div class="flex justify-between items-center">
            <h3 class="text-lg font-medium text-gray-900">{{ selectedScenario.name }}</h3>
            <button @click="showViewModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 max-h-[80vh] overflow-y-auto">
          <div class="mb-6">
            <p class="text-gray-600">{{ selectedScenario.description }}</p>
            <div class="grid grid-cols-2 gap-4 mt-4 text-sm">
              <div>
                <span class="text-gray-500">ID:</span>
                <span class="font-medium">{{ selectedScenario.id }}</span>
              </div>
              <div>
                <span class="text-gray-500">Создан:</span>
                <span class="font-medium">{{ formatDate(selectedScenario.created_at) }}</span>
              </div>
              <div>
                <span class="text-gray-500">Обновлен:</span>
                <span class="font-medium">{{ formatDate(selectedScenario.updated_at) }}</span>
              </div>
              <div>
                <span class="text-gray-500">Всего параметров:</span>
                <span class="font-medium">{{ selectedScenario.parameters.length }}</span>
              </div>
            </div>
          </div>

          <!-- Parameters Table -->
          <div class="overflow-x-auto">
            <table class="min-w-full border border-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase border-r">Час</th>
                  <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Температура (°C)</th>
                  <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Влажность (%)</th>
                  <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">CO₂ (ppm)</th>
                  <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Освещение</th>
                  <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Полив</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="(param, index) in selectedScenario.parameters" :key="index" class="hover:bg-gray-50">
                  <td class="px-3 py-2 font-medium text-gray-900 border-r">{{ index + 1 }}</td>
                  <td class="px-3 py-2 text-center border-r">{{ param.temperature }}</td>
                  <td class="px-3 py-2 text-center border-r">{{ param.humidity }}</td>
                  <td class="px-3 py-2 text-center border-r">{{ param.co2_level }}</td>
                  <td class="px-3 py-2 text-center border-r">
                    <div class="text-xs">
                      <div v-for="light in param.light_sectors" :key="light.sector_id" class="inline-block mr-1">
                        S{{ light.sector_id }}: {{ light.light_intensity }}%
                      </div>
                    </div>
                  </td>
                  <td class="px-3 py-2 text-center">
                    <div class="text-xs">
                      <div v-for="water in param.watering_sectors" :key="water.sector_id" class="inline-block mr-1">
                        S{{ water.sector_id }}: {{ water.watering_duration }}мин
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Scenario Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showCreateModal = false">
      <div class="relative top-20 mx-auto p-5 border w-11/12 max-w-md shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Создать сценарий</h3>
          <div class="space-y-4">
            <div class="form-group">
              <label class="form-label">Название</label>
              <input type="text" v-model="newScenario.name" class="form-input" placeholder="Название сценария">
            </div>
            <div class="form-group">
              <label class="form-label">Описание</label>
              <textarea v-model="newScenario.description" class="form-input" rows="3" placeholder="Описание сценария"></textarea>
            </div>
          </div>
          <div class="flex justify-end space-x-3 mt-6">
            <button class="btn-outline" @click="showCreateModal = false">Отмена</button>
            <button class="btn-primary" @click="createScenario" :disabled="!newScenario.name">Создать</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Types
interface LightSector {
  sector_id: number
  light_intensity: number
}

interface WateringSector {
  sector_id: number
  watering_duration: number
}

interface Parameters {
  temperature: number
  humidity: number
  light_sectors: LightSector[]
  co2_level: number
  watering_sectors: WateringSector[]
}

interface Scenario {
  id: string
  name: string
  description: string
  created_at: number
  updated_at: number
  parameters: Parameters[]
}

// Reactive data
const scenarios = ref<Scenario[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const showViewModal = ref(false)
const showCreateModal = ref(false)
const selectedScenario = ref<Scenario | null>(null)
const newScenario = ref({
  name: '',
  description: ''
})

// API base URL
const API_BASE = 'http://localhost:8000'

// Methods
const fetchScenarios = async () => {
  try {
    loading.value = true
    error.value = null
    
    const response = await fetch(`${API_BASE}/scenarios`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    scenarios.value = data
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Неизвестная ошибка'
    console.error('Error fetching scenarios:', err)
  } finally {
    loading.value = false
  }
}

const createScenario = async () => {
  try {
    const scenarioData = {
      name: newScenario.value.name,
      description: newScenario.value.description,
      parameters: [
        {
          temperature: 22,
          humidity: 65,
          light_sectors: [
            { sector_id: 1, light_intensity: 80 },
            { sector_id: 2, light_intensity: 70 },
            { sector_id: 3, light_intensity: 60 }
          ],
          co2_level: 400,
          watering_sectors: [
            { sector_id: 1, watering_duration: 30 },
            { sector_id: 2, watering_duration: 30 },
            { sector_id: 3, watering_duration: 20 }
          ]
        }
      ]
    }
    
    const response = await fetch(`${API_BASE}/scenarios`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(scenarioData)
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // Reset form
    newScenario.value = { name: '', description: '' }
    showCreateModal.value = false
    
    // Refresh data
    await fetchScenarios()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка создания сценария'
    console.error('Error creating scenario:', err)
  }
}

const viewScenario = (scenario: Scenario) => {
  selectedScenario.value = scenario
  showViewModal.value = true
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('ru-RU')
}

const refreshData = async () => {
  await fetchScenarios()
}

onMounted(() => {
  fetchScenarios()
})
</script> 