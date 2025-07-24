import { ref, computed } from 'vue'

// Types - updated to match backend models
interface EnvironmentControlSettings {
  sectors: number
  types?: string[]
}

interface EnvironmentParameters {
  temperature?: EnvironmentControlSettings
  humidity?: EnvironmentControlSettings
  co2?: EnvironmentControlSettings
  light?: EnvironmentControlSettings
  watering?: EnvironmentControlSettings
}

interface DefineController {
  controller_name: string
  settings: EnvironmentParameters
}

interface Chamber {
  id: string
  name: string
  is_active: boolean
  controllers: DefineController[]
  sum_sectors: EnvironmentParameters
  created_at: number
  updated_at: number
}

// Global state
const chambers = ref<Chamber[]>([])
const selectedChamber = ref<Chamber | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

// Storage key for persisting selected chamber
const STORAGE_KEY = 'selected_chamber'

// API base URL
const API_BASE = 'http://localhost:8000'

// Composable function
export function useChambers() {
  // Computed properties
  const chambersCount = computed(() => chambers.value.length)
  const activeChambers = computed(() => chambers.value.filter(chamber => chamber.id))
  const availableChambers = computed(() => chambers.value)
  
  // Check if chamber is selected
  const hasSelectedChamber = computed(() => selectedChamber.value !== null)

  // Get sectors count from selected chamber
  const lightSectorsCount = computed(() => selectedChamber.value?.sum_sectors?.light?.sectors || 0)
  const wateringSectorsCount = computed(() => selectedChamber.value?.sum_sectors?.watering?.sectors || 0)
  const temperatureSectorsCount = computed(() => selectedChamber.value?.sum_sectors?.temperature?.sectors || 0)
  const humiditySectorsCount = computed(() => selectedChamber.value?.sum_sectors?.humidity?.sectors || 0)
  const co2SectorsCount = computed(() => selectedChamber.value?.sum_sectors?.co2?.sectors || 0)

  // Get types from selected chamber
  const lightTypes = computed(() => selectedChamber.value?.sum_sectors?.light?.types || [])
  const wateringTypes = computed(() => selectedChamber.value?.sum_sectors?.watering?.types || [])
  const temperatureTypes = computed(() => selectedChamber.value?.sum_sectors?.temperature?.types || [])
  const humidityTypes = computed(() => selectedChamber.value?.sum_sectors?.humidity?.types || [])
  const co2Types = computed(() => selectedChamber.value?.sum_sectors?.co2?.types || [])

  // Helper functions for persistence
  const saveSelectedChamber = (chamber: Chamber | null) => {
    try {
      if (chamber) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chamber))
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch (error) {
      console.warn('Failed to save selected chamber to localStorage:', error)
    }
  }

  const loadSelectedChamber = (): Chamber | null => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY)
      if (saved) {
        return JSON.parse(saved)
      }
    } catch (error) {
      console.warn('Failed to load selected chamber from localStorage:', error)
      localStorage.removeItem(STORAGE_KEY)
    }
    return null
  }

  // Initialize selected chamber from localStorage
  const initializeSelectedChamber = () => {
    const savedChamber = loadSelectedChamber()
    if (savedChamber) {
      selectedChamber.value = savedChamber
    }
  }

  // Methods
  const fetchChambers = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await fetch(`${API_BASE}/chamber`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      // Transform single chamber to array and normalize id
      const chamber = data._id ? { ...data, id: data._id } : data
      
      // Ensure chamber has sum_sectors with default values
      if (!chamber.sum_sectors) {
        chamber.sum_sectors = {
          temperature: { sectors: 1 },
          humidity: { sectors: 1 },
          co2: { sectors: 1 },
          light: { sectors: 1 },
          watering: { sectors: 1 }
        }
      }
      
      chambers.value = [chamber]
      
      // Restore selected chamber from localStorage or auto-select first chamber
      const savedChamber = loadSelectedChamber()
      if (savedChamber) {
        // Verify that the saved chamber still exists and update it with fresh data
        const freshChamber = chambers.value.find(c => c.id === savedChamber.id)
        if (freshChamber) {
          selectedChamber.value = freshChamber
          saveSelectedChamber(freshChamber) // Update saved data with fresh data
        } else {
          // Saved chamber no longer exists, clear it
          clearSelection()
        }
      } else if (!selectedChamber.value && chambers.value.length > 0) {
        // No saved chamber and no current selection, auto-select first chamber
        // selectChamber(chambers.value[0])
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : 'Ошибка загрузки камер'
      console.error('Error fetching chambers:', err)
    } finally {
      loading.value = false
    }
  }

  const getChamberById = (id: string): Chamber | undefined => {
    return chambers.value.find(chamber => chamber.id === id)
  }

  const getChamberName = (id: string | null): string => {
    if (!id) return 'Не назначена'
    const chamber = getChamberById(id)
    return chamber?.name || 'Неизвестная камера'
  }

  const selectChamber = (chamber: Chamber) => {
    selectedChamber.value = chamber
    saveSelectedChamber(chamber)
  }

  const clearSelection = () => {
    selectedChamber.value = null
    saveSelectedChamber(null)
  }

  const refreshChambers = async () => {
    await fetchChambers()
  }

  // Initialize selected chamber from localStorage on first call
  if (!selectedChamber.value) {
    initializeSelectedChamber()
  }

  // Return reactive state and methods
  return {
    // State
    chambers: computed(() => chambers.value),
    selectedChamber: computed(() => selectedChamber.value),
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    
    // Computed
    chambersCount,
    activeChambers,
    availableChambers,
    hasSelectedChamber,
    
    // Sectors counts
    lightSectorsCount,
    wateringSectorsCount,
    temperatureSectorsCount,
    humiditySectorsCount,
    co2SectorsCount,
    
    // Types
    lightTypes,
    wateringTypes,
    temperatureTypes,
    humidityTypes,
    co2Types,
    
    // Methods
    fetchChambers,
    getChamberById,
    getChamberName,
    selectChamber,
    clearSelection,
    refreshChambers,
    initializeSelectedChamber
  }
} 