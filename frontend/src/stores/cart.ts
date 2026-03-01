import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiService } from '@/services/apiService'
import type { CreateOrderRequest, OrderResponse } from '@/interfaces/Order'
import { useTelegram } from '@/composables/useTelegram'

export interface CartItem {
  productId: string
  name: string
  price: number
  quantity: number
  image?: string
  flavors: Array<{
    id: string
    name: string
    quantity: number
    isAvailable?: boolean
  }>
  city: string
  vendorId: string
  vendorName?: string
}

export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  
  // Общая стоимость
  const totalPrice = computed(() => {
    return items.value.reduce((total, item) => {
      return total + (item.price * item.quantity)
    }, 0)
  })
  
  // Общее количество товаров
  const totalItems = computed(() => {
    return items.value.reduce((total, item) => total + item.quantity, 0)
  })
  
  // Добавление товара в корзину
  const addItem = (item: Omit<CartItem, 'quantity'>) => {
    const existingItemIndex = items.value.findIndex(
      i => i.productId === item.productId && 
           JSON.stringify(i.flavors) === JSON.stringify(item.flavors)
    )
    
    if (existingItemIndex > -1) {
      const existingItem = items.value[existingItemIndex]
      if (existingItem) {
        existingItem.quantity += 1
      }
    } else {
      items.value.push({ ...item, quantity: 1 })
    }
    
    saveCartToStorage()
  }
  
  // Удаление товара из корзины
  const removeItem = (itemId: string, flavors: any[] = []) => {
    const itemIndex = items.value.findIndex(
      i => i.productId === itemId && 
           JSON.stringify(i.flavors) === JSON.stringify(flavors)
    )
    
    if (itemIndex > -1) {
      items.value.splice(itemIndex, 1)
      saveCartToStorage()
    }
  }
  
  // Обновление количества
  const updateQuantity = (itemId: string, quantity: number, flavors: any[] = []) => {
    const itemIndex = items.value.findIndex(
      i => i.productId === itemId && 
           JSON.stringify(i.flavors) === JSON.stringify(flavors)
    )
    
    if (itemIndex > -1) {
      const item = items.value[itemIndex]
      if (item) {
        if (quantity <= 0) {
          removeItem(itemId, flavors)
        } else {
          item.quantity = quantity
          saveCartToStorage()
        }
      }
    }
  }
  
  // Очистка корзины
  const clearCart = () => {
    items.value = []
    localStorage.removeItem('cart')
  }
  
  // Сохранение в localStorage
  const saveCartToStorage = () => {
    localStorage.setItem('cart', JSON.stringify(items.value))
  }
  
  // Загрузка из localStorage
  const loadCartFromStorage = () => {
    const savedCart = localStorage.getItem('cart')
    if (savedCart) {
      try {
        const parsed = JSON.parse(savedCart)
        // Проверяем что parsed это массив
        if (Array.isArray(parsed)) {
          items.value = parsed
        } else {
          items.value = []
        }
      } catch (error) {
        console.error('Error loading cart from storage:', error)
        items.value = []
      }
    }
  }
  
  // Получение товаров для текущего города
  const itemsForCurrentCity = computed(() => {
    const selectedCity = localStorage.getItem('selectedCity')
    if (!selectedCity) return items.value
    
    try {
      const city = JSON.parse(selectedCity)
      return items.value.filter(item => item.city === city.id)
    } catch {
      return items.value
    }
  })
  
  // Создание заказа
  const createOrder = async (deliveryAddress: string, phoneNumber?: string, comment?: string): Promise<{ success: boolean; orderId?: number; error?: string }> => {
    try {
      const { user } = useTelegram()
      if (!user.value) {
        return { success: false, error: 'Пользователь не авторизован' }
      }
      
      // Подготовка данных для отправки
      const orderItems = items.value.map(item => ({
        product_id: parseInt(item.productId),
        quantity: item.quantity,
        // Предполагаем, что первый вкус в списке - это выбранный
        flavor_id: item.flavors.length > 0 ? parseInt(item.flavors[0].id) : undefined
      }))
      
      const orderData: CreateOrderRequest = {
        user_id: user.value.id,
        items: orderItems,
        delivery_address: deliveryAddress,
        phone_number: phoneNumber,
        comment: comment,
        total_amount: totalPrice.value
      }
      
      const response = await apiService.createOrder(orderData)
      
      if (response.success && response.data) {
        // Очищаем корзину после успешного оформления заказа
        clearCart()
        return { success: true, orderId: (response.data as OrderResponse).id }
      } else {
        return { success: false, error: response.error || 'Ошибка при создании заказа' }
      }
    } catch (err: any) {
      return { success: false, error: err.message || 'Ошибка при создании заказа' }
    }
  }
  
  // Инициализация
  const init = () => {
    loadCartFromStorage()
  }
  
  return {
    items,
    totalPrice,
    totalItems,
    itemsForCurrentCity,
    addItem,
    removeItem,
    updateQuantity,
    clearCart,
    init,
    saveCartToStorage,
    loadCartFromStorage
  }
})