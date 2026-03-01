import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '@/services/apiService'
import { useCitiesStore } from '@/stores/cities'
import { getCurrentLocale } from '@/i18n'

export interface Product {
  id: string
  name: string
  description?: string
  price: number
  image?: string
  images?: string[]
  puffs: number
  strength: number
  brand: string
  vendorId: string
  vendorName?: string
  city: string
  flavors: Array<{
    id: string
    name: string
    isAvailable: boolean
  }>
  isAvailable: boolean
  isActive: boolean
  createdAt: Date
  updatedAt: Date
}

export interface FilterOptions {
  minPuffs: number
  maxPuffs: number
  strengths: number[]
  brands: string[]
  vendors?: string[]
  showOutOfStock: boolean
}

export const useCatalogStore = defineStore('catalog', () => {
  const products = ref<Product[]>([])
  const loading = ref<boolean>(false)
  const error = ref<string | null>(null)

  const filters = ref<FilterOptions>({
    minPuffs: 0,
    maxPuffs: 50000,
    strengths: [],
    brands: [],
    showOutOfStock: false,
  })

  // Методы для изменения фильтров из Header
  const setPuffRange = (min: number, max: number) => {
    filters.value.minPuffs = min
    filters.value.maxPuffs = max
  }

  const setStrength = (value: number) => {
    // Если 0 или дефолт 25 — снимаем фильтр
    filters.value.strengths = (value === 0 || value === 25) ? [] : [value]
  }

  const toggleBrand = (brand: string) => {
    if (filters.value.brands.includes(brand)) {
      filters.value.brands = filters.value.brands.filter(b => b !== brand)
    } else {
      filters.value.brands.push(brand)
    }
  }

  const resetFilters = () => {
    filters.value = {
      minPuffs: 0,
      maxPuffs: 50000,
      strengths: [],
      brands: [],
      showOutOfStock: false,
    }
  }

  // Загрузка товаров с API (только strength и brand идут в запрос)
  const loadProducts = async () => {
    loading.value = true;
    error.value = null;

    try {
        const citiesStore = useCitiesStore();
        
        // Диагностика
        console.group('📱 Mobile Debug Info');
        console.log('User Agent:', navigator.userAgent);
        console.log('Online:', navigator.onLine);
        console.log('City Store:', {
            selected: citiesStore.selectedCity,
            cities: citiesStore.cities
        });
        console.log('Current URL:', window.location.href);
        console.log('Base URL:', import.meta.env.BASE_URL);
        console.groupEnd();

        if (!citiesStore.selectedCity?.id) {
            // Попробуем подождать загрузки города
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            if (!citiesStore.selectedCity?.id) {
                throw new Error('Город не выбран');
            }
        }

        const cityId = Number(citiesStore.selectedCity.id);
        
        // Проверяем валидность cityId
        if (isNaN(cityId) || cityId <= 0) {
            throw new Error('Некорректный ID города');
        }

        const params: Record<string, any> = {};

        if (filters.value.strengths.length > 0) {
            params.strength = filters.value.strengths.join(',');
        }

        if (filters.value.brands.length > 0) {
            params.brand = filters.value.brands.join(',');
        }

        const lang = getCurrentLocale();
        
        // Пробуем выполнить запрос
        const response = await apiService.getProducts(cityId, params, lang);
        
        console.log('📦 API Response:', response);

        if (response.success && Array.isArray(response.data)) {
            products.value = response.data.map((p: any) => ({
                id: String(p.id),
                name: p.name,
                price: p.price,
                image: p.image || '',
                puffs: p.puffs,
                strength: p.strength,
                brand: p.brand,
                vendorId: String(p.seller_id || ''),
                city: String(cityId),
                flavors: p.flavors || [],
                isAvailable: !!p.in_stock,
                isActive: true,
                createdAt: new Date(),
                updatedAt: new Date(),
            }));
        } else {
            error.value = response.error || 'Не удалось загрузить товары';
            products.value = [];
        }
    } catch (err: any) {
        console.error('🔥 Mobile Error:', {
            message: err.message,
            stack: err.stack,
            name: err.name
        });
        error.value = err.message || 'Ошибка загрузки каталога';
        products.value = [];
    } finally {
        loading.value = false;
    }
  };

  // Клиентская фильтрация по количеству тяг (пока API не поддерживает puffs)
  const filteredProducts = computed(() => {
    let filtered = [...products.value]

    // Фильтр по тягам (клиентский)
    if (filters.value.minPuffs > 0) {
      filtered = filtered.filter(p => p.puffs >= filters.value.minPuffs!)
    }
    if (filters.value.maxPuffs < 50000) {
      filtered = filtered.filter(p => p.puffs <= filters.value.maxPuffs!)
    }

    // Остальные фильтры уже учтены на сервере (strength, brand)
    // но на всякий случай оставляем
    if (filters.value.strengths.length > 0) {
      filtered = filtered.filter(p => filters.value.strengths.includes(p.strength))
    }

    if (filters.value.brands.length > 0) {
      filtered = filtered.filter(p => filters.value.brands.includes(p.brand))
    }

    if (!filters.value.showOutOfStock) {
      filtered = filtered.filter(p => p.isAvailable)
    }

    return filtered
  })

  const availableBrands = computed(() => {
    return [...new Set(products.value.map(p => p.brand))].sort((a, b) => a.localeCompare(b))
  })

  const init = async () => {
    await loadProducts()
  }

  window.addEventListener('cityChanged', () => loadProducts())
  window.addEventListener('localeChanged', () => loadProducts())

  return {
    products,
    filteredProducts,
    loading,
    error,
    filters,
    availableBrands,
    setPuffRange,
    setStrength,
    toggleBrand,
    resetFilters,
    loadProducts,
    init,
  }
})