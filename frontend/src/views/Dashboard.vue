<template>
  <div class="space-y-4">
    <!-- Dashboard Header -->
    <div class="bg-white rounded-lg shadow-sm p-4">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="text-xl font-bold text-gray-900">Панель управления</h1>
          <p class="text-sm text-gray-600">Мониторинг и управление системами</p>
        </div>
        <div class="flex items-center space-x-4">
          <!-- Connection Status -->
          <div class="flex items-center space-x-2">
            <div :class="connectionStatusClass"></div>
            <span class="text-xs text-gray-600">{{ connectionStatusText }}</span>
          </div>
          
          <!-- Auto Mode Toggle -->
          <div class="flex items-center space-x-2">
            <span class="text-xs text-gray-700">Авто</span>
            <button
              @click="handleAutoModeToggle"
              :class="autoModeButtonClass"
              :disabled="!dashboardState"
            >
              <div :class="autoModeIndicatorClass"></div>
            </button>
          </div>
          
          <!-- Last Update -->
          <div class="text-xs text-gray-500">
            {{ lastUpdateTime }}
          </div>
        </div>
      </div>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="bg-red-50 border border-red-200 rounded-lg p-3">
      <div class="flex items-center">
        <svg class="w-4 h-4 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
        </svg>
        <span class="text-sm">{{ error }}</span>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading && !dashboardState" class="flex items-center justify-center py-8">
      <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-400"></div>
      <span class="ml-2 text-sm text-gray-600">Загрузка...</span>
    </div>

    <!-- Dashboard Content -->
    <div v-else-if="dashboardState" class="space-y-4">
      <!-- Sensors Section -->
      <div class="bg-white rounded-lg shadow-sm p-4">
        <h2 class="text-base font-medium text-gray-900 mb-3">Датчики</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-3">
          <!-- Temperature Sensors -->
          <div v-for="sensor in temperatureSensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">🌡️</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}°C</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>

          <!-- Humidity Sensors -->
          <div v-for="sensor in humiditySensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">💧</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}%</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>

          <!-- CO2 Sensors -->
          <div v-for="sensor in co2Sensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">🫧</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}ppm</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>

          <!-- Light Sensors -->
          <div v-for="sensor in lightSensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">💡</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>

          <!-- pH Sensors -->
          <div v-for="sensor in phSensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">⚗️</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>

          <!-- Water Level Sensors -->
          <div v-for="sensor in waterLevelSensors" :key="sensor.sensor_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">📊</span>
              <div :class="sensorStatusClass(sensor)"></div>
            </div>
            <div class="mb-2">
              <div class="text-lg font-semibold text-gray-900">{{ sensor.value }}</div>
              <div class="text-xs text-gray-500">{{ sensor.name }}</div>
            </div>
            <div class="text-xs text-gray-400">
              {{ sensor.device_name }}
            </div>
          </div>
        </div>
      </div>

      <!-- Switches Section -->
      <div class="bg-white rounded-lg shadow-sm p-4">
        <h2 class="text-base font-medium text-gray-900 mb-3">Управление</h2>
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
          <div v-for="switch_ in allSwitches" :key="switch_.switch_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <span class="text-lg">{{ getSwitchIcon(switch_.switch_type) }}</span>
              <div class="flex items-center space-x-1">
                <span v-if="switch_.auto_mode" class="px-1.5 py-0.5 text-xs rounded bg-blue-100 text-blue-700">A</span>
              </div>
            </div>
            
            <div class="mb-2">
              <div class="text-sm font-medium text-gray-900">{{ switch_.name }}</div>
              <div class="text-xs text-gray-500">{{ switch_.device_name }}</div>
            </div>
            
            <div class="flex space-x-1">
              <button
                @click="handleSwitchToggle(switch_, !switch_.state)"
                :class="switchButtonClass(switch_.state)"
                :disabled="switch_.auto_mode && dashboardState?.auto_mode"
                class="flex-1 px-2 py-1 text-xs rounded transition-colors"
              >
                {{ switch_.state ? 'ВКЛ' : 'ВЫКЛ' }}
              </button>
              
              <button
                @click="handleSwitchModeToggle(switch_, !switch_.auto_mode)"
                :class="autoModeToggleClass(switch_.auto_mode)"
                class="px-2 py-1 text-xs rounded transition-colors"
                title="Режим"
              >
                {{ switch_.auto_mode ? 'A' : 'M' }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Devices Status Section -->
      <div class="bg-white rounded-lg shadow-sm p-4">
        <h2 class="text-base font-medium text-gray-900 mb-3">Устройства</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          <div v-for="device in dashboardState.esp_devices" :key="device.device_id" 
               class="bg-gray-50 border border-gray-200 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center">
                <div :class="deviceStatusClass(device.status)"></div>
                <span class="ml-2 text-sm font-medium text-gray-900">{{ device.name }}</span>
              </div>
              <span class="text-xs text-gray-500">{{ device.status === 'online' ? 'Онлайн' : 'Офлайн' }}</span>
            </div>
            
            <div class="flex justify-between text-xs text-gray-500">
              <span>Датчики: {{ device.sensors.length }}</span>
              <span>Переключатели: {{ device.switches.length }}</span>
            </div>
            
            <div class="text-xs text-gray-400 mt-1">
              {{ device.ip_address }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- No Chamber Selected -->
    <div v-else-if="!hasSelectedChamber" class="bg-white rounded-lg shadow-sm p-8">
      <div class="text-center">
        <svg class="mx-auto h-8 w-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">Камера не выбрана</h3>
        <p class="mt-1 text-xs text-gray-500">Выберите камеру для просмотра панели управления</p>
        <div class="mt-4">
          <button @click="$router.push('/')" class="btn-primary">
            Выбрать камеру
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onUnmounted, watch } from 'vue'
import { useChambers } from '../composables/useChambers'
import { useDashboard } from '../composables/useDashboard'

// Composables
const { selectedChamber, hasSelectedChamber } = useChambers()
const {
  dashboardState,
  isConnected,
  error,
  loading,
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
  'bg-green-500': isConnected.value,
  'bg-red-500': !isConnected.value && !loading.value,
  'bg-gray-400': loading.value
}))

