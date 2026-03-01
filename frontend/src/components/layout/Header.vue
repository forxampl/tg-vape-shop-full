<template>
  <header class="app-header" :class="{ 'is-catalog': isCatalog }">
    <div class="header-top">
      <h1 class="page-title">{{ pageTitle }}</h1>
    </div>

    <div v-if="isCatalog" class="header-controls">
      <!-- Город -->
      <div class="dropdown" ref="cityDropdownEl">
        <button class="dropdown-button" type="button" @click="toggleCityDropdown">
          <span class="dropdown-label">{{ currentCityName || t('common.loading') }}</span>
          <span class="dropdown-chevron" :class="{ open: cityDropdownOpen }">▼</span>
        </button>

        <div v-if="cityDropdownOpen" class="dropdown-menu">
          <button
            v-for="city in activeCities"
            :key="city.id"
            type="button"
            class="dropdown-item"
            :class="{ active: city.id === selectedCity?.id }"
            @click="selectCity(city.id)"
          >
            {{ city.name }}
          </button>
          <div v-if="loading" class="dropdown-loading">
            {{ t('common.loading') }}
          </div>
        </div>
      </div>

      <!-- Фильтры -->
      <div class="dropdown" ref="filtersDropdownEl">
        <button class="dropdown-button" type="button" @click="toggleFiltersDropdown">
          <span class="dropdown-label">
            {{ t('catalog.filters') }}
            <span v-if="activeFiltersCount > 0" class="filters-badge">
              {{ activeFiltersCount }}
            </span>
          </span>
          <span class="dropdown-chevron" :class="{ open: filtersDropdownOpen }">▼</span>
        </button>

        <div v-if="filtersDropdownOpen" class="dropdown-menu filters-menu">
          <!-- Количество тяг -->
          <div class="filter-section">
            <div class="filter-header">
              <span class="filter-title">{{ t('catalog.filterLabels.puffs') }}</span>
              <span class="filter-value">{{ puffCount.toLocaleString() }} / 50000</span>
            </div>
            <div class="range-slider">
              <input 
                type="range" 
                class="slider" 
                min="0" 
                max="50000" 
                :value="puffCount"
                @input="updatePuffCount"
                step="1000"
              />
              <div class="range-labels">
                <span>0</span>
                <span>25000</span>
                <span>50000</span>
              </div>
            </div>
          </div>

          <!-- Крепость -->
          <div class="filter-section">
            <div class="filter-header">
              <span class="filter-title">{{ t('catalog.filterLabels.strength') }}</span>
              <span class="filter-value">{{ strength }} mg</span>
            </div>
            <div class="range-slider">
              <input 
                type="range" 
                class="slider" 
                min="0" 
                max="50" 
                :value="strength"
                @input="updateStrength"
                step="5"
              />
              <div class="range-labels">
                <span>0mg</span>
                <span>25mg</span>
                <span>50mg</span>
              </div>
            </div>
          </div>

          <!-- Бренды -->
          <div class="filter-section">
            <div class="filter-header">
              <span class="filter-title">{{ t('catalog.filterLabels.brands') }}</span>
            </div>
            <div class="brands-grid">
              <button 
                v-for="brand in displayedBrands"
                :key="brand"
                class="brand-button" 
                :class="{ active: selectedBrands.includes(brand) }"
                @click="toggleBrand(brand)"
              >
                {{ brand }}
              </button>

              <button
                v-if="!showAllBrands && hiddenBrandsCount > 0"
                class="brand-button more-brands"
                @click="showAllBrands = true"
              >
                {{ t('catalog.allBrands') }}
              </button>

              <button
                v-if="showAllBrands && totalBrandsCount > 3"
                class="brand-button more-brands"
                @click="showAllBrands = false"
              >
                {{ t('common.collapse') }}
              </button>
            </div>
          </div>

          <!-- Кнопка сброса -->
          <button class="reset-filters" @click="resetFilters">
            {{ t('common.clearFilters') }}
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCartStore } from '@/stores/cart'
import { useCitiesStore } from '@/stores/cities'
import { useCatalogStore } from '@/stores/catalog'

const { t } = useI18n()
const cartStore = useCartStore()
const citiesStore = useCitiesStore()
const catalogStore = useCatalogStore()
const route = useRoute()

// Фильтры - меняем начальные значения на МАКСИМУМ
const puffCount = ref(50000) // Было 25000, стало 50000 (максимум)
const strength = ref(50)      // Было 25, стало 50 (максимум)
const selectedBrands = ref<string[]>([])

