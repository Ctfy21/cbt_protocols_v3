import { ref, computed, onMounted, onUnmounted } from 'vue'

// Types
interface SensorReading {
  sensor_id: string
  sensor_type: 'temperature' | 'humidity' | 'co2' | 'light' | 'ph' | 'water_level'
  name: string
  value: number
  unit: string
  sector_id?: string
  timestamp: number
  status: 'online' | 'offline' | 'error'
}

interface SwitchState {
  switch_id: string
  switch_type: 'light' | 'pump' | 'fan' | 'heater' | 'cooler' | 'valve'
  name: string
  state: boolean
  sector_id?: string
  auto_mode: boolean
  timestamp: number
}

interface MideaDevice {
  device_id: string
  name: string
  ip_address: string
  status: 'online' | 'offline'
  last_seen: number
  climate: Climate
}

interface ESPHomeDevice {
  device_id: string
  name: string
  ip_address: string
  status: 'online' | 'offline'
  last_seen: number
  sensors: SensorReading[]
  switches: SwitchState[]
}

interface Climate {
  indoor_temperature: number
  outdoor_temperature: number
  target_temperature: number
  fan_speed: number
  mode: 'off' | 'cool' | 'dry' | 'auto' | 'heat'
}

interface CurrentStep {
  step_id?: string
  schedule_name?: string
  scenario_name?: string
  temperature?: number
  humidity?: number
  co2?: number
  light_sectors?: number[]
  relative_start_time?: number
  time_remaining?: number
  is_active: boolean
}

interface DashboardState {
  chamber_id: string
  esp_devices: ESPHomeDevice[]
  midea_devices: MideaDevice[]
  current_step?: CurrentStep
  last_update: number
  auto_mode: boolean
}

// Global state
const dashboardState = ref<DashboardState | null>(null)
const isConnected = ref(false)
const error = ref<string | null>(null)
const loading = ref(false)

// EventSource connection
let eventSource: EventSource | null = null

// API base URL
const API_BASE = 'http://localhost:8000'

