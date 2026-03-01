<template>
  <div class="product-card" @click="handleClick">
    <div class="product-image">
      <!-- Пытаемся загрузить изображение -->
      <img 
        v-if="!imageError && imageUrl"
        :src="imageUrl"
        :alt="product.name"
        class="product-img"
        @error="handleImageError"
        @load="handleImageLoad"
        loading="lazy"
      >
      <!-- Плейсхолдер если нет изображения или ошибка -->
      <div v-else class="image-placeholder">📦</div>
      
      <div v-if="!product.isAvailable" class="out-of-stock-badge">
        {{ t('product.outOfStockLabel') }}
      </div>
    </div>
    
    <div class="product-info">
      <div class="product-specs">
        <span class="spec-item">
          <div class="product-footer">
            <div class="product-price">
              <span class="price-amount">{{ product.price }} €</span>
            </div>
          </div>
          <span class="spec-unit">·</span>
          <span class="spec-label">{{ product.puffs }}</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCartStore } from '@/stores/cart'
import { apiService } from '@/services/apiService'
import type { Product } from '@/stores/catalog'

const { t } = useI18n()

const props = defineProps<{ product: Product }>()

const router = useRouter()
const cartStore = useCartStore()

const imageError = ref(false)
const imageLoading = ref(false)
const imageUrl = ref<string | null>(null)

// Загружаем изображение если есть file_id
const loadImage = async () => {
  if (!props.product.image) {
    imageError.value = true
    return
  }
  
  // Если это уже прямая ссылка (начинается с http)
  if (props.product.image.startsWith('http')) {
    imageUrl.value = props.product.image
    return
  }
  
  // Если это file_id, используем существующий эндпоинт для получения изображения
  imageUrl.value = `${apiService.getBaseUrl()}/api/api/get_image/${props.product.image}`
  imageLoading.value = false
}

onMounted(() => {
  loadImage()
})

const handleImageError = () => {
  console.log('Image failed to load for product:', props.product.id)
  imageError.value = true
}

const handleImageLoad = () => {
  console.log('Image loaded for product:', props.product.id)
  imageError.value = false
}

const handleClick = () => {
  router.push(`/product/${props.product.id}`)
}

const addToCart = (e: Event) => {
  e.stopPropagation()
  
  if (!props.product.isAvailable) return
  
  // Подготовка элемента корзины
  const cartItem = {
    productId: props.product.id,
    name: props.product.name,
    price: props.product.price,
    image: props.product.image,
    flavors: props.product.flavors?.map(f => ({
      id: f.id,
      name: f.name,
      quantity: 1,
      isAvailable: f.isAvailable
    })) || [],
    city: props.product.city,
    vendorId: props.product.vendorId
  }
  
  cartStore.addItem(cartItem)
  
  console.log('Добавлен в корзину:', props.product)
  alert(`Товар "${props.product.name}" добавлен в корзину!`)
}
</script>

<style scoped>
.product-card {
  background: #0f0f0fc7;
  border-radius: 12px;
  border: .5px solid #272727;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.product-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
}

.product-card:active {
  transform: translateY(0);
}

.product-image {
  position: relative;
  width: 100%;
  height: 200px;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 20px;
  background: #005B90;
  display: flex;
  align-items: center;
  justify-content: center;
}

.product-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  font-size: 60px;
  color: #999999;
}

.out-of-stock-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: rgba(255, 68, 68, 0.9);
  color: white;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 500;
  z-index: 1;
}

.product-info h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #fafafa;
}

.product-specs {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  justify-content: space-between;
  text-align: center;
  padding-left: 15px;
}

.spec-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.spec-label {
  font-weight: 600;
  color: #fafafa;
}

.spec-unit {
  font-size: 16px;
  color: #fafafa;
  text-align: center;
  font-weight: 800;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.price-amount {
  font-size: 16px;
  font-weight: 700;
  color: #fafafa;
}

.add-to-cart-btn {
  background: #3390ec;
  color: #ffffff;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.add-to-cart-btn:hover {
  opacity: 0.9;
}

.add-to-cart-btn.disabled,
.add-to-cart-btn:disabled {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.3);
  cursor: not-allowed;
}
</style>