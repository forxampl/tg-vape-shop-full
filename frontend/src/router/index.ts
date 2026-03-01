import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/CatalogView.vue'),
      meta: { titleKey: 'catalog.title' }
    },
    {
      path: '/cabinet',
      name: 'cabinet',
      component: () => import('@/views/CabinetView.vue'),
      meta: { titleKey: 'cabinet.title' }
    },
    {
      path: '/product/:id',
      name: 'product',
      component: () => import('@/views/ProductView.vue'),
      meta: { title: 'Товар' }
    },
    {
      path: '/order',
      name: 'order',
      component: () => import('@/views/OrderView.vue'),
      meta: { titleKey: 'order.title' }
    },
  ]
})

export default router