// Бренды
const showAllBrands = ref(false)
const BRANDS_TO_SHOW_INITIALLY = 3

const allUniqueBrands = computed(() => {
  return [...catalogStore.availableBrands].sort((a, b) => a.localeCompare(b))
})

const totalBrandsCount = computed(() => allUniqueBrands.value.length)

const visibleBrandsShort = computed(() => {
  return allUniqueBrands.value.slice(0, BRANDS_TO_SHOW_INITIALLY)
})

const hiddenBrandsCount = computed(() => {
  return Math.max(0, totalBrandsCount.value - BRANDS_TO_SHOW_INITIALLY)
})

const displayedBrands = computed(() => {
  if (showAllBrands.value || totalBrandsCount.value <= BRANDS_TO_SHOW_INITIALLY) {
    return allUniqueBrands.value
  }
  return visibleBrandsShort.value
})

// Индикатор активных фильтров - обновляем логику
const activeFiltersCount = computed(() => {
  let count = 0
  // Считаем только если значение НЕ максимальное
  if (puffCount.value !== 50000) count++           // Было 25000, стало 50000
  if (strength.value !== 50) count++                // Было 25, стало 50
  count += selectedBrands.value.length
  return count
})

// computed из роутера и сторов
const isCatalog = computed(() => route.path === '/')

const pageTitle = computed(() => {
  const metaTitleKey = (route.meta?.titleKey as string | undefined) ?? ''
  if (metaTitleKey) return t(metaTitleKey)
  if (route.path.startsWith('/product')) return t('product.defaultTitle')
  if (route.path.startsWith('/order')) return t('order.title')
  if (route.path.startsWith('/cabinet')) return t('cabinet.title')
  return t('app.title')
})

const activeCities = computed(() => citiesStore.cities.filter(c => c.isActive))
const selectedCity = computed(() => citiesStore.selectedCity)
const currentCityName = computed(() => citiesStore.currentCityName)
const loading = computed(() => citiesStore.loading)

// Dropdown state
const cityDropdownOpen = ref(false)
const filtersDropdownOpen = ref(false)
const cityDropdownEl = ref<HTMLElement | null>(null)
const filtersDropdownEl = ref<HTMLElement | null>(null)

const closeAllDropdowns = () => {
  cityDropdownOpen.value = false
  filtersDropdownOpen.value = false
  showAllBrands.value = false
}

const toggleCityDropdown = () => {
  cityDropdownOpen.value = !cityDropdownOpen.value
  if (filtersDropdownOpen.value) filtersDropdownOpen.value = false
}

const toggleFiltersDropdown = () => {
  filtersDropdownOpen.value = !filtersDropdownOpen.value
  if (cityDropdownOpen.value) cityDropdownOpen.value = false
}

const selectCity = (cityId: string) => {
  citiesStore.selectCity(cityId)
  cityDropdownOpen.value = false
}

// Обработчики фильтров
const updatePuffCount = (e: Event) => {
  puffCount.value = Number((e.target as HTMLInputElement).value)
  catalogStore.setPuffRange(0, puffCount.value)
  // puffs — клиентский фильтр, можно не перезагружать с сервера
}

const updateStrength = (e: Event) => {
  strength.value = Number((e.target as HTMLInputElement).value)
  catalogStore.setStrength(strength.value)
  catalogStore.loadProducts()
}

const toggleBrand = (brand: string) => {
  if (selectedBrands.value.includes(brand)) {
    selectedBrands.value = selectedBrands.value.filter(b => b !== brand)
  } else {
    selectedBrands.value.push(brand)
  }
  catalogStore.toggleBrand(brand)
  catalogStore.loadProducts()
}

const resetFilters = () => {
  // Меняем значения на МАКСИМУМ, а не на середину
  puffCount.value = 50000  // Было 25000, стало 50000
  strength.value = 50       // Было 25, стало 50
  selectedBrands.value = []
  showAllBrands.value = false
  catalogStore.resetFilters()
  catalogStore.loadProducts()
}

// Закрытие по клику вне
const onDocumentPointerDown = (e: PointerEvent) => {
  const target = e.target as Node | null
  if (!target) return

  const inCity = cityDropdownEl.value?.contains(target) ?? false
  const inFilters = filtersDropdownEl.value?.contains(target) ?? false
  if (!inCity && !inFilters) {
    closeAllDropdowns()
  }
}

