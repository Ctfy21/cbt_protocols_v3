<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Планировщик экспериментов</h2>
        <p class="text-gray-600">Создание и управление расписаниями для научных экспериментов</p>
      </div>
      <div class="flex space-x-3">
        <button class="btn-outline" @click="refreshData">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
          </svg>
          Обновить
        </button>
        <button class="btn-primary" @click="openCreateModal">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Создать эксперимент
        </button>
      </div>
    </div>

    <!-- Info Panel -->
    <div class="bg-primary-50 border border-primary-200 rounded-lg p-4">
      <div class="flex items-center">
        <svg class="w-5 h-5 text-primary-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
        </svg>
        <div>
          <p class="text-primary-800 font-medium">О расписаниях экспериментов</p>
          <p class="text-primary-700 text-sm">Создавайте сложные эксперименты, комбинируя различные 24-часовые сценарии. Поддерживаются как повторяющиеся циклы, так и последовательности различных условий.</p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка планировщика...</p>
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
    <div v-if="schedules.length > 0 && !loading" class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
      <div v-for="schedule in schedules" :key="schedule.id" class="card">
        <div class="card-header">
          <div class="flex justify-between items-start">
            <div class="flex-1">
              <h3 class="text-lg font-medium text-gray-900">{{ schedule.name }}</h3>
              <p class="text-sm text-gray-500">Эксперимент {{ getScheduleType(schedule) }}</p>
            </div>
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
              <button class="text-red-600 hover:text-red-800" @click="openDeleteModal(schedule)">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                </svg>
              </button>
            </div>
          </div>
        </div>
        <div class="card-body">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">{{ schedule.description }}</p>
            
            <!-- Schedule Summary -->
            <div class="bg-gray-50 rounded-lg p-3">
              <h4 class="text-sm font-medium text-gray-900 mb-2">Параметры эксперимента</h4>
              <div class="grid grid-cols-2 gap-3 text-sm">
                <div>
                  <span class="text-gray-500">Сценариев:</span>
                  <div class="font-medium">{{ schedule.scenarios.length }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Камера:</span>
                  <div class="font-medium">{{ getChamberName(schedule.chamber_id) }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Длительность:</span>
                  <div class="font-medium">{{ getScheduleDuration(schedule) }}</div>
                </div>
                <div>
                  <span class="text-gray-500">Создан:</span>
                  <div class="font-medium">{{ formatDate(schedule.created_at) }}</div>
                </div>
              </div>
            </div>
            
            <!-- Timeline -->
            <div v-if="schedule.time_start && schedule.time_end" class="space-y-2">
              <h4 class="text-sm font-medium text-gray-900">Временная шкала</h4>
              <div class="bg-gradient-to-r from-blue-100 to-green-100 rounded-lg p-2">
                <div class="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span class="text-gray-600">Начало:</span>
                    <div class="font-medium">{{ formatTimestamp(schedule.time_start) }}</div>
                  </div>
                  <div>
                    <span class="text-gray-600">Конец:</span>
                    <div class="font-medium">{{ formatTimestamp(schedule.time_end) }}</div>
                  </div>
                </div>
                <div class="mt-2">
                  <div class="text-xs text-gray-600">Прогресс:</div>
                  <div class="w-full bg-gray-200 rounded-full h-2 mt-1">
                    <div class="bg-blue-600 h-2 rounded-full" :style="{ width: getProgressPercentage(schedule) + '%' }"></div>
                  </div>
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
        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Нет экспериментов</h3>
        <p class="text-gray-600 mb-4">Создайте первый эксперимент для начала научных исследований</p>
        <button class="btn-primary" @click="openCreateModal">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Создать эксперимент
        </button>
      </div>
    </div>

    <!-- View Schedule Modal -->
    <div v-if="showViewModal && selectedSchedule" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showViewModal = false">
      <div class="relative top-10 mx-auto p-0 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-medium text-gray-900">{{ selectedSchedule.name }}</h3>
              <p class="text-sm text-gray-500">{{ getScheduleType(selectedSchedule) }} эксперимент</p>
            </div>
            <button @click="showViewModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
        </div>
        
        <div class="p-6 max-h-[80vh] overflow-y-auto">
          <div class="mb-6">
            <p class="text-gray-600 mb-4">{{ selectedSchedule.description }}</p>
            
            <!-- Schedule Summary -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div class="bg-primary-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-primary-600">{{ selectedSchedule.scenarios.length }}</div>
                <div class="text-sm text-primary-700">Сценариев</div>
              </div>
              <div class="bg-green-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-green-600">{{ getScheduleDuration(selectedSchedule) }}</div>
                <div class="text-sm text-green-700">Длительность</div>
              </div>
              <div class="bg-blue-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-blue-600">{{ getChamberName(selectedSchedule.chamber_id) }}</div>
                <div class="text-sm text-blue-700">Камера</div>
              </div>
              <div class="bg-yellow-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-yellow-600">{{ getStatusLabel(selectedSchedule.status) }}</div>
                <div class="text-sm text-yellow-700">Статус</div>
              </div>
            </div>
          </div>

          <!-- Scenarios Timeline -->
          <div v-if="selectedSchedule.scenarios.length > 0" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Последовательность сценариев</h4>
            <div class="space-y-3">
              <div v-for="(scenarioId, index) in selectedSchedule.scenarios" :key="scenarioId" 
                   class="flex items-center p-4 bg-gray-50 rounded-lg">
                <div class="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                  <span class="text-primary-600 font-medium">{{ index + 1 }}</span>
                </div>
                <div class="ml-4 flex-1">
                  <div class="font-medium text-gray-900">День {{ index + 1 }}</div>
                  <div class="text-sm text-gray-500">ID сценария: {{ scenarioId }}</div>
                  <div class="text-sm text-gray-500">24-часовой цикл выращивания</div>
                </div>
                <div class="flex-shrink-0">
                  <button class="btn-outline text-xs" @click="viewScenarioDetails(scenarioId)">
                    Подробности
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Timeline -->
          <div v-if="selectedSchedule.time_start && selectedSchedule.time_end" class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Временная шкала эксперимента</h4>
            <div class="bg-gradient-to-r from-blue-50 to-green-50 rounded-lg p-6">
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
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
                  <span class="text-gray-500">Статус:</span>
                  <div class="font-medium">{{ getTimeRemaining(selectedSchedule.time_end) }}</div>
                </div>
              </div>
              <div class="mt-4">
                <div class="text-sm text-gray-600 mb-2">Прогресс эксперимента</div>
                <div class="w-full bg-gray-200 rounded-full h-4">
                  <div class="bg-gradient-to-r from-blue-600 to-green-600 h-4 rounded-full transition-all duration-300" 
                       :style="{ width: getProgressPercentage(selectedSchedule) + '%' }"></div>
                </div>
                <div class="text-xs text-gray-500 mt-1">{{ getProgressPercentage(selectedSchedule) }}% завершено</div>
              </div>
            </div>
          </div>

          <!-- Metadata -->
          <div class="grid grid-cols-2 gap-4 text-sm text-gray-600">
            <div>
              <span class="text-gray-500">ID эксперимента:</span>
              <span class="font-medium">{{ selectedSchedule.id }}</span>
            </div>
            <div>
              <span class="text-gray-500">Создан:</span>
              <span class="font-medium">{{ formatDate(selectedSchedule.created_at) }}</span>
            </div>
            <div>
              <span class="text-gray-500">Последнее обновление:</span>
              <span class="font-medium">{{ formatDate(selectedSchedule.updated_at) }}</span>
            </div>
            <div>
              <span class="text-gray-500">Тип эксперимента:</span>
              <span class="font-medium">{{ getScheduleType(selectedSchedule) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Schedule Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showCreateModal = false">
      <div class="relative top-5 mx-auto p-5 border w-11/12 max-w-7xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Создать новый эксперимент</h3>
          
          <div class="space-y-1">
            <!-- Basic Info -->
              <div class="form-group">
                <label class="form-label">Название эксперимента</label>
                <input type="text" v-model="newSchedule.name" class="form-input" 
                       placeholder="Например: Исследование роста базилика">
              </div>
            
            <div class="form-group">
              <label class="form-label">Описание эксперимента</label>
              <textarea v-model="newSchedule.description" class="form-input" rows="3" 
                        placeholder="Опишите цели и особенности эксперимента..."></textarea>
            </div>
            
            <!-- Selected Chamber Display -->
            <div v-if="selectedChamber" class="form-group">
              <label class="form-label">Назначенная камера</label>
              <div class="bg-primary-50 border border-primary-200 rounded-lg p-3 flex items-center">
                <svg class="w-5 h-5 text-primary-600 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"></path>
                </svg>
                <div class="flex-1">
                  <div class="font-medium text-primary-900">{{ selectedChamber.name }}</div>
                  <div class="text-sm text-primary-700">{{ selectedChamber.settings?.light_sectors || 0 }} секторов освещения, {{ selectedChamber.settings?.watering_sectors || 0 }} секторов полива</div>
                </div>
              </div>
              <p class="text-sm text-gray-500 mt-1">
                Эксперимент будет запущен в выбранной камере
              </p>
            </div>
            
            <!-- Scenario Selection -->
            <div class="bg-gray-50 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-4">Выбор сценариев для эксперимента</h4>
              
              <!-- Available Scenarios -->
              <div class="mb-4">
                <label class="form-label">Выберите сценарий для добавления</label>
                <div class="flex gap-3">
                  <select v-model="selectedScenarioToAdd" class="form-input flex-1">
                    <option value="" disabled>
                      {{ availableScenarios.length === 0 ? 'Загрузка сценариев...' : 'Выберите сценарий' }}
                    </option>
                    <option v-for="scenario in availableScenarios" 
                            :key="scenario.id" 
                            :value="scenario.id"
                            :disabled="selectedScheduleScenarios.some(s => s.id === scenario.id)">
                      {{ scenario.name }}
                      {{ selectedScheduleScenarios.some(s => s.id === scenario.id) ? ' (уже добавлен)' : '' }}
                    </option>
                  </select>
                  <button @click="addSelectedScenario" 
                          :disabled="!selectedScenarioToAdd"
                          class="btn-primary whitespace-nowrap">
                    Добавить сценарий
                  </button>
                </div>
                <!-- Debug info -->
                <div v-if="availableScenarios.length === 0" class="mt-2 text-sm text-gray-500">
                  Нет доступных сценариев. Создайте сценарий в разделе "Библиотека сценариев" или обновите страницу.
                </div>
              </div>

              <!-- Selected Scenarios for Schedule -->
              <div v-if="selectedScheduleScenarios.length > 0" class="mb-4">
                <label class="form-label">Сценарии эксперимента (выберите сценарий для назначения в календаре)</label>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  <div v-for="(scenario, index) in selectedScheduleScenarios" :key="scenario.id" 
                       @click="selectScenarioForCalendar(scenario.id)"
                       :class="[
                         selectedScenarioForCalendar === scenario.id ? 'bg-blue-100 border-blue-500 ring-2 ring-blue-300' : 'bg-white hover:bg-gray-50 border-gray-200'
                       ]"
                       class="p-4 border-2 rounded-lg cursor-pointer transition-all relative">
                    <div class="flex items-start justify-between mb-2">
                      <div class="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-xs font-medium">
                        {{ index + 1 }}
                      </div>
                      <button @click.stop="removeScenarioFromSchedule(scenario.id)" 
                              class="text-red-600 hover:text-red-800">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                      </button>
                    </div>
                    <div>
                      <div class="font-medium text-gray-900 mb-1">{{ scenario.name }}</div>
                      <div class="text-sm text-gray-500 mb-2">{{ scenario.description }}</div>
                      <div v-if="getScenarioAssignedDates(scenario.id).length > 0" 
                           class="text-xs text-blue-600 font-medium">
                        Назначен на {{ getScenarioAssignedDates(scenario.id).length }} дней
                      </div>
                      <div v-else class="text-xs text-gray-400">
                        Не назначен
                      </div>
                    </div>
                    <div v-if="selectedScenarioForCalendar === scenario.id" 
                         class="absolute top-2 left-2 w-3 h-3 bg-blue-500 rounded-full ring-2 ring-white"></div>
                  </div>
                </div>
              </div>

              <!-- Calendar -->
              <div class="border rounded-lg p-4 bg-white">
                <div class="mb-4 flex justify-between items-center">
                  <h5 class="font-medium text-gray-900">Календарь эксперимента</h5>
                  <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2 text-sm">
                      <div class="w-4 h-4 bg-blue-200 rounded"></div>
                      <span>Назначен сценарий</span>
                    </div>
                    <div class="flex items-center space-x-2 text-sm">
                      <div class="w-4 h-4 bg-red-200 rounded"></div>
                      <span>Конфликт</span>
                    </div>
                    <button @click="clearAllAssignments" class="btn-outline text-sm">
                      Очистить все
                    </button>
                  </div>
                </div>

                <!-- Selected Scenario Info -->
                <div v-if="selectedScenarioForCalendar" class="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div class="flex items-center">
                    <svg class="w-5 h-5 text-blue-600 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <div>
                      <p class="text-blue-800 font-medium">Активный сценарий: {{ getScenarioName(selectedScenarioForCalendar) }}</p>
                      <p class="text-blue-700 text-sm">Кликните на даты в календаре для назначения этого сценария</p>
                    </div>
                  </div>
                </div>
                
                <div v-if="!selectedScenarioForCalendar && selectedScheduleScenarios.length > 0" class="mb-4 p-3 bg-gray-50 border border-gray-200 rounded-lg">
                  <div class="flex items-center">
                    <svg class="w-5 h-5 text-gray-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                    <div>
                      <p class="text-gray-700 font-medium">Выберите сценарий выше</p>
                      <p class="text-gray-600 text-sm">Для назначения дат сначала выберите сценарий из списка выше</p>
                    </div>
                  </div>
                </div>
                
                <!-- Month Navigation -->
                <div class="flex justify-between items-center mb-4">
                  <button @click="previousMonth" class="btn-outline">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                    </svg>
                  </button>
                  <h5 class="text-lg font-medium text-gray-900">
                    {{ currentMonth.toLocaleDateString('ru-RU', { month: 'long', year: 'numeric' }) }}
                  </h5>
                  <button @click="nextMonth" class="btn-outline">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                  </button>
                </div>

                <!-- Calendar Grid -->
                <div class="grid grid-cols-7 gap-1 mb-4">
                  <div v-for="day in weekDays" :key="day" 
                       class="text-center text-xs font-medium text-gray-500 p-2">
                    {{ day }}
                  </div>
                </div>
                
                <div class="grid grid-cols-7 gap-1">
                  <div v-for="date in calendarDates" :key="date.getTime()" 
                       @click="handleDateClick(date)"
                       :class="getCalendarDateClass(date)"
                       class="h-12 flex flex-col items-center justify-center text-xs rounded-lg cursor-pointer border transition-all hover:shadow-md relative">
                    <span class="font-bold">{{ date.getDate() }}</span>
                    <div v-if="getDateAssignment(date)" 
                         class="absolute bottom-0 left-0 right-0 h-2 rounded-b-lg"
                         :style="{ backgroundColor: getDateAssignmentColor(date) }"></div>
                  </div>
                </div>

                <!-- Scenario Legend -->
                <div v-if="selectedScheduleScenarios.length > 0 && Object.keys(dateScenarioAssignments).length > 0" 
                     class="mt-4 p-3 bg-gray-50 rounded-lg">
                  <h5 class="font-medium text-gray-900 mb-2">Легенда сценариев:</h5>
                  <div class="flex flex-wrap gap-3">
                    <template v-for="scenario in selectedScheduleScenarios" :key="scenario.id">
                      <div v-if="getScenarioAssignedDates(scenario.id).length > 0"
                           class="flex items-center space-x-2">
                        <div class="w-4 h-4 rounded"
                             :style="{ backgroundColor: getColorForScenario(scenario.id) }"></div>
                        <span class="text-sm font-medium">{{ scenario.name }}</span>
                        <span class="text-xs text-gray-500">({{ getScenarioAssignedDates(scenario.id).length }} дней)</span>
                      </div>
                    </template>
                  </div>
                </div>
              </div>

              <!-- Validation Messages -->
              <div v-if="validationMessages.length > 0" class="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <h5 class="font-medium text-red-900 mb-2">Ошибки валидации:</h5>
                <ul class="text-sm text-red-700 space-y-1">
                  <li v-for="message in validationMessages" :key="message" class="flex items-center">
                    <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                    {{ message }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <div class="flex justify-end space-x-3 mt-6">
            <button class="btn-outline" @click="cancelCreate">Отмена</button>
            <button class="btn-primary" @click="createSchedule" 
                    :disabled="!newSchedule.name || Object.keys(dateScenarioAssignments).length === 0">
              Создать эксперимент
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Schedule Modal -->
    <div v-if="showDeleteModal && scheduleToDelete" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showDeleteModal = false">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <h3 class="text-lg leading-6 font-medium text-gray-900 mt-2">Удалить эксперимент</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">
              Вы уверены, что хотите удалить эксперимент <strong>"{{ scheduleToDelete.name }}"</strong>?
            </p>
            <p class="text-sm text-red-600 mt-2">
              Это действие нельзя отменить. Эксперимент будет удален навсегда.
            </p>
          </div>
          <div class="flex justify-center space-x-3 mt-4">
            <button @click="showDeleteModal = false" class="btn-outline">
              Отмена
            </button>
            <button @click="deleteSchedule" class="btn-danger" :disabled="deleting">
              <svg v-if="deleting" class="animate-spin -ml-1 mr-3 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ deleting ? 'Удаление...' : 'Удалить' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useChambers } from '../composables/useChambers'

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

// Use chambers composable
const { selectedChamber, getChamberName } = useChambers()

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
  description: ''
})
const selectedScheduleScenarios = ref<Scenario[]>([])
const selectedScenarioForCalendar = ref('')
const selectedScenarioToAdd = ref('')
const dateScenarioAssignments = ref<Record<string, string>>({})
const currentMonth = ref(new Date())
const weekDays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
const validationMessages = ref<string[]>([])
const showDeleteModal = ref(false)
const scheduleToDelete = ref<Schedule | null>(null)
const deleting = ref(false)

// API base URL
const API_BASE = 'http://localhost:8000'

// Computed properties

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
    schedules.value = data.map((schedule: any) => ({
      ...schedule,
      id: schedule._id || schedule.id
    }))
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
    availableScenarios.value = data.map((scenario: any) => ({
      ...scenario,
      id: scenario._id || scenario.id
    }))
  } catch (err) {
    console.error('Error fetching scenarios:', err)
  }
}

