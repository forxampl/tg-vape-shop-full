<template>
  <footer class="app-footer">
    <nav class="footer-nav">
      <button
        v-for="item in menuItems"
        :key="item.id"
        class="nav-item"
        :class="{ active: item.id === activeItem }"
        @click="navigateTo(item.path)"
      >
        <span class="nav-icon">
          <component :is="item.icon" />
        </span>
        <span class="nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </footer>
</template>

<script setup lang="ts">
import UserIcon from '@/components/icons/UserIcon.vue'
import CartIcon from '@/components/icons/CartIcon.vue'
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

const activeItem = computed(() => {
  if (route.path === '/') return 'catalog'
  if (route.path.startsWith('/cabinet')) return 'cabinet'
  if (route.path.startsWith('/admin')) return 'admin'
  return ''
})

const menuItems = computed(() => [
  {
    id: 'catalog',
    icon: CartIcon,
    label: t('catalog.title'),
    path: '/'
  },
  {
    id: 'cabinet',
    icon: UserIcon,
    label: t('cabinet.title'),
    path: '/cabinet'
  }
])

const navigateTo = (path: string) => {
  router.push(path)
}
</script>

<style lang="scss" scoped>
.app-footer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 90;
  display: flex;
  justify-content: center;
  pointer-events: none; /* кликаются только элементы внутри панели */
}

.footer-nav {
  position: relative;
  display: flex;
  gap: 12px;
  width: 100%;
  background: rgba(0, 0, 0, 0.05); 
  box-shadow:
    0 -8px 30px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  pointer-events: auto;
}

.nav-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  color: rgba(255, 255, 255, 0.55); /* цвет неактивной иконки и текста */
  transition: all 0.18s ease;
  background: transparent;
  border: none;
  cursor: pointer;
  border-radius: 999px;
  
  &.active {
    color: #ffffff; /* активная иконка и текст — белые */
    
    .nav-icon {
      transform: translateY(-1px);
    }
  }
  
  .nav-icon {
    font-size: 20px;
    margin-bottom: 4px;
    transition: transform 0.2s ease;
  }
  
  .nav-label {
    font-size: 11px;
    font-weight: 600;
  }
}
</style>