// Инициализация фильтров при монтировании
onMounted(async () => {
  cartStore.init()
  
  // Устанавливаем начальные значения фильтров в сторе
  catalogStore.setPuffRange(0, puffCount.value)
  catalogStore.setStrength(strength.value)
  
  document.addEventListener('pointerdown', onDocumentPointerDown, { capture: true })
})

onBeforeUnmount(() => {
  document.removeEventListener('pointerdown', onDocumentPointerDown, { capture: true })
})
</script>

<style lang="scss" scoped>
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: #000000;
  color: #ffffff;
  padding: 16px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 10px;

  --app-header-height: 104px;
}

.header-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.page-title {
  margin: 0;
  font-size: 40px;
  font-weight: 500;
  letter-spacing: -0.02em;
  line-height: 1;
}

.header-controls {
  margin-top: 14px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.dropdown {
  position: relative;
}

.dropdown-button {
  width: 100%;
  border: none;
  background: rgba(255, 255, 255, 0.10);
  color: #ffffff;
  padding: 12px 14px;
  border-radius: 14px;
  font-family: inherit;
  font-size: 14px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  cursor: pointer;

  &:hover {
    background: rgba(255, 255, 255, 0.14);
  }
}

.dropdown-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dropdown-chevron {
  font-size: 12px;
  opacity: 0.8;
  transition: transform 0.15s ease;
  transform: rotate(0deg);

  &.open {
    transform: rotate(180deg);
  }
}

.dropdown-menu {
  position: absolute;
  left: 1;
  right: 0;
  top: calc(100% + 10px);
  background: #2b2b2b;
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 14px;
  padding: 6px;
  max-height: 240px;
  overflow-y: auto;
  width: 200px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.45);
  z-index: 101;
}

.dropdown-loading {
  padding: 12px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
}

.filters-menu {
  max-height: 480px;
  width: 320px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.filter-section {
  margin-bottom: 24px;

  &:last-of-type {
    margin-bottom: 0;
  }
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}

.filter-title {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.filter-value {
  font-size: 14px;
  font-weight: 500;
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 10px;
  border-radius: 20px;
}

.range-slider {
  width: 100%;
  padding: 0 2px;
}

.slider {
  width: 100%;
  height: 6px;
  -webkit-appearance: none;
  appearance: none;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  outline: none;
  margin-bottom: 12px;

  &::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 22px;
    height: 22px;
    background: #ffffff;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    transition: transform 0.1s ease;

    &:hover {
      transform: scale(1.1);
    }
  }

  &::-moz-range-thumb {
    width: 22px;
    height: 22px;
    background: #ffffff;
    border: none;
    border-radius: 50%;
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    transition: transform 0.1s ease;

    &:hover {
      transform: scale(1.1);
    }
  }
}

.range-labels {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  padding: 0 2px;

  span {
    width: 35px;
  }
}

.brands-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr); 
  gap: 8px;
  margin-top: 8px;
}

.brand-button {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #ffffff;
  padding: 10px 6px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.12);
    border-color: rgba(255, 255, 255, 0.2);
  }

  &.active {
    background: #ffffff;
    color: #000000;
    border-color: #ffffff;
  }
}

.reset-filters {
  width: 100%;
  background: rgba(255, 59, 48, 0.15);
  border: 1px solid rgba(255, 59, 48, 0.3);
  color: #ff3b30;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 16px;
  transition: all 0.2s ease;

  &:hover {
    background: rgba(255, 59, 48, 0.25);
    border-color: rgba(255, 59, 48, 0.5);
  }
}

.dropdown-item {
  width: 100%;
  border: none;
  background: transparent;
  color: #ffffff;
  padding: 12px;
  border-radius: 10px;
  font-family: inherit;
  font-size: 14px;
  text-align: left;
  cursor: pointer;
  margin-top: 3px;

  &:hover {
    background: rgba(255, 255, 255, 0.10);
  }

  &.active {
    background: rgba(255, 255, 255, 0.14);
  }
}

.dropdown-item:first-child {
  margin-top: 0;
}

.more-brands {
  background: rgba(100, 180, 255, 0.15) !important;
  border-color: rgba(100, 180, 255, 0.4) !important;
  color: #a0d0ff !important;
}

.more-brands:hover {
  background: rgba(100, 180, 255, 0.25) !important;
}
</style>