const createSchedule = async () => {
  try {
    // Validate the Schedule
    const validationErrors = validateSchedule()
    if (validationErrors.length > 0) {
      validationMessages.value = validationErrors
      return
    }
    
    // Convert date-scenario assignments to ordered scenario list
    const sortedDates = Object.keys(dateScenarioAssignments.value).sort()
    const scenarioIds = sortedDates.map(dateStr => dateScenarioAssignments.value[dateStr])
    
    // Calculate Schedule start and end times
    const firstDate = new Date(sortedDates[0])
    const timeStart = Math.floor(firstDate.getTime() / 1000) + getTimezoneSecondsOffset()
    
    const scheduleData = {
      name: newSchedule.value.name,
      description: newSchedule.value.description,
      time_start: timeStart,      
      scenarios: scenarioIds,
      chamber_id: selectedChamber.value?.id || undefined
    }
    console.log(scheduleData)
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
    
    // Reset form using the cancelCreate method
    cancelCreate()
    
    // Refresh data
    await fetchSchedules()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка создания эксперимента'
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

const getScheduleType = (schedule: Schedule) => {
  if (schedule.scenarios.length === 1) {
    return 'Циклический'
  } else if (schedule.scenarios.length > 1) {
    return 'Комбинированный'
  }
  return 'Пустой'
}

const getScheduleDuration = (schedule: Schedule) => {
  const days = schedule.scenarios.length
  if (days === 1) {
    return '1 день'
  } else {
    return `${days} дней`
  }
}

const getProgressPercentage = (schedule: Schedule) => {
  if (!schedule.time_start || !schedule.time_end) return 0
  
  const now = Math.floor(Date.now() / 1000)
  const total = schedule.time_end - schedule.time_start
  const elapsed = now - schedule.time_start
  
  if (elapsed <= 0) return 0
  if (elapsed >= total) return 100
  
  return Math.round((elapsed / total) * 100)
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
    'ready': 'Готов к запуску',
    'active': 'Выполняется',
    'completed': 'Завершен',
    'cancelled': 'Отменен'
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
    return 'Завершен'
  }
  
  const diffSeconds = endTime - now
  const days = Math.floor(diffSeconds / 86400)
  const hours = Math.floor((diffSeconds % 86400) / 3600)
  const minutes = Math.floor((diffSeconds % 3600) / 60)
  
  if (days > 0) {
    return `Осталось ${days}д ${hours}ч`
  } else if (hours > 0) {
    return `Осталось ${hours}ч ${minutes}м`
  } else {
    return `Осталось ${minutes}м`
  }
}

const refreshData = async () => {
  await Promise.all([
    fetchSchedules(),
    fetchScenarios()
  ])
}

const openCreateModal = async () => {
  // Ensure scenarios are loaded before opening modal
  if (availableScenarios.value.length === 0) {
    await fetchScenarios()
  }
  // Reset form state
  selectedScenarioToAdd.value = '' // This will show the placeholder
  showCreateModal.value = true
}

const addScenarioToSchedule = (scenario: Scenario) => {
  if (!selectedScheduleScenarios.value.some(s => s.id === scenario.id)) {
    selectedScheduleScenarios.value.push(scenario)
  }
}

const addSelectedScenario = () => {
  console.log('addSelectedScenario called', { 
    selectedScenarioToAdd: selectedScenarioToAdd.value,
    availableScenarios: availableScenarios.value.length,
    availableScenarioIds: availableScenarios.value.map(s => s.id)
  })
  
  if (!selectedScenarioToAdd.value) {
    console.log('No scenario selected')
    return
  }
  
  const scenario = availableScenarios.value.find(s => s.id === selectedScenarioToAdd.value)
  if (scenario) {
    console.log('Adding scenario to Schedule:', scenario.name)
    addScenarioToSchedule(scenario)
    selectedScenarioToAdd.value = '' // Reset selection to placeholder
  } else {
    console.log('Scenario not found with ID:', selectedScenarioToAdd.value)
  }
}

const removeScenarioFromSchedule = (scenarioId: string) => {
  selectedScheduleScenarios.value = selectedScheduleScenarios.value.filter(s => s.id !== scenarioId)
  // Remove all date assignments for this scenario
  Object.keys(dateScenarioAssignments.value).forEach(dateStr => {
    if (dateScenarioAssignments.value[dateStr] === scenarioId) {
      delete dateScenarioAssignments.value[dateStr]
    }
  })
  // Clear calendar selection if this scenario was selected
  if (selectedScenarioForCalendar.value === scenarioId) {
    selectedScenarioForCalendar.value = ''
  }
}

const selectScenarioForCalendar = (scenarioId: string) => {
  selectedScenarioForCalendar.value = scenarioId
}

const getTimezoneSecondsOffset = () => {
  return new Date().getTimezoneOffset() * 60
}

// Helper function to format date without timezone conversion
const formatDateKey = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const handleDateClick = (date: Date) => {
  if (!selectedScenarioForCalendar.value) {
    return
  }
  
  const dateStr = formatDateKey(date)
  
  if (dateScenarioAssignments.value[dateStr]) {
    // If date already has a scenario, remove it
    delete dateScenarioAssignments.value[dateStr]
  } else {
    // Assign selected scenario to this date
    dateScenarioAssignments.value[dateStr] = selectedScenarioForCalendar.value
  }
  
  // Update validation messages
  validationMessages.value = validateSchedule()
}

const getScenarioAssignedDates = (scenarioId: string) => {
  return Object.keys(dateScenarioAssignments.value).filter(dateStr => 
    dateScenarioAssignments.value[dateStr] === scenarioId
  )
}

const clearAllAssignments = () => {
  dateScenarioAssignments.value = {}
  validationMessages.value = []
}




const previousMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() - 1, 1)
}

