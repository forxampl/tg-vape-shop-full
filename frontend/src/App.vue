<template>
  <div id="app">
    <Header />
    
    <main>
      <router-view />
    </main>
    
    <Footer />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Header from '@/components/layout/Header.vue'
import Footer from '@/components/layout/Footer.vue'
import { useCitiesStore } from '@/stores/cities'

const citiesStore = useCitiesStore()

onMounted(async () => {
  // Инициализируем города при запуске приложения
  await citiesStore.init()
})
</script>

<style>
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
  padding-top: var(--app-header-height, 104px);
  width: 100%;
  background: #000;
}
</style>