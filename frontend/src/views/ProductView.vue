<template>
  <div class="product-page">
    <!-- Основной контент -->
    <div class="product-content">
      <!-- Хлебные крошки -->
      <div class="breadcrumbs">
        <span class="breadcrumb-item" @click="goToCatalog">{{ t('catalog.title') }}</span>
        <span class="breadcrumb-separator">/</span>
        <span class="breadcrumb-item active">{{ product?.name || t('product.defaultTitle') }}</span>
      </div>

      <!-- Загрузка -->
      <div v-if="loading" class="loading-state">
        {{ t('product.loading') }}
      </div>

      <!-- Ошибка -->
      <div v-else-if="error" class="error-state">
        {{ error }}
        <button @click="loadProduct" class="retry-btn">{{ t('common.retry') }}</button>
      </div>

      <!-- Товар не найден -->
      <div v-else-if="!product" class="error-state">
        {{ t('product.notFound') }}
      </div>

      <!-- Карточка товара -->
      <div v-else class="product-card">
        <div class="product-main">
          <div class="product-image">
            <img
              v-if="imageUrl && !imageError"
              :src="imageUrl"
              :alt="product?.name || 'Product image'"
              class="product-img"
              @error="handleImageError"
              @load="handleImageLoad"
              loading="lazy"
            >
            <div v-else class="image-placeholder">
              <span class="brand-tag">{{ product?.brand || '' }}</span>
              <div class="image-text">{{ product?.name || 'Нет фото' }}</div>
            </div>
          </div>

          <div class="product-info">
            <h1 class="product-title">{{ product.name }}</h1>
            <div class="product-brand">{{ product.brand }}</div>
            
            <!-- Характеристики -->
            <div class="specs-list">
              <div class="spec-item">
                <span class="spec-label">{{ t('catalog.filterLabels.puffs') }}:</span>
                <span class="spec-value">{{ product.puffs }}</span>
              </div>
              <div class="spec-item">
                <span class="spec-label">{{ t('catalog.filterLabels.strength') }}:</span>
                <span class="spec-value">{{ product.strength }}mg</span>
              </div>
              <div class="spec-item">
                <span class="spec-label">{{ t('product.brand') }}:</span>
                <span class="spec-value">{{ product.brand }}</span>
              </div>
              <div class="spec-item">
                <span class="spec-label">{{ t('product.availability') }}:</span>
                <span class="spec-value" :class="{ 'in-stock': product.isAvailable, 'out-of-stock': !product.isAvailable }">
                  {{ product.isAvailable ? t('product.available') : t('product.notAvailable') }}
                </span>
              </div>
            </div>

            <!-- Цена -->
            <div class="price-section">
              <div class="price">{{ formatPrice(product.price) }} €</div>
              <div class="price-note">{{ t('product.perPiece') }}</div>
            </div>

            <!-- Выбор вкуса -->
            <div v-if="product.flavors && product.flavors.length > 0" class="dropdown-section">
              <div class="dropdown-label">{{ t('product.chooseFlavorLabel') }}</div>
              <div class="custom-dropdown" @click="toggleDropdown">
                <div class="dropdown-selected" :class="{ 'placeholder': !selectedFlavor }">
                  {{ selectedFlavor ? selectedFlavor.name : t('product.clickToChooseFlavor') }}
                  <span class="dropdown-arrow" :class="{ 'open': isDropdownOpen }">▼</span>
                </div>
                <div class="dropdown-menu" v-show="isDropdownOpen" :class="{ 'closing': isClosing }">
                  <div 
                    v-for="flavor in product.flavors" 
                    :key="flavor.id"
                    class="dropdown-item"
                    :class="{ 'active': selectedFlavorId === flavor.id }"
                    @click.stop="selectFlavor(flavor)"
                  >
                    {{ flavor.name }}
                  </div>
                </div>
              </div>
            </div>

            <!-- Количество + кнопка Купить -->
            <div class="cart-actions">
              <div class="quantity-selector">
                <button class="quantity-btn" @click="decrementQuantity" :disabled="!product.isAvailable">−</button>
                <span class="quantity">{{ quantity }}</span>
                <button class="quantity-btn" @click="incrementQuantity" :disabled="!product.isAvailable">+</button>
              </div>
              <button 
                class="buy-btn" 
                :class="{ 'disabled': !canBuy, 'loading': orderLoading }"
                @click="buyNow"
                :disabled="!canBuy || orderLoading"
              >
                {{ orderLoading ? t('product.creating') : (product.isAvailable ? t('product.buy') : t('product.notAvailable')) }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Анимация успеха при добавлении в корзину -->
    <div v-if="showSuccess" class="success-overlay" @click="showSuccess = false">
      <div class="success-animation">
        <div class="success-checkmark">
          <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
            <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none"/>
            <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8"/>
          </svg>
        </div>
        <div class="success-title">
          {{ t('product.addedToCart', { name: product?.name || 'товар' }) }}
        </div>
        <div class="success-subtitle">{{ t('product.connectTitle') }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCitiesStore } from '@/stores/cities'
import { apiService } from '@/services/apiService'
import type { Product } from '@/stores/catalog'

const { t, locale } = useI18n()
const route = useRoute()
const router = useRouter()
const citiesStore = useCitiesStore()

// ── Состояния ────────────────────────────────────────────────
const product          = ref<Product | null>(null)
const loading          = ref(false)
const error            = ref<string | null>(null)
const quantity         = ref(1)
const imageUrl         = ref<string | null>(null)
const imageError       = ref(false)
const showSuccess      = ref(false)
const orderLoading     = ref(false)

// Выбор вкуса
const selectedFlavorId = ref<string | null>(null)
const selectedFlavor   = ref<any>(null)
const isDropdownOpen   = ref(false)
const isClosing        = ref(false)

// ── Вычисляемые ──────────────────────────────────────────────
const canBuy = computed(() => {
  if (!product.value?.isAvailable) return false
  if (product.value.flavors && product.value.flavors.length > 0) {
    return !!selectedFlavorId.value
  }
  return true
})

// ── Функции ──────────────────────────────────────────────────
const formatPrice = (price: number) => price.toFixed(2)

const loadProductImage = () => {
  if (!product.value?.image) {
    imageError.value = true
    imageUrl.value = null
    return
  }

  if (product.value.image.startsWith('http') || product.value.image.startsWith('//')) {
    imageUrl.value = product.value.image
  } else {
    // Предполагаем, что это file_id → используем тот же эндпоинт, что и в списке товаров
    imageUrl.value = `${apiService.getBaseUrl()}/api/api/get_image/${product.value.image}`
  }
}

const loadProduct = async () => {
  const productId = Number(route.params.id)
  if (!productId) {
    error.value = 'Не указан ID товара'
    return
  }

  loading.value = true
  error.value = null

  try {
    const response = await apiService.getProductById(productId, locale.value as string)
    
    if (response.success && response.data) {
      const apiProduct = response.data as any
      product.value = {
        id: String(apiProduct.id),
        name: apiProduct.name,
        price: apiProduct.price,
        image: apiProduct.image,
        puffs: apiProduct.puffs,
        strength: apiProduct.strength,
        brand: apiProduct.brand,
        vendorId: String(apiProduct.seller_id || ''),
        city: String(apiProduct.city_id || ''),
        flavors: apiProduct.flavors?.map((f: any) => ({
          id: String(f.id),
          name: f.name,
          isAvailable: true
        })) || [],
        isAvailable: apiProduct.in_stock,
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      }

      // Загружаем изображение после получения данных о продукте
      loadProductImage()
    } else {
      error.value = response.error || t('product.loadError')
    }
  } catch (err: any) {
    console.error('Error loading product:', err)
    error.value = err.message || t('product.loadError')
  } finally {
    loading.value = false
  }
}

const handleImageError = () => {
  console.warn('Ошибка загрузки изображения товара:', product.value?.id, imageUrl.value)
  imageError.value = true
}

const handleImageLoad = () => {
  console.log('Изображение товара успешно загружено:', product.value?.id)
  imageError.value = false
}

const incrementQuantity = () => quantity.value++
const decrementQuantity = () => { if (quantity.value > 1) quantity.value-- }

const selectFlavor = (flavor: any) => {
  selectedFlavorId.value = flavor.id
  selectedFlavor.value = flavor
  closeDropdown()
}

const closeDropdown = () => {
  if (isDropdownOpen.value) {
    isClosing.value = true
    setTimeout(() => {
      isDropdownOpen.value = false
      isClosing.value = false
    }, 200)
  }
}

const toggleDropdown = () => {
  isDropdownOpen.value ? closeDropdown() : (isDropdownOpen.value = true, isClosing.value = false)
}

const buyNow = async () => {
  if (!canBuy.value) {
    if (!product.value?.isAvailable) {
      alert(t('product.notAvailableAlert') || 'Товар временно недоступен')
    } else if (product.value?.flavors?.length && !selectedFlavor.value) {
      alert(t('product.selectFlavorAlert') || 'Выберите вкус')
    }
    return
  }

  if (!citiesStore.selectedCity?.id) {
    alert('Пожалуйста, выберите город')
    return
  }

  orderLoading.value = true

  try {
    const orderData = {
      product_id: Number(product.value!.id),
      flavors: selectedFlavor.value ? [{
        flavor_id: Number(selectedFlavor.value.id),
        quantity: quantity.value
      }] : []
    }

    console.log('📦 Отправка заказа:', orderData)

    const response = await apiService.createOrder(orderData)

    if (response.success) {
      showSuccess.value = true
      console.log('✅ Заказ создан успешно:', response.data)
      setTimeout(() => {
        showSuccess.value = false
      }, 5000)
    } else {
      console.error('❌ Ошибка создания заказа:', response.error)
      alert(response.error || 'Не удалось создать заказ')
    }
  } catch (err: any) {
    console.error('🔥 Ошибка при создании заказа:', err)
    alert('Произошла ошибка при создании заказа')
  } finally {
    orderLoading.value = false
  }
}

// Навигация
const goToCatalog = () => router.push('/')

// Закрытие дропдауна по клику вне
const handleClickOutside = (e: MouseEvent) => {
  const dropdown = document.querySelector('.custom-dropdown')
  if (dropdown && !dropdown.contains(e.target as Node) && isDropdownOpen.value) {
    closeDropdown()
  }
}

// ── Жизненный цикл ───────────────────────────────────────────
watch(locale, () => { if (product.value) loadProduct() })

onMounted(async () => {
  if (citiesStore.cities.length === 0) await citiesStore.init()
  await loadProduct()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.product-page {
  min-height: 100vh;
  background: #000000;
  color: #ffffff;
  padding: 16px;
  margin-top: -30px;
  margin-bottom: 35px;
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 24px;
  font-size: 14px;
}

.breadcrumb-item {
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: color 0.2s ease;
}

.breadcrumb-item:hover {
  color: rgba(255, 255, 255, 0.9);
}

.breadcrumb-item.active {
  color: #ffffff;
}

.breadcrumb-separator {
  color: rgba(255, 255, 255, 0.3);
}

.loading-state,
.error-state {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 16px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
}

.error-state {
  color: #ff4444;
}

.retry-btn {
  margin-top: 12px;
  background: #3390ec;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
}

.product-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 24px;
  padding: 20px;
  margin-bottom: 32px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.product-main {
  display: flex;
  gap: 24px;
}

@media (max-width: 768px) {
  .product-main {
    flex-direction: column;
  }
}

.product-image {
  flex-shrink: 0;
  width: 200px;
}

.product-img {
  width: 100%;
  height: 200px;
  object-fit: cover;
  border-radius: 20px;
}

.image-placeholder {
  aspect-ratio: 1;
  background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.brand-tag {
  position: absolute;
  top: 12px;
  left: 12px;
  background: rgba(255, 255, 255, 0.15);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.image-text {
  font-size: 24px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.2);
  text-transform: uppercase;
  letter-spacing: 4px;
  transform: rotate(-15deg);
}

.product-info {
  flex: 1;
}

.product-title {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.product-brand {
  font-size: 18px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 20px;
}

.specs-list {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  padding: 16px;
  margin-bottom: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.spec-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.spec-item:last-child {
  border-bottom: none;
}

.spec-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.spec-value {
  font-weight: 600;
  font-size: 15px;
}

.spec-value.in-stock {
  color: #4caf50;
}

.spec-value.out-of-stock {
  color: #ff4444;
}

.price-section {
  margin-bottom: 20px;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.price {
  font-size: 36px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: -0.02em;
}

.price-note {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.5);
}

.dropdown-section {
  margin-bottom: 20px;
}

.dropdown-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 10px;
}

.custom-dropdown {
  position: relative;
  width: 100%;
  cursor: pointer;
}

.dropdown-selected {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px 20px;
  color: #ffffff;
  font-size: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: all 0.2s ease;
}

.dropdown-selected:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.dropdown-selected.placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.dropdown-arrow {
  font-size: 12px;
  opacity: 0.8;
  transition: transform 0.3s ease;
  display: inline-block;
}

.dropdown-arrow.open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  bottom: calc(100% + 5px);
  left: 0;
  right: 0;
  background: #1c1c1e;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  max-height: 250px;
  overflow-y: auto;
  z-index: 1;
  box-shadow: 0 -10px 25px rgba(0, 0, 0, 0.5);
  animation: slideDown 0.2s ease forwards;
}

.dropdown-menu.closing {
  animation: slideUp 0.2s ease forwards;
}

.dropdown-item {
  padding: 15px 20px;
  color: #ffffff;
  font-size: 15px;
  transition: all 0.2s ease;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.dropdown-item:last-child {
  border-bottom: none;
}

.dropdown-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.dropdown-item.active {
  background: #3390ec;
  color: white;
}

.cart-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.quantity-selector {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.quantity-btn {
  width: 40px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 20px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 12px;
  transition: background 0.2s ease;
}

.quantity-btn:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
}

.quantity-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.quantity {
  min-width: 40px;
  text-align: center;
  font-weight: 600;
  font-size: 16px;
}

.buy-btn {
  flex: 1;
  background: #ffffff;
  border: none;
  color: #000000;
  padding: 0 24px;
  height: 48px;
  border-radius: 14px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.buy-btn:hover:not(.disabled) {
  background: rgba(255, 255, 255, 0.9);
  transform: scale(0.98);
}

.buy-btn.disabled {
  background: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  background: #1c1c1e;
  border-radius: 24px;
  width: 90%;
  max-width: 400px;
  max-height: 80vh;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  animation: slideUp 0.3s ease;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
}

.modal-close {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #ffffff;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  cursor: pointer;
  transition: background 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.15);
}

.cities-list {
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.city-item {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #ffffff;
  padding: 14px 16px;
  border-radius: 12px;
  font-size: 16px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.city-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.city-item.active {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
}

/* ──────────────────────────────────────────────────────────────
   НОВЫЕ СТИЛИ — АНИМАЦИЯ УСПЕХА (в твоём тёмном стиле)
─────────────────────────────────────────────────────────────── */

.success-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.82);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
  animation: fadeIn 0.25s ease;
}

.success-animation {
  text-align: center;
  color: white;
  padding: 40px 32px;
  background: rgba(30, 30, 35, 0.92);
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  max-width: 360px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.7);
}

.success-checkmark {
  width: 90px;
  height: 90px;
  margin: 0 auto 20px;
}

.checkmark {
  width: 100%;
  height: 100%;
}

.checkmark__circle {
  stroke-dasharray: 166;
  stroke-dashoffset: 166;
  stroke-width: 3;
  stroke-miterlimit: 10;
  stroke: #27ae60;
  fill: none;
  animation: stroke 0.6s cubic-bezier(0.65, 0, 0.45, 1) forwards;
}

.checkmark__check {
  stroke-dasharray: 48;
  stroke-dashoffset: 48;
  stroke: #27ae60;
  stroke-width: 3;
  stroke-linecap: round;
  stroke-linejoin: round;
  animation: stroke 0.3s cubic-bezier(0.65, 0, 0.45, 1) 0.6s forwards;
}

.success-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 8px;
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards 1s;
}

.success-subtitle {
  font-size: 16px;
  color: rgba(255,255,255,0.8);
  opacity: 0;
  animation: fadeInUp 0.6s ease forwards 1.2s;
}

/* Анимации (уже есть в твоём коде fadeIn/slideUp, добавляем недостающие) */
@keyframes stroke {
  100% { stroke-dashoffset: 0; }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* Уже существующие анимации из твоего кода */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideDown {
  from { 
    opacity: 0;
    transform: translateY(10px);
  }
  to { 
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes slideUp {
  from { 
    opacity: 1;
    transform: translateY(0);
  }
  to { 
    opacity: 0;
    transform: translateY(10px);
  }
}
</style>