const nextMonth = () => {
  currentMonth.value = new Date(currentMonth.value.getFullYear(), currentMonth.value.getMonth() + 1, 1)
}

const calendarDates = computed(() => {
  const year = currentMonth.value.getFullYear()
  const month = currentMonth.value.getMonth()
  
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  
  const dates = []
  
  // Add previous month's trailing days
  const firstDayOfWeek = (firstDay.getDay() + 6) % 7 // Convert to Monday = 0
  for (let i = firstDayOfWeek - 1; i >= 0; i--) {
    const date = new Date(year, month, -i)
    dates.push(date)
  }
  
  // Add current month's days
  for (let day = 1; day <= lastDay.getDate(); day++) {
    dates.push(new Date(year, month, day))
  }
  
  // Add next month's leading days
  const totalCells = Math.ceil(dates.length / 7) * 7
  const remainingCells = totalCells - dates.length
  for (let i = 1; i <= remainingCells; i++) {
    dates.push(new Date(year, month + 1, i))
  }
  
  return dates
})

const getCalendarDateClass = (date: Date) => {
  const classes = []
  const dateStr = formatDateKey(date)
  const isCurrentMonth = date.getMonth() === currentMonth.value.getMonth()
  const isToday = date.toDateString() === new Date().toDateString()
  
  // Base styling
  if (!isCurrentMonth) {
    classes.push('text-gray-400', 'bg-gray-50')
  } else if (dateScenarioAssignments.value[dateStr]) {
    classes.push('bg-blue-100', 'border-blue-300', 'text-blue-800')
  } else {
    classes.push('bg-white', 'border-gray-200', 'text-gray-700')
  }
  
  // Today highlighting
  if (isToday) {
    classes.push('ring-2', 'ring-primary-500')
  }
  
  // Conflict highlighting
  if (hasDateConflict(date)) {
    classes.push('bg-red-100', 'border-red-300', 'text-red-800')
  }
  
  return classes.join(' ')
}


const getDateAssignment = (date: Date) => {
  const dateStr = formatDateKey(date)
  return dateScenarioAssignments.value[dateStr]
}

const getDateAssignmentColor = (date: Date) => {
  const scenarioId = getDateAssignment(date)
  if (!scenarioId) return '#6B7280'
  
  return getColorForScenario(scenarioId)
}

const getColorForScenario = (scenarioId: string) => {
  // Generate consistent color based on scenario ID
  const index = selectedScheduleScenarios.value.findIndex(s => s.id === scenarioId)
  const colors = ['#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EC4899', '#6366F1']
  return colors[index % colors.length] || '#6B7280'
}

const hasDateConflict = (date: Date) => {
  // Check if this date conflicts with other schedules
  // This would require checking existing schedules from the backend
  // For now, we'll just return false
  return false
}

const validateSchedule = () => {
  const errors: string[] = []
  const dates = Object.keys(dateScenarioAssignments.value)
  
  if (dates.length === 0) {
    errors.push('Необходимо назначить хотя бы один день для эксперимента')
    return errors
  }
  
  // Check for date sequence gaps
  dates.sort()
  for (let i = 1; i < dates.length; i++) {
    const prevDate = new Date(dates[i-1])
    const currentDate = new Date(dates[i])
    const dayDiff = Math.ceil((currentDate.getTime() - prevDate.getTime()) / (1000 * 60 * 60 * 24))
    
    if (dayDiff > 1) {
      errors.push(`Обнаружен пропуск между ${prevDate.toLocaleDateString('ru-RU')} и ${currentDate.toLocaleDateString('ru-RU')}`)
    }
  }
  
  // Check for conflicts with existing schedules
  // This would require checking against existing schedules from the backend
  // For now, we'll skip this check
  
  return errors
}


const getScenarioName = (scenarioId: string) => {
  const scenario = availableScenarios.value.find(s => s.id === scenarioId)
  return scenario ? scenario.name : 'Неизвестный сценарий'
}

const cancelCreate = () => {
  // Reset all form data
  newSchedule.value = {
    name: '',
    description: ''
  }
  selectedScheduleScenarios.value = []
  selectedScenarioForCalendar.value = ''
  selectedScenarioToAdd.value = '' // This will show the placeholder
  dateScenarioAssignments.value = {}
  validationMessages.value = []
  showCreateModal.value = false
}

const openDeleteModal = (schedule: Schedule) => {
  scheduleToDelete.value = schedule
  showDeleteModal.value = true
}

const deleteSchedule = async () => {
  try {
    deleting.value = true
    error.value = null
    
    const response = await fetch(`${API_BASE}/schedules/${scheduleToDelete.value?.id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // Reset form
    scheduleToDelete.value = null
    showDeleteModal.value = false
    
    // Refresh data
    await fetchSchedules()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка удаления эксперимента'
    console.error('Error deleting schedule:', err)
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  refreshData()
})
</script> 