const connectionStatusText = computed(() => {
  if (loading.value) return 'Подключение...'
  if (isConnected.value) return 'Подключено'
  return 'Отключено'
})

// Auto mode toggle
const autoModeButtonClass = computed(() => ({
  'relative inline-flex h-5 w-9 items-center rounded-full transition-colors': true,
  'bg-blue-500': dashboardState.value?.auto_mode,
  'bg-gray-300': !dashboardState.value?.auto_mode,
  'opacity-50 cursor-not-allowed': !dashboardState.value
}))

const autoModeIndicatorClass = computed(() => ({
  'inline-block h-3 w-3 transform rounded-full bg-white transition-transform': true,
  'translate-x-5': dashboardState.value?.auto_mode,
  'translate-x-1': !dashboardState.value?.auto_mode
}))

// Last update time
const lastUpdateTime = computed(() => {
  if (!dashboardState.value) return 'Нет данных'
  return formatTimestamp(dashboardState.value.last_update)
})

// Sensor status classes
const sensorStatusClass = (sensor: any) => ({
  'w-2 h-2 rounded-full': true,
  'bg-green-500': getSensorStatus(sensor) === 'online',
  'bg-red-500': getSensorStatus(sensor) === 'offline' || getSensorStatus(sensor) === 'error',
  'bg-gray-400': getSensorStatus(sensor) === 'stale'
})


const switchButtonClass = (state: boolean) => ({
  'bg-gray-200 text-gray-700 hover:bg-gray-300': !state,
  'bg-blue-500 text-white hover:bg-blue-600': state
})

const autoModeToggleClass = (autoMode: boolean) => ({
  'bg-blue-100 text-blue-700 hover:bg-blue-200': autoMode,
  'bg-gray-200 text-gray-600 hover:bg-gray-300': !autoMode
})

// Device status
const deviceStatusClass = (status: string) => ({
  'w-2 h-2 rounded-full': true,
  'bg-green-500': status === 'online',
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