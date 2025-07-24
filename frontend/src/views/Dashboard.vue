<template>
  <div class="space-y-6">
    <!-- Dashboard Header -->
    <div class="bg-white rounded-lg shadow-sm p-6">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold text-gray-900">Панель управления</h1>
          <p class="text-gray-600">Мониторинг и управление системами в реальном времени</p>
        </div>
        <div class="flex items-center space-x-4">
          <!-- Connection Status -->
          <div class="flex items-center space-x-2">
            <div :class="connectionStatusClass"></div>
            <span class="text-sm text-gray-600">{{ connectionStatusText }}</span>
          </div>
          
          <!-- Auto Mode Toggle -->
          <div class="flex items-center space-x-2">
            <label class="text-sm font-medium text-gray-700">Автоматический режим</label>
            <button
              @click="handleAutoModeToggle"
              :class="autoModeButtonClass"
              :disabled="!dashboardState"
            >
              <div :class="autoModeIndicatorClass"></div>
            </button>
          </div>
          
          <!-- Last Update -->
          <div class="text-sm text-gray-500">
            Обновлено: {{ lastUpdateTime }}
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-center">
        <svg class="w-5 h-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <span>{{ error }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !dashboardState" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      <span class="ml-3 text-gray-600">Загрузка данных панели управления...</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else-if="dashboardState" class="space-y-8">
      <!-- Sensors Section -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Датчики</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
          <!-- Temperature Sensors -->
          <div v-for="sensor in temperatureSensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">🌡️</span>
              <div>
                <h3 class="font-medium text-gray-900">Температура</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>

          <!-- Humidity Sensors -->
          <div v-for="sensor in humiditySensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-blue-50 to-cyan-50 border border-blue-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">💧</span>
              <div>
                <h3 class="font-medium text-gray-900">Влажность</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>

          <!-- CO2 Sensors -->
          <div v-for="sensor in co2Sensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-purple-50 to-indigo-50 border border-purple-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">🫧</span>
              <div>
                <h3 class="font-medium text-gray-900">CO₂</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>

          <!-- Light Sensors -->
          <div v-for="sensor in lightSensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">💡</span>
              <div>
                <h3 class="font-medium text-gray-900">Освещение</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>

          <!-- pH Sensors -->
          <div v-for="sensor in phSensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-green-50 to-emerald-50 border border-green-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">⚗️</span>
              <div>
                <h3 class="font-medium text-gray-900">pH</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>

          <!-- Water Level Sensors -->
          <div v-for="sensor in waterLevelSensors" :key="sensor.sensor_id" 
               class="bg-gradient-to-r from-teal-50 to-blue-50 border border-teal-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center justify-between mb-3">
              <span class="text-2xl mr-3">📊</span>
              <div>
                <h3 class="font-medium text-gray-900">Уровень воды</h3>
                <p class="text-xs text-gray-500">{{ sensor.device_name }}</p>
              </div>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="text-center mb-3">
              <span class="text-2xl font-bold text-gray-900">{{ sensor.value }}</span>
              <span class="text-sm text-gray-600 ml-1">{{ sensor.unit }}</span>
            </div>
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(sensor.timestamp) }}</span>
              <span v-if="sensor.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ sensor.sector_id }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Switches Section -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Управление</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="switch_ in allSwitches" :key="switch_.switch_id" 
               class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow">
            <div class="flex items-center mb-4">
              <span class="text-xl mr-3">{{ getSwitchIcon(switch_.switch_type) }}</span>
              <div class="flex-1">
                <h3 class="font-medium text-gray-900">{{ switch_.name }}</h3>
                <p class="text-xs text-gray-500">{{ switch_.device_name }}</p>
              </div>
              <div class="flex items-center">
                <span v-if="switch_.auto_mode" class="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">АВТО</span>
                <span v-else class="px-2 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800">РУЧНОЙ</span>
              </div>
            </div>
            
            <div class="flex items-center justify-between mb-3">
              <div>
                <span :class="switchStateClass(switch_.state)">
                  {{ switch_.state ? 'ВКЛ' : 'ВЫКЛ' }}
                </span>
              </div>
              
              <div class="flex space-x-2">
                <button
                  @click="handleSwitchToggle(switch_, !switch_.state)"
                  :class="switchButtonClass(switch_.state)"
                  :disabled="switch_.auto_mode && dashboardState?.auto_mode"
                  title="Переключить состояние"
                >
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 9l4-4 4 4m0 6l-4 4-4-4"></path>
                  </svg>
                </button>
                
                <button
                  @click="handleSwitchModeToggle(switch_, !switch_.auto_mode)"
                  :class="autoModeToggleClass(switch_.auto_mode)"
                  title="Переключить режим"
                >
                  <svg v-if="switch_.auto_mode" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                  </svg>
                  <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4"></path>
                  </svg>
                </button>
              </div>
            </div>
            
            <div class="flex items-center justify-between text-xs text-gray-500">
              <span>{{ formatTimestamp(switch_.timestamp) }}</span>
              <span v-if="switch_.sector_id" class="bg-gray-100 px-2 py-1 rounded-full">Сектор {{ switch_.sector_id }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Devices Status Section -->
      <div class="bg-white rounded-lg shadow-sm p-6">
        <h2 class="text-lg font-semibold text-gray-900 mb-4">Состояние устройств</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="device in dashboardState.devices" :key="device.device_id" 
               class="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
            <div class="flex items-center mb-3">
              <div :class="deviceStatusClass(device.status)"></div>
              <div class="flex-1 ml-3">
                <h3 class="font-medium text-gray-900">{{ device.name }}</h3>
                <p class="text-xs text-gray-500">{{ device.ip_address }}</p>
              </div>
              <span class="text-sm font-medium text-gray-700">{{ device.status === 'online' ? 'Онлайн' : 'Офлайн' }}</span>
            </div>
            
            <div class="flex justify-between mb-3">
              <div class="text-center">
                <span class="block text-xs text-gray-500">Датчики:</span>
                <span class="block text-lg font-semibold text-gray-900">{{ device.sensors.length }}</span>
              </div>
              <div class="text-center">
                <span class="block text-xs text-gray-500">Переключатели:</span>
                <span class="block text-lg font-semibold text-gray-900">{{ device.switches.length }}</span>
              </div>
            </div>
            
            <div class="text-xs text-gray-500">
              <span>Последняя активность: {{ formatTimestamp(device.last_seen) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Chamber Selected -->
    <div v-else-if="!hasSelectedChamber" class="bg-white rounded-lg shadow-sm p-12">
      <div class="text-center">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Камера не выбрана</h3>
        <p class="mt-1 text-sm text-gray-500">Выберите камеру для просмотра панели управления</p>
        <div class="mt-6">
          <button @click="$router.push('/')" class="btn-primary">
            Выбрать камеру
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useChambers } from '../composables/useChambers'
import { useDashboard } from '../composables/useDashboard'

// Composables
const { selectedChamber, hasSelectedChamber } = useChambers()
const {
  dashboardState,
  isConnected,
  error,
  loading,
  allSensors,
  allSwitches,
  initializeDashboard,
  disconnect,
  toggleSwitch,
  toggleAutoMode,
  getSensorsByType,
  getSwitchIcon,
  formatTimestamp,
  getSensorStatus
} = useDashboard()

// Computed properties for sensors by type
const temperatureSensors = computed(() => getSensorsByType('temperature'))
const humiditySensors = computed(() => getSensorsByType('humidity'))
const co2Sensors = computed(() => getSensorsByType('co2'))
const lightSensors = computed(() => getSensorsByType('light'))
const phSensors = computed(() => getSensorsByType('ph'))
const waterLevelSensors = computed(() => getSensorsByType('water_level'))

// Connection status
const connectionStatusClass = computed(() => ({
  'w-2 h-2 rounded-full': true,
  'bg-green-500 animate-pulse': isConnected.value,
  'bg-red-500': !isConnected.value && !loading.value,
  'bg-yellow-500': loading.value
}))

const connectionStatusText = computed(() => {
  if (loading.value) return 'Подключение...'
  if (isConnected.value) return 'Подключено'
  return 'Отключено'
})

// Auto mode toggle
const autoModeButtonClass = computed(() => ({
  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors': true,
  'bg-primary-600': dashboardState.value?.auto_mode,
  'bg-gray-200': !dashboardState.value?.auto_mode,
  'opacity-50 cursor-not-allowed': !dashboardState.value
}))

const autoModeIndicatorClass = computed(() => ({
  'inline-block h-4 w-4 transform rounded-full bg-white transition-transform': true,
  'translate-x-6': dashboardState.value?.auto_mode,
  'translate-x-1': !dashboardState.value?.auto_mode
}))

// Last update time
const lastUpdateTime = computed(() => {
  if (!dashboardState.value) return 'Нет данных'
  return formatTimestamp(dashboardState.value.last_update)
})

// Sensor status classes
const sensorStatusClass = (sensor: any) => ({
  'w-3 h-3 rounded-full': true,
  'bg-green-500': getSensorStatus(sensor) === 'online',
  'bg-red-500': getSensorStatus(sensor) === 'offline' || getSensorStatus(sensor) === 'error',
  'bg-yellow-500': getSensorStatus(sensor) === 'stale'
})

// Switch classes
const switchStateClass = (state: boolean) => ({
  'px-2 py-1 text-xs font-medium rounded-full': true,
  'bg-green-100 text-green-800': state,
  'bg-gray-100 text-gray-800': !state
})

const switchButtonClass = (state: boolean) => ({
  'p-2 rounded-lg transition-colors': true,
  'bg-red-100 text-red-600 hover:bg-red-200': state,
  'bg-green-100 text-green-600 hover:bg-green-200': !state,
  'opacity-50 cursor-not-allowed': false
})

const autoModeToggleClass = (autoMode: boolean) => ({
  'p-2 rounded-lg transition-colors': true,
  'bg-blue-100 text-blue-600 hover:bg-blue-200': autoMode,
  'bg-gray-100 text-gray-600 hover:bg-gray-200': !autoMode
})

// Device status
const deviceStatusClass = (status: string) => ({
  'w-3 h-3 rounded-full': true,
  'bg-green-500 animate-pulse': status === 'online',
  'bg-red-500': status === 'offline'
})

// Event handlers
const handleAutoModeToggle = async () => {
  if (!selectedChamber.value || !dashboardState.value) return
  
  try {
    await toggleAutoMode(selectedChamber.value.id, !dashboardState.value.auto_mode)
  } catch (error) {
    console.error('Failed to toggle auto mode:', error)
  }
}

const handleSwitchToggle = async (switch_: any, newState: boolean) => {
  if (!selectedChamber.value) return
  
  try {
    await toggleSwitch(selectedChamber.value.id, switch_.switch_id, newState)
  } catch (error) {
    console.error('Failed to toggle switch:', error)
  }
}

const handleSwitchModeToggle = async (switch_: any, newAutoMode: boolean) => {
  if (!selectedChamber.value) return
  
  try {
    await toggleSwitch(selectedChamber.value.id, switch_.switch_id, switch_.state, newAutoMode)
  } catch (error) {
    console.error('Failed to toggle switch mode:', error)
  }
}

// Watch for chamber selection changes
watch(() => selectedChamber.value, (newChamber, oldChamber) => {
  if (newChamber && newChamber.id !== oldChamber?.id) {
    initializeDashboard(newChamber.id)
  } else if (!newChamber) {
    disconnect()
  }
}, { immediate: true })

// Cleanup on unmount
onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
/* Minimal scoped styles - most styling is done with Tailwind classes */
</style> 