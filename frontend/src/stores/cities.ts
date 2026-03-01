import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiService } from '@/services/apiService'

export interface City {
  id: string
  name: string          // ru
  latName?: string      // lv
  isActive: boolean
  vendors: string[]
}

export const useCitiesStore = defineStore('cities', () => {
  const { locale } = useI18n()

  const cities = ref<City[]>([])
  const selectedCity = ref<City | null>(null)
  const loading = ref<boolean>(false)

  const getCityName = (city: City) => {
    if (locale.value === 'lv' && city.latName) {
      return city.latName
    }
    return city.name
  }

  const currentCityName = computed(() => {
    return selectedCity.value ? getCityName(selectedCity.value) : ''
  })

  const selectCity = (cityId: string) => {
    const city = cities.value.find(c => c.id === cityId)
    if (city) {
      selectedCity.value = city
      localStorage.setItem('selectedCity', JSON.stringify(city))
      window.dispatchEvent(new CustomEvent('cityChanged', { detail: city }))
    }
  }

  const loadSelectedCity = () => {
    const saved = localStorage.getItem('selectedCity')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        const match = cities.value.find(c => c.id === parsed.id)
        if (match) {
          selectedCity.value = match
          return
        }
      } catch {}
    }
    // fallback — первый активный
    const first = cities.value.find(c => c.isActive)
    if (first) {
      selectedCity.value = first
      localStorage.setItem('selectedCity', JSON.stringify(first))
    }
  }

  const loadCities = async () => {
    loading.value = true
    try {
      const response = await apiService.getCities()
      if (response.success && response.data) {
        cities.value = response.data.map((city: any) => ({
          id: String(city.id),
          name: city.name_ru || city.name || city.name || '',
          latName: city.name_lv || city.name_lv || city.name || '',
          isActive: city.isActive ?? true,
          vendors: city.vendors || []
        }))
      }
    } catch (err) {
      console.error('Error loading cities:', err)
    } finally {
      loading.value = false
    }
  }

  const init = async () => {
    await loadCities()
    loadSelectedCity()
  }

  return {
    cities,
    selectedCity,
    loading,
    currentCityName,
    selectCity,
    init,
    loadCities,         // если нужно перезагружать где-то
  }
}, {
  persist: {
    key: 'cities',
    storage: localStorage,
  }
})