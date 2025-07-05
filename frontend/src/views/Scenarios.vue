<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Библиотека сценариев</h2>
        <p class="text-gray-600">Управление 24-часовыми циклами выращивания для научных экспериментов</p>
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
          Создать сценарий
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
          <p class="text-primary-800 font-medium">О сценариях</p>
          <p class="text-primary-700 text-sm">Каждый сценарий представляет собой 24-часовой цикл выращивания, разбитый на почасовые этапы с точными параметрами среды.</p>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="card">
      <div class="card-body text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
        <p class="mt-2 text-gray-600">Загрузка библиотеки сценариев...</p>
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
          <div>
            <h3 class="text-lg font-medium text-gray-900">{{ scenario.name }}</h3>
            <p class="text-sm text-gray-500">24-часовой цикл выращивания</p>
          </div>
          <div class="flex space-x-2">
            <button class="text-primary-600 hover:text-primary-800" @click="viewScenario(scenario)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path>
              </svg>
            </button>
            <button class="text-red-600 hover:text-red-800" @click="openDeleteModal(scenario)">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
              </svg>
            </button>
          </div>
        </div>
        <div class="card-body">
          <div class="space-y-4">
            <p class="text-sm text-gray-600">{{ scenario.description }}</p>
            
            <!-- 24-Hour Cycle Summary -->
            <div class="bg-gray-50 rounded-lg p-3">
              <h4 class="text-sm font-medium text-gray-900 mb-2">Суточный цикл ({{ scenario.parameters.length }} часов)</h4>
              <div class="grid grid-cols-4 gap-2 text-xs">
                <div class="text-center">
                  <div class="text-gray-500">Температура</div>
                  <div class="font-medium">{{ getTempRange(scenario.parameters) }}°C</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Влажность</div>
                  <div class="font-medium">{{ getHumidityRange(scenario.parameters) }}%</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">CO₂</div>
                  <div class="font-medium">{{ getCO2Range(scenario.parameters) }} ppm</div>
                </div>
                <div class="text-center">
                  <div class="text-gray-500">Освещение</div>
                  <div class="font-medium">{{ getLightRange(scenario.parameters) }}%</div>
                </div>
              </div>
            </div>
          
            
            <div class="pt-2 border-t text-xs text-gray-500">
              <div>Создан: {{ formatDate(scenario.created_at) }}</div>
              <div v-if="scenario.updated_at !== scenario.created_at">
                Обновлен: {{ formatDate(scenario.updated_at) }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-if="scenarios.length === 0 && !loading && !error" class="card">
      <div class="card-body text-center py-8">
        <svg class="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v18m0 0l-4-4m4 4l4-4M3 12h18"></path>
        </svg>
        <h3 class="text-lg font-medium text-gray-900 mb-2">Библиотека сценариев пуста</h3>
        <p class="text-gray-600 mb-4">Создайте первый 24-часовой сценарий для начала экспериментов</p>
        <button class="btn-primary" @click="openCreateModal">
          <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
          </svg>
          Создать сценарий
        </button>
      </div>
    </div>

    <!-- View Scenario Modal -->
    <div v-if="showViewModal && selectedScenario" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showViewModal = false">
      <div class="relative top-10 mx-auto p-0 border w-11/12 max-w-6xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-md">
          <div class="flex justify-between items-center">
            <div>
              <h3 class="text-lg font-medium text-gray-900">{{ selectedScenario.name }}</h3>
              <p class="text-sm text-gray-500">24-часовой цикл выращивания</p>
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
            <p class="text-gray-600 mb-4">{{ selectedScenario.description }}</p>
            
            <!-- Scenario Summary -->
            <div class="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div class="bg-primary-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-primary-600">{{ selectedScenario.parameters.length }}</div>
                <div class="text-sm text-primary-700">Часов в цикле</div>
              </div>
              <div class="bg-green-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-green-600">{{ getTempRange(selectedScenario.parameters) }}</div>
                <div class="text-sm text-green-700">Температура °C</div>
              </div>
              <div class="bg-blue-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-blue-600">{{ getHumidityRange(selectedScenario.parameters) }}</div>
                <div class="text-sm text-blue-700">Влажность %</div>
              </div>
              <div class="bg-yellow-50 rounded-lg p-4 text-center">
                <div class="text-2xl font-bold text-yellow-600">{{ getLightRange(selectedScenario.parameters) }}</div>
                <div class="text-sm text-yellow-700">Освещение %</div>
              </div>
            </div>
          </div>

          <!-- 24-Hour Parameters Table -->
          <div class="mb-6">
            <h4 class="text-lg font-medium text-gray-900 mb-4">Почасовые параметры</h4>
            <div class="overflow-x-auto">
              <table class="min-w-full border border-gray-200">
                <thead class="bg-gray-50">
                  <tr>
                    <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase border-r">Время</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Температура (°C)</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Влажность (%)</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">CO₂ (ppm)</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">Освещение (сектора)</th>
                    <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">Полив (мин)</th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200">
                  <tr v-for="(param, index) in selectedScenario.parameters" :key="index" 
                      class="hover:bg-gray-50">
                    <td class="px-3 py-2 font-medium text-gray-900 border-r">
                      {{ String(index).padStart(2, '0') }}:00
                    </td>
                    <td class="px-3 py-2 text-center border-r">
                      <span class="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded">
                        {{ param.temperature }}°C
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center border-r">
                      <span class="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded">
                        {{ param.humidity }}%
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center border-r">
                      <span class="px-2 py-1 text-xs font-medium bg-purple-100 text-purple-800 rounded">
                        {{ param.co2_level }}
                      </span>
                    </td>
                    <td class="px-3 py-2 text-center border-r">
                      <div class="flex justify-center space-x-1">
                        <span v-for="light in param.light_sectors" :key="light.sector_id" 
                              class="px-1 py-0.5 text-xs font-medium bg-yellow-100 text-yellow-800 rounded">
                          S{{ light.sector_id }}:{{ light.light_intensity }}%
                        </span>
                      </div>
                    </td>
                    <td class="px-3 py-2 text-center">
                                             <div class="flex justify-center space-x-1">
                         <template v-for="watering in param.watering_sectors" :key="watering.sector_id">
                           <span v-if="watering.watering_duration > 0"
                                 class="px-1 py-0.5 text-xs font-medium bg-cyan-100 text-cyan-800 rounded">
                             S{{ watering.sector_id }}:{{ watering.watering_duration }}м
                           </span>
                         </template>
                         <span v-if="!param.watering_sectors.some(w => w.watering_duration > 0)" 
                               class="px-1 py-0.5 text-xs font-medium bg-gray-100 text-gray-500 rounded">
                           —
                         </span>
                       </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Scenario Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showCreateModal = false">
      <div class="relative top-5 mx-auto p-5 border w-11/12 max-w-7xl shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3">
          <div class="flex justify-between items-center mb-6">
            <div>
              <h3 class="text-lg font-medium text-gray-900">Создать 24-часовой сценарий</h3>
              <p class="text-sm text-gray-500">Настройте параметры среды для каждого часа суток</p>
            </div>
            <button @click="showCreateModal = false" class="text-gray-400 hover:text-gray-600">
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
              </svg>
            </button>
          </div>
          
          <div class="space-y-6">
            <!-- Basic Info -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="form-group">
                <label class="form-label">Название сценария</label>
                <input type="text" v-model="newScenario.name" class="form-input" 
                       placeholder="Например: Базовый цикл для листовых">
              </div>
            </div>
            
            <div class="form-group">
              <label class="form-label">Описание сценария</label>
              <textarea v-model="newScenario.description" class="form-input" rows="2" 
                        placeholder="Опишите условия выращивания и особенности данного цикла..."></textarea>
            </div>

            <!-- Parameters Table -->
            <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
              <div class="border-b border-gray-200 p-4">
                <div class="flex justify-between items-center mb-3">
                  <h4 class="font-medium text-gray-900">Параметры по часам</h4>
                  <div class="flex items-center space-x-2">
                    <button @click="copySelectedRows" class="btn-outline text-xs" :disabled="selectedRows.length === 0">
                      Копировать ({{ selectedRows.length }})
                    </button>
                    <button @click="pasteToSelectedRows" class="btn-outline text-xs" :disabled="selectedRows.length === 0 || copiedRows.length === 0">
                      Вставить
                    </button>
                  </div>
                </div>
                <p class="text-sm text-gray-500">Используйте чекбокс в заголовке для выбора всех строк, отдельные чекбоксы для выбора нужных часов или правый клик для быстрых действий</p>
              </div>
              
              <div class="overflow-x-auto">
                <table class="w-full">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r sticky left-0 bg-gray-50 w-16">
                        <input type="checkbox" v-model="selectAllCheckbox" class="form-checkbox">
                      </th>
                      <th class="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase border-r sticky left-0 bg-gray-50" style="left: 64px;">
                        Время
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Температура<br/>(°C)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Влажность<br/>(%)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        CO₂<br/>(ppm)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Освещение 1<br/>(%)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Освещение 2<br/>(%)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Освещение 3<br/>(%)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Полив 1<br/>(мин)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase border-r">
                        Полив 2<br/>(мин)
                      </th>
                      <th class="px-3 py-2 text-center text-xs font-medium text-gray-500 uppercase">
                        Полив 3<br/>(мин)
                      </th>
                    </tr>
                  </thead>
                  <tbody class="bg-white divide-y divide-gray-200">
                    <tr v-for="(param, hour) in newScenario.parameters" :key="hour" 
                        class="hover:bg-gray-50"
                        @contextmenu.prevent="showContextMenu($event, hour)">
                      <td class="px-3 py-2 text-center border-r sticky left-0 bg-white hover:bg-gray-50 w-16">
                        <input type="checkbox" v-model="selectedRows" :value="hour" class="form-checkbox">
                      </td>
                      <td class="px-3 py-2 text-sm font-medium text-gray-900 border-r sticky left-0 bg-white hover:bg-gray-50" style="left: 64px;">
                        {{ String(hour).padStart(2, '0') }}:00
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.temperature" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="10" max="35" step="0.5">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.humidity" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="30" max="90" step="1">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.co2_level" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="200" max="1000" step="10">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.light_sectors[0].light_intensity" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="100" step="1">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.light_sectors[1].light_intensity" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="100" step="1">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.light_sectors[2].light_intensity" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="100" step="1">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.watering_sectors[0].watering_duration" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="120" step="1">
                      </td>
                      <td class="px-3 py-2 text-center border-r">
                        <input type="number" v-model.number="param.watering_sectors[1].watering_duration" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="120" step="1">
                      </td>
                      <td class="px-3 py-2 text-center">
                        <input type="number" v-model.number="param.watering_sectors[2].watering_duration" 
                               class="w-16 text-center border-0 focus:ring-1 focus:ring-blue-500 rounded text-sm"
                               min="0" max="120" step="1">
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- Context Menu -->
            <div v-if="contextMenu.show" 
                 class="fixed bg-white border border-gray-200 rounded-lg shadow-lg z-50 py-2"
                 :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
                 @click.stop>
              <button @click="copyRow(contextMenu.hour)" 
                      class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                </svg>
                Копировать строку {{ String(contextMenu.hour).padStart(2, '0') }}:00
              </button>
              <button @click="pasteRow(contextMenu.hour)" 
                      :disabled="copiedRow === null"
                      class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center"
                      :class="copiedRow === null ? 'text-gray-400' : ''">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path>
                </svg>
                Вставить строку
                {{ copiedRow !== null ? `(из ${String(copiedRow).padStart(2, '0')}:00)` : '' }}
              </button>
              <hr class="my-1">
              <button @click="duplicateRow(contextMenu.hour)" 
                      class="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 flex items-center">
                <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2"></path>
                </svg>
                Дублировать в соседние часы
              </button>
            </div>

            <!-- Summary -->
            <div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h4 class="font-medium text-gray-900 mb-3">Сводка сценария</h4>
              <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <div class="text-center">
                  <div class="text-sm text-gray-600">Температура</div>
                  <div class="font-bold text-green-600">{{ getTempRange(newScenario.parameters) }}°C</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-600">Влажность</div>
                  <div class="font-bold text-blue-600">{{ getHumidityRange(newScenario.parameters) }}%</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-600">CO₂</div>
                  <div class="font-bold text-purple-600">{{ getCO2Range(newScenario.parameters) }} ppm</div>
                </div>
                <div class="text-center">
                  <div class="text-sm text-gray-600">Освещение</div>
                  <div class="font-bold text-yellow-600">{{ getLightRange(newScenario.parameters) }}%</div>
                </div>
              </div>
            </div>
          </div>
          
          <div class="flex justify-end space-x-3 mt-6">
            <button class="btn-outline" @click="closeModal">Отмена</button>
            <button class="btn-primary" @click="createScenario" :disabled="!newScenario.name">
              <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
              </svg>
              Создать сценарий
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete Scenario Modal -->
    <div v-if="showDeleteModal && scenarioToDelete" class="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" @click="showDeleteModal = false">
      <div class="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white" @click.stop>
        <div class="mt-3 text-center">
          <div class="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
            <svg class="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
            </svg>
          </div>
          <h3 class="text-lg leading-6 font-medium text-gray-900 mt-2">Удалить сценарий</h3>
          <div class="mt-2 px-7 py-3">
            <p class="text-sm text-gray-500">
              Вы уверены, что хотите удалить сценарий <strong>"{{ scenarioToDelete.name }}"</strong>?
            </p>
            <p class="text-sm text-red-600 mt-2">
              Это действие нельзя отменить. Сценарий будет удален навсегда.
            </p>
          </div>
          <div class="flex justify-center space-x-3 mt-4">
            <button @click="showDeleteModal = false" class="btn-outline">
              Отмена
            </button>
            <button @click="deleteScenario" class="btn-danger" :disabled="deleting">
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
import { ref, onMounted, onUnmounted, computed } from 'vue'

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
  description: '',
  template: 'custom',
  parameters: [] as Parameters[]
})
const copiedRow = ref<number | null>(null)
const selectedRows = ref<number[]>([])
const copiedRows = ref<Parameters[]>([])
const contextMenu = ref({
  show: false,
  x: 0,
  y: 0,
  hour: 0
})
const showDeleteModal = ref(false)
const scenarioToDelete = ref<Scenario | null>(null)
const deleting = ref(false)

