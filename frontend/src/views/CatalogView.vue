<template>
  <div class="catalog">
    <div v-if="catalogStore.loading" class="loading">
      {{ t('catalog.loadingProducts') }}
    </div>

    <div v-else-if="catalogStore.error" class="error">
      {{ catalogStore.error }}
    </div>

    <div v-else-if="catalogStore.filteredProducts.length === 0" class="no-products">
      {{ t('catalog.noAvailableProducts') }}
    </div>

    <TransitionGroup
      v-else
      name="product-list"
      tag="div"
      class="products"
    >
      <ProductCard
        v-for="product in catalogStore.filteredProducts"
        :key="product.id"
        :product="product"
      />
    </TransitionGroup>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import ProductCard from '@/components/catalog/ProductCard.vue'
import { useCatalogStore } from '@/stores/catalog'
import { useCitiesStore } from '@/stores/cities'

const { t } = useI18n()
const route = useRoute()
const catalogStore = useCatalogStore()
const citiesStore = useCitiesStore()

onMounted(async () => {
  const cityFromRoute = route.query.city
  if (cityFromRoute && citiesStore.cities.length > 0) {
    const cityId = String(cityFromRoute)
    const city = citiesStore.cities.find(c => c.id === cityId)
    if (city) {
      citiesStore.selectCity(city.id)
    }
  }

  await catalogStore.init()
})
</script>

<style scoped>
.catalog {
  padding: 20px;
  margin-top: 20px;
  background-color: #000000;
  min-height: calc(100vh - 140px);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #ffffff;
  font-size: 16px;
}

.error {
  text-align: center;
  padding: 40px;
  color: #ff4444;
  font-size: 16px;
  background: rgba(255, 68, 68, 0.1);
  border-radius: 12px;
  margin: 20px;
}

.no-products {
  text-align: center;
  padding: 40px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 16px;
}

.products {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 35px;
}

@media (min-width: 768px) {
  .products {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1024px) {
  .products {
    grid-template-columns: repeat(4, 1fr);
  }
}

/* Плавная анимация для карточек */
.product-list-enter-active,
.product-list-leave-active {
  transition: all 0.4s ease;
}

.product-list-enter-from,
.product-list-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.product-list-move {
  transition: transform 0.4s ease;
}
</style>