export function useDashboard() {
  // Computed properties
  const allSensors = computed(() => {
    if (!dashboardState.value) return []
    return dashboardState.value.esp_devices.flatMap(device => 
      device.sensors.map(sensor => ({ ...sensor, device_name: device.name }))
    )
  })

  const allSwitches = computed(() => {
    if (!dashboardState.value) return []
    return dashboardState.value.esp_devices.flatMap(device => 
      device.switches.map(switch_ => ({ ...switch_, device_name: device.name }))
    )
  })

  const allMideaDevices = computed(() => {
    if (!dashboardState.value) return []
    return dashboardState.value.midea_devices.map(device => ({ ...device, device_name: device.name }))
  })

  const onlineDevices = computed(() => {
    if (!dashboardState.value) return []
    return dashboardState.value.esp_devices.filter(device => device.status === 'online')
  })

  const offlineDevices = computed(() => {
    if (!dashboardState.value) return []
    return dashboardState.value.esp_devices.filter(device => device.status === 'offline')
  })

  const getSensorsByType = (type: string) => {
    return allSensors.value.filter(sensor => sensor.sensor_type === type)
  }

  const getSwitchesByType = (type: string) => {
    return allSwitches.value.filter(switch_ => switch_.switch_type === type)
  }

  // Connection management
  const connectToStream = (chamberId: string) => {
    if (eventSource) {
      eventSource.close()
    }

    try {
      eventSource = new EventSource(`${API_BASE}/dashboard/${chamberId}/stream`)
      
      eventSource.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('Dashboard stream connected')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          dashboardState.value = data
          error.value = null
        } catch (err) {
          console.error('Error parsing dashboard data:', err)
          error.value = 'Ошибка парсинга данных'
        }
      }

      eventSource.onerror = (event) => {
        console.error('Dashboard stream error:', event)
        isConnected.value = false
        error.value = 'Ошибка соединения с сервером'
        
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (!isConnected.value) {
            connectToStream(chamberId)
          }
        }, 5000)
      }
    } catch (err) {
      console.error('Error creating EventSource:', err)
      error.value = 'Не удалось подключиться к серверу'
    }
  }

  const disconnect = () => {
    if (eventSource) {
      eventSource.close()
      eventSource = null
    }
    isConnected.value = false
    dashboardState.value = null
  }

  // API methods
  const fetchInitialState = async (chamberId: string) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`${API_BASE}/dashboard/${chamberId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      dashboardState.value = data
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка загрузки состояния'
      console.error('Error fetching dashboard state:', err)
    } finally {
      loading.value = false
    }
  }

  const toggleSwitch = async (chamberId: string, switchId: string, state: boolean, autoMode?: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/dashboard/${chamberId}/switches/${switchId}/toggle`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          switch_id: switchId,
          state: state,
          auto_mode: autoMode
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка переключения'
      console.error('Error toggling switch:', err)
      throw err
    }
  }

  const toggleAutoMode = async (chamberId: string, autoMode: boolean) => {
    try {
      const response = await fetch(`${API_BASE}/dashboard/${chamberId}/auto-mode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(autoMode),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка переключения автоматического режима'
      console.error('Error toggling auto mode:', err)
      throw err
    }
  }

  // Climate control API methods
  const setMideaTemperature = async (deviceId: string, temperature: number) => {
    try {
      const response = await fetch(`${API_BASE}/midea/devices/${deviceId}/set_temperature?temperature=${temperature}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка установки температуры'
      console.error('Error setting temperature:', err)
      throw err
    }
  }

  const setMideaFanSpeed = async (deviceId: string, fanSpeed: number) => {
    try {
      const response = await fetch(`${API_BASE}/midea/devices/${deviceId}/set_fan_speed?fan_speed=${fanSpeed}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка установки скорости вентилятора'
      console.error('Error setting fan speed:', err)
      throw err
    }
  }

  const setMideaMode = async (deviceId: string, mode: number) => {
    try {
      const response = await fetch(`${API_BASE}/midea/devices/${deviceId}/set_mode?mode=${mode}`, {
        method: 'POST',
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка установки режима'
      console.error('Error setting mode:', err)
      throw err
    }
  }

  // Utility methods
  const getSensorIcon = (sensorType: string) => {
    const icons = {
      temperature: '🌡️',
      humidity: '💧',
      co2: '🫧',
      light: '💡',
      ph: '⚗️',
      water_level: '📊'
    }
    return icons[sensorType as keyof typeof icons] || '📊'
  }

  const getSwitchIcon = (switchType: string) => {
    const icons = {
      light: '💡',
      pump: '⚙️',
      fan: '🌀',
      heater: '🔥',
      cooler: '❄️',
      valve: '🚰'
    }
    return icons[switchType as keyof typeof icons] || '🔌'
  }

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString('ru-RU')
  }

  const getSensorStatus = (sensor: SensorReading) => {
    const now = Date.now() / 1000
    const age = now - sensor.timestamp
    
    if (sensor.status === 'offline') return 'offline'
    if (sensor.status === 'error') return 'error'
    if (age > 60) return 'stale' // Data older than 1 minute
    return 'online'
  }

  const formatTimeRemaining = (seconds?: number) => {
    if (!seconds || seconds <= 0) return 'N/A'
    
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}ч ${minutes}м ${secs}с`
    } else if (minutes > 0) {
      return `${minutes}м ${secs}с`
    } else {
      return `${secs}с`
    }
  }

  const formatLightSectors = (lightSectors?: number[]) => {
    if (!lightSectors || lightSectors.length === 0) return 'N/A'
    return lightSectors.map((intensity, index) => `S${index + 1}: ${intensity}%`).join(', ')
  }

  // Initialize dashboard
  const initializeDashboard = async (chamberId: string) => {
    await fetchInitialState(chamberId)
    connectToStream(chamberId)
  }

  // Cleanup
  onUnmounted(() => {
    disconnect()
  })

  return {
    // State
    dashboardState: computed(() => dashboardState.value),
    isConnected: computed(() => isConnected.value),
    error: computed(() => error.value),
    loading: computed(() => loading.value),

    // Computed
    allSensors,
    allSwitches,  
    onlineDevices,
    offlineDevices,
    allMideaDevices,
    // Methods
    initializeDashboard,
    disconnect,
    toggleSwitch,
    toggleAutoMode,
    getSensorsByType,
    getSwitchesByType,
    getSensorIcon,
    getSwitchIcon,
    formatTimestamp,
    getSensorStatus,
    formatTimeRemaining,
    formatLightSectors,
    connectToStream,
    fetchInitialState,
    // Climate control methods
    setMideaTemperature,
    setMideaFanSpeed,
    setMideaMode
  }
} 