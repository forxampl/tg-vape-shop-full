<template>
  <div class="order">
    <h1>{{ t('order.checkoutTitle') }}</h1>
    <p>{{ t('order.placeholder') }}</p>
    <button @click="goBack">{{ t('common.back') }}</button>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const router = useRouter()

const goBack = () => {
  router.push('/')
}
</script>

<style scoped>
.order {
  padding: 20px;
}

button {
  background: #666;
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 20px;
}

button:hover {
  opacity: 0.9;
}
</style>