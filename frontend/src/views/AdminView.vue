<template>
  <div class="admin">
    <h1>{{ t('admin.panelTitle') }}</h1>
    <p>{{ t('admin.description') }}</p>
    <button @click="goBack">{{ t('common.goHome') }}</button>
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
.admin {
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