// Computed for select all checkbox
const selectAllCheckbox = computed({
  get: () => selectedRows.value.length === 24,
  set: (value: boolean) => {
    if (value) {
      selectedRows.value = Array.from({ length: 24 }, (_, i) => i)
    } else {
      selectedRows.value = []
    }
  }
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
    // Transform _id to id for frontend compatibility
    scenarios.value = data.map((scenario: any) => ({
      ...scenario,
      id: scenario._id || scenario.id
    }))
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Неизвестная ошибка'
    console.error('Error fetching scenarios:', err)
  } finally {
    loading.value = false
  }
}

const createScenario = async () => {
  try {
    console.log(newScenario.value)
    
    const scenarioData = {
      name: newScenario.value.name,
      description: newScenario.value.description,
      parameters: newScenario.value.parameters
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
    newScenario.value = { name: '', description: '', template: 'custom', parameters: [] as Parameters[] }
    showCreateModal.value = false
    
    // Refresh data
    await fetchScenarios()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка создания сценария'
    console.error('Error creating scenario:', err)
  }
}

const openCreateModal = () => {
  // Reset form
  newScenario.value = { name: '', description: '', template: 'custom', parameters: [] as Parameters[] }
  // Initialize parameters
  initializeParameters()
  // Reset selection state
  selectedRows.value = []
  copiedRows.value = []
  // Open modal
  showCreateModal.value = true
}

const viewScenario = (scenario: Scenario) => {
  selectedScenario.value = scenario
  showViewModal.value = true
}

const getTempRange = (parameters: Parameters[]) => {
  const temps = parameters.map(p => p.temperature)
  return `${Math.min(...temps)}-${Math.max(...temps)}`
}

const getHumidityRange = (parameters: Parameters[]) => {
  const humidities = parameters.map(p => p.humidity)
  return `${Math.min(...humidities)}-${Math.max(...humidities)}`
}

const getCO2Range = (parameters: Parameters[]) => {
  const co2s = parameters.map(p => p.co2_level)
  return `${Math.min(...co2s)}-${Math.max(...co2s)}`
}

const getLightRange = (parameters: Parameters[]) => {
  const lights = parameters.map(p => Math.max(...p.light_sectors.map(s => s.light_intensity)))
  return `${Math.min(...lights)}-${Math.max(...lights)}`
}

const formatDate = (timestamp: number) => {
  return new Date(timestamp * 1000).toLocaleString('ru-RU')
}

const refreshData = async () => {
  await fetchScenarios()
}

const initializeParameters = () => {
  const parameters: Parameters[] = []
  
  for (let hour = 0; hour < 24; hour++) {
    const lightIntensity = 0
    const temperature = 20
    const humidity = 65
    const co2Level = 400
    
    parameters.push({
      temperature,
      humidity,
      light_sectors: [
        { sector_id: 1, light_intensity: lightIntensity },
        { sector_id: 2, light_intensity: lightIntensity },
        { sector_id: 3, light_intensity: lightIntensity }
      ],
      co2_level: co2Level,
      watering_sectors: [
        { sector_id: 1, watering_duration: 0 },
        { sector_id: 2, watering_duration: 0 },
        { sector_id: 3, watering_duration: 0 }
      ]
    })
  }
  
  newScenario.value.parameters = parameters
}

const showContextMenu = (event: MouseEvent, hour: number) => {
  event.preventDefault()
  contextMenu.value.show = true
  contextMenu.value.x = event.clientX
  contextMenu.value.y = event.clientY
  contextMenu.value.hour = hour
}

const copyRow = (hour: number) => {
  copiedRow.value = hour
  contextMenu.value.show = false
}

const pasteRow = (hour: number) => {
  if (copiedRow.value === null) return
  
  const source = newScenario.value.parameters[copiedRow.value]
  const target = newScenario.value.parameters[hour]
  
  target.temperature = source.temperature
  target.humidity = source.humidity
  target.co2_level = source.co2_level
  target.light_sectors.forEach((sector, index) => {
    sector.light_intensity = source.light_sectors[index].light_intensity
  })
  target.watering_sectors.forEach((sector, index) => {
    sector.watering_duration = source.watering_sectors[index].watering_duration
  })
  
  contextMenu.value.show = false
}

const duplicateRow = (hour: number) => {
  const source = newScenario.value.parameters[hour]
  
  for (let targetHour = 0; targetHour < 24; targetHour++) {
    if (targetHour !== hour) {
      const target = newScenario.value.parameters[targetHour]
      target.temperature = source.temperature
      target.humidity = source.humidity
      target.co2_level = source.co2_level
      target.light_sectors.forEach((sector, index) => {
        sector.light_intensity = source.light_sectors[index].light_intensity
      })
      target.watering_sectors.forEach((sector, index) => {
        sector.watering_duration = source.watering_sectors[index].watering_duration
      })
    }
  }
  
  contextMenu.value.show = false
}

const closeModal = () => {
  showCreateModal.value = false
}

// Checkbox selection methods

const copySelectedRows = () => {
  if (selectedRows.value.length === 0) return
  
  copiedRows.value = selectedRows.value.map(hour => {
    const param = newScenario.value.parameters[hour]
    return {
      temperature: param.temperature,
      humidity: param.humidity,
      co2_level: param.co2_level,
      light_sectors: param.light_sectors.map(sector => ({
        sector_id: sector.sector_id,
        light_intensity: sector.light_intensity
      })),
      watering_sectors: param.watering_sectors.map(sector => ({
        sector_id: sector.sector_id,
        watering_duration: sector.watering_duration
      }))
    }
  })
}

const pasteToSelectedRows = () => {
  if (selectedRows.value.length === 0 || copiedRows.value.length === 0) return
  
  selectedRows.value.forEach((hour, index) => {
    const sourceIndex = index % copiedRows.value.length
    const source = copiedRows.value[sourceIndex]
    const target = newScenario.value.parameters[hour]
    
    target.temperature = source.temperature
    target.humidity = source.humidity
    target.co2_level = source.co2_level
    target.light_sectors.forEach((sector, sectorIndex) => {
      sector.light_intensity = source.light_sectors[sectorIndex].light_intensity
    })
    target.watering_sectors.forEach((sector, sectorIndex) => {
      sector.watering_duration = source.watering_sectors[sectorIndex].watering_duration
    })
  })
  
  // Clear selection after pasting
  selectedRows.value = []
}

// Close context menu when clicking outside
const closeContextMenu = () => {
  contextMenu.value.show = false
}

const openDeleteModal = (scenario: Scenario) => {
  scenarioToDelete.value = scenario
  showDeleteModal.value = true
}

const deleteScenario = async () => {
  try {
    deleting.value = true
    error.value = null
    
    const response = await fetch(`${API_BASE}/scenarios/${scenarioToDelete.value?.id}`, {
      method: 'DELETE'
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    // Reset form
    scenarioToDelete.value = null
    showDeleteModal.value = false
    
    // Refresh data
    await fetchScenarios()
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Ошибка удаления сценария'
    console.error('Error deleting scenario:', err)
  } finally {
    deleting.value = false
  }
}

onMounted(() => {
  fetchScenarios()
  
  // Add click handler to close context menu
  document.addEventListener('click', closeContextMenu)
  document.addEventListener('contextmenu', closeContextMenu)
})

onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
  document.removeEventListener('contextmenu', closeContextMenu)
})
</script> 