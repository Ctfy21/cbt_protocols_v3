<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <h1 class="text-4xl font-bold text-gray-900 mb-4">Система управления фитотроном</h1>
      <p class="text-xl text-gray-600 mb-8">Выберите камеру для начала работы</p>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-4 text-gray-600">Загрузка камер...</p>
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

    <!-- Chambers Grid -->
    <div v-if="chambers.length > 0 && !loading" class="max-w-4xl mx-auto">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div v-for="chamber in chambers" :key="chamber.id" class="relative group">
          <div 
            @click="handleChamberSelect(chamber)"
            :class="[
              'card cursor-pointer transition-all duration-200 transform hover:scale-105',
              selectedChamber?.id === chamber.id ? 'ring-2 ring-primary-500 shadow-lg' : 'hover:shadow-md'
            ]"
          >
            <div class="card-body text-center py-8">
              <!-- Chamber Icon -->
              <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg class="w-8 h-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
              </div>
              
              <!-- Chamber Name -->
              <h3 class="text-xl font-semibold text-gray-900 mb-2">{{ chamber.name }}</h3>
              
              <!-- Chamber Info -->
              <div class="space-y-2 text-sm text-gray-600">
                <div class="flex justify-center items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
                  </svg>
                  <div class="text-center">
                    <div>{{ chamber.sum_sectors?.light?.sectors || 0 }} секторов освещения</div>
                    <div v-if="chamber.sum_sectors?.light?.types?.length" class="text-xs text-gray-500 mt-1">
                      {{ chamber.sum_sectors.light.types.join(', ') }}
                    </div>
                  </div>
                </div>
                <div class="flex justify-center items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10"></path>
                  </svg>
                  {{ chamber.sum_sectors?.watering?.sectors || 0 }} секторов полива
                </div>
                <div class="flex justify-center items-center">
                  <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                  Создана {{ formatDate(chamber.created_at) }}
                </div>
              </div>
              
              <!-- Selection Indicator -->
              <div v-if="selectedChamber?.id === chamber.id" class="mt-4">
                <div class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800">
                  <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  Выбрана
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Cards -->
    <div v-if="hasSelectedChamber && !loading" class="max-w-4xl mx-auto">
      <div class="text-center mb-8">
        <h2 class="text-2xl font-bold text-gray-900 mb-2">Рабочие разделы</h2>
        <p class="text-gray-600">Выберите раздел для работы с камерой "{{ selectedChamber?.name }}"</p>
      </div>
      
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <!-- Scenarios Card -->
        <router-link 
          to="/scenarios" 
          class="card hover:shadow-lg transition-shadow duration-200 transform hover:scale-105"
        >
          <div class="card-body text-center py-8">
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v18m0 0l-4-4m4 4l4-4M3 12h18"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">Библиотека сценариев</h3>
            <p class="text-gray-600 mb-4">Создание и управление 24-часовыми циклами выращивания</p>
            <div class="inline-flex items-center text-green-600 font-medium">
              Перейти
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </div>
          </div>
        </router-link>

        <!-- Schedules Card -->
        <router-link 
          to="/schedules" 
          class="card hover:shadow-lg transition-shadow duration-200 transform hover:scale-105"
        >
          <div class="card-body text-center py-8">
            <div class="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg class="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
              </svg>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-2">Планировщик экспериментов</h3>
            <p class="text-gray-600 mb-4">Создание и управление расписаниями научных экспериментов</p>
            <div class="inline-flex items-center text-blue-600 font-medium">
              Перейти
              <svg class="w-4 h-4 ml-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
              </svg>
            </div>
          </div>
        </router-link>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="chambers.length === 0 && !loading && !error" class="card">
      <div class="card-body text-center py-12">
        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Камеры не найдены</h3>
        <p class="text-gray-600 mb-4">Не удалось найти доступные камеры в системе</p>
        <button class="btn-primary" @click="refreshChambers">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Обновить
        </button>
      </div>
    </div>

    <!-- System Status -->
    <div v-if="!loading" class="max-w-2xl mx-auto">
      <div class="bg-gray-50 rounded-lg p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="w-3 h-3 bg-green-500 rounded-full mr-3 animate-pulse"></div>
            <span class="text-sm font-medium text-gray-700">Система работает</span>
          </div>
          <div class="text-xs text-gray-500">
            Камер доступно: {{ chambersCount }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useChambers } from '../composables/useChambers'

// Use chambers composable
const { 
  chambers, 
  selectedChamber, 
  loading, 
  error, 
  chambersCount,
  hasSelectedChamber,
  fetchChambers, 
  selectChamber,
  refreshChambers 
} = useChambers()

// Methods
const handleChamberSelect = (chamber: any) => {
  selectChamber(chamber)
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleDateString('ru-RU')
}

// Load chambers on mount
onMounted(() => {
  fetchChambers()
})
</script>

<style scoped>
.card:hover {
  transform: translateY(-2px);
}

.router-link-active .card {
  border-color: #3b82f6;
}
</style> 