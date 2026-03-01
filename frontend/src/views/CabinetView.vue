<template>
  <div class="cabinet">
    <!-- Предупреждение о проблемах -->
    <div v-if="initError" class="error-warning">
      ❌ {{ initError }}
    </div>

    <!-- Предупреждение о mock-режиме -->
    <div v-else-if="isMock" class="mock-warning">
      ⚠️ {{ t('cabinet.mockMode') }}<br>
      <small>{{ t('cabinet.mockHint') }}</small>
    </div>

    <!-- Карточка профиля -->
    <section class="profile-card">
      <div class="avatar">
        <div 
          class="avatar-inner"
          :style="avatarStyle"
        >
          <span v-if="useInitials" class="avatar-initials">{{ displayInitials }}</span>
        </div>
      </div>

      <div class="profile-info">
        <div class="profile-name">{{ displayName }}</div>
        <div class="profile-username">@{{ displayUsername }}</div>
        <div v-if="formattedUserRole" class="profile-role" :class="roleClass">
          {{ formattedUserRole }}
        </div>
      </div>
    </section>

    <!-- Настройки -->
    <section class="settings-card">
      <div class="settings-row" @click="toggleNotifications">
        <span class="settings-label">{{ t('cabinet.notifications') }}</span>
        <button
          type="button"
          class="switch"
          :class="{ 'switch--on': notificationsEnabled }"
          @click.stop="toggleNotifications"
          :disabled="notificationsLoading"
        >
          <span class="switch-thumb" />
        </button>
      </div>

      <div class="settings-row" @click="toggleLocale">
        <span class="settings-label">{{ t('cabinet.language') }}</span>
        <div class="lang-toggle">
          <div
            class="lang-toggle__thumb"
            :class="{ 'lang-toggle__thumb--lv': currentLocale === 'lv' }"
          />
          <button
            type="button"
            class="lang-toggle__btn"
            :class="{ 'lang-toggle__btn--active': currentLocale === 'ru' }"
            @click.stop="setLocale('ru')"
          >
            RU
          </button>
          <button
            type="button"
            class="lang-toggle__btn"
            :class="{ 'lang-toggle__btn--active': currentLocale === 'lv' }"
            @click.stop="setLocale('lv')"
          >
            LV
          </button>
        </div>
      </div>
    </section>

    <!-- Вопрос / жалоба -->
    <button type="button" class="support-button" @click="showSupportModal = true">
      {{ t('cabinet.supportButton') }}
    </button>

    <!-- История заказов -->
    <section class="orders-section">
      <div class="orders-header">
        <h3 class="orders-title">{{ t('order.history') }}</h3>
        <span class="orders-count">{{ t('order.totalOrders') }} {{ orders.length }}</span>
      </div>

      <div class="orders-list" v-if="orders.length">
        <div v-for="order in orders" :key="order.id" class="order-card">
          <div class="order-icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none">
              <path d="M9 5H7C5.89543 5 5 5.89543 5 7V19C5 20.1046 5.89543 21 7 21H17C18.1046 21 19 20.1046 19 19V7C19 5.89543 18.1046 5 17 5H15M9 5C9 3.89543 9.89543 3 11 3H13C14.1046 3 15 3.89543 15 5M9 5C9 6.10457 9.89543 7 11 7H13C14.1046 7 15 6.10457 15 5" stroke="#ffffff" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
          
          <div class="order-info">
            <!-- Номер заказа и название товара -->
            <div class="order-name">
              <span class="order-number">{{ t('order.orderNumber', { id: order.id }) }}</span>
              {{ order.productName }}
            </div>
            
            <!-- Дата заказа -->
            <div class="order-date">{{ formatDate(order.createdAt) }}</div>
          </div>

          <div class="order-amounts">
            <!-- Цена -->
            <div class="amount-primary">{{ formatPrice(order.totalPrice) }}</div>
          </div>
        </div>
      </div>

      <div class="no-orders" v-else>
        {{ t('order.noOrders') }}
      </div>
    </section>

    <SupportModal 
      v-model="showSupportModal"
      @success="handleSupportSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useTelegram } from '@/composables/useTelegram'
import { apiService } from '@/services/apiService'
import SupportModal from '@/components/modal/SupportModal.vue'

// Интерфейс для заказа
interface OrderFlavor {
  flavor_id: number
  flavor_name: string
  quantity: number
}

interface Order {
  id: number
  product_id: number
  productName: string
  totalPrice: number
  createdAt: string
  flavors?: OrderFlavor[]
  status?: string
}

const { t, locale } = useI18n()

const showSupportModal = ref(false)

// Добавляем обработчик успеха
const handleSupportSuccess = (message: string) => {
  console.log('Success:', message)
  alert(message)
}

const avatarStyle = computed(() => {
  if (!telegramAvatarUrl.value || useInitials.value) {
    return {};
  }
  return {
    backgroundImage: `url(${telegramAvatarUrl.value})`,
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
  };
});

// Telegram composable
const {
  user: telegramUser,
  avatarUrl: telegramAvatarUrl,
  fullName: telegramFullName,
  initials: telegramInitials,
  isMock,
  waitForInit,
  initError,
} = useTelegram()

// Состояние для fallback на инициалы
const useInitials = ref(false)

// Данные из бэкенда
const profile = ref({
  id: 0,
  username: '',
  full_name: '',
  role: '',
  language: '',
})

// ============= УВЕДОМЛЕНИЯ (BROADCAST) =============
const notificationsEnabled = ref(false)
const notificationsLoading = ref(false)

// Загружаем состояние уведомлений отдельно
const loadBroadcastState = async () => {
  try {
    const response = await apiService.getBroadcastState()
    console.log('Broadcast state response:', response)
    
    if (response.success && response.data) {
      notificationsEnabled.value = response.data.enabled
      console.log('Broadcast enabled from server:', notificationsEnabled.value)
    }
  } catch (e) {
    console.error('Error loading broadcast state:', e)
  }
}

const toggleNotifications = async () => {
  if (notificationsLoading.value) return
  
  const newState = !notificationsEnabled.value
  console.log('Toggling broadcast to:', newState)
  
  notificationsLoading.value = true
  
  try {
    // Отправляем новое состояние на сервер
    const response = await apiService.toggleBroadcast(newState)
    
    if (response.success) {
      // Если сервер подтвердил, обновляем локальное состояние
      notificationsEnabled.value = newState
      console.log('Broadcast updated successfully on server')
    } else {
      console.error('Failed to update broadcast:', response.error)
    }
  } catch (e) {
    console.error('Error toggling broadcast:', e)
  } finally {
    notificationsLoading.value = false
  }
}

// Вычисляемые свойства
const displayName = computed(() => {
  return profile.value.full_name || telegramFullName.value || t('roles.user')
})

const displayUsername = computed(() => {
  return profile.value.username || telegramUser.value?.username || 'username'
})

const displayInitials = computed(() => {
  return telegramInitials.value || '?'
})

// Маппинг ролей
const roleKeyMap: Record<string, string> = {
  'user': 'roles.user',
  'seller': 'roles.seller',
  'admin': 'roles.admin',
  'super_admin': 'roles.super_admin',
  'superadmin': 'roles.super_admin',
  'super admin': 'roles.super_admin',
  'owner': 'roles.owner',
}

const formattedUserRole = computed(() => {
  const rawRole = profile.value.role?.toLowerCase().trim() || ''
  const key = roleKeyMap[rawRole] ?? Object.entries(roleKeyMap).find(([k]) => rawRole.includes(k) || k.includes(rawRole))?.[1]
  if (key) return t(key)
  return rawRole ? rawRole.charAt(0).toUpperCase() + rawRole.slice(1) : ''
})

const roleClass = computed(() => {
  const role = profile.value.role?.toLowerCase() || ''
  if (role.includes('super') || role.includes('owner')) return 'role-super'
  if (role.includes('admin')) return 'role-admin'
  if (role.includes('seller')) return 'role-seller'
  return 'role-user'
})

// Обработчики аватарки
const onAvatarError = () => {
  console.warn('Не удалось загрузить аватарку → показываем инициалы')
  useInitials.value = true
}

const onAvatarLoad = () => {
  console.log('Аватарка успешно загружена')
  useInitials.value = false
}

// Сброс при смене пользователя
watch(() => telegramUser.value?.id, () => {
  console.log('Telegram user changed, resetting avatar state')
  useInitials.value = false
})

// Язык
const currentLocale = computed(() => locale.value as 'ru' | 'lv')

const setLocale = async (nextLocale: 'ru' | 'lv') => {
  if (nextLocale === locale.value) return; // уже выбран — ничего не делаем

  locale.value = nextLocale;

  try {
    const res = await apiService.updateLanguage(nextLocale);
    if (!res.success) {
      console.warn('Не удалось сохранить язык на сервере:', res.error);
    }

    window.location.reload();
  } catch (e) {
    console.error('Ошибка при смене языка:', e);
    window.location.reload();
  }
};

const toggleLocale = () => {
  const next = currentLocale.value === 'ru' ? 'lv' : 'ru';
  setLocale(next);
};

// Форматирование цены
const formatPrice = (price: number) => {
  return `${price.toFixed(2)} €`
}

// Форматирование даты
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return new Intl.DateTimeFormat(locale.value, {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

// Заказы
const orders = ref<Order[]>([])

const loadProfile = async () => {
  try {
    const response = await apiService.getCurrentUser()
    console.log('Profile response:', response)
    
    if (response.success && response.data) {
      profile.value = response.data
      console.log('Profile loaded from server:', profile.value)
      
      if (profile.value.language) locale.value = profile.value.language as 'ru' | 'lv'
    }
  } catch (e) {
    console.error('Error loading profile:', e)
  }
}

const loadOrders = async () => {
  try {
    const response = await apiService.getUserOrders()
    console.log('Orders response:', response)
    
    if (response.success && response.data) {
      orders.value = response.data.map((order: any) => ({
        id: order.id,
        product_id: order.product_id,
        productName: order.product_name || t('order.unknownProduct'),
        totalPrice: order.total_price || 0,
        createdAt: order.created_at,
        flavors: order.flavors || [], // Массив вкусов из ответа API
        status: order.status || 'pending'
      }))
    }
  } catch (e) {
    console.error('Error loading orders:', e)
  }
}

// Загружаем данные при монтировании
onMounted(async () => {
  console.log('=== CABINET MOUNTED ===')
  await waitForInit(8000)
  
  if (telegramUser.value) {
    await loadProfile() // Загружаем основные данные с сервера
    await loadBroadcastState() // Загружаем состояние уведомлений
    await loadOrders() // Загружаем заказы
  }
  
  console.log('Telegram avatar URL:', telegramAvatarUrl.value)
})
</script>

<style scoped>
.cabinet {
  padding: 20px 20px 96px;
  background-color: #000000;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.error-warning {
  background: #ff4444;
  color: white;
  padding: 14px 16px;
  border-radius: 16px;
  margin: 12px 0;
  text-align: center;
  font-weight: 600;
  font-size: 15px;
}

.mock-warning {
  background: #ff4444;
  color: white;
  padding: 14px 16px;
  border-radius: 16px;
  margin: 12px 0;
  text-align: center;
  font-weight: 600;
  font-size: 15px;
}

.profile-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 16px;
  background: #111111;
  border-radius: 24px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
}

.avatar {
  width: 96px;
  height: 96px;
  border-radius: 24px;
  background: linear-gradient(145deg, #2d2d2d, #111111);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-inner {
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: #2f2f2f;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-size: 28px;
  font-weight: 600;
  letter-spacing: 0.03em;
}

.profile-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.profile-name {
  font-size: 20px;
  font-weight: 600;
}

.profile-username {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.settings-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 18px 25px;
  border-radius: 18px;
  border: solid 1px #4a5565a4;
  background: rgba(255, 255, 255, 0.1);
  transition: transform 0.1s ease;
}

.settings-row:hover {
  transform: scale(1.01);
  cursor: pointer;
}

.settings-label {
  font-size: 15px;
  font-weight: 500;
}

.switch {
  position: relative;
  width: 54px;
  height: 30px;
  border-radius: 999px;
  border: none;
  padding: 0;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background 0.18s ease;
}

.switch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.switch-thumb {
  position: absolute;
  left: 4px;
  width: 22px;
  height: 22px;
  border-radius: 999px;
  background: #ffffff;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.6);
  transition: transform 0.18s ease;
}

.switch--on {
  background: #27ae60;
}

.switch--on .switch-thumb {
  transform: translateX(20px);
}

.lang-toggle {
  position: relative;
  display: inline-flex;
  align-items: center;
  padding: 4px;
  border-radius: 8px;
  background: #111111;
}

.lang-toggle__thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: calc(50% - 3px);
  height: calc(100% - 6px);
  border-radius: 8px;
  background: #ffffff;
  transition: transform 0.2s ease;
}

.lang-toggle__thumb--lv {
  transform: translateX(100%);
}

.lang-toggle__btn {
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 44px;
  padding: 4px 10px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.16s ease;
}

.lang-toggle__btn--active {
  color: #000000;
}

.orders-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #101010;
  padding: 20px 18px;
  border-radius: 16px;
  border: solid 1px #4a5565a4;
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.orders-title {
  font-size: 18px;
  font-weight: 600;
  margin: 0;
}

.orders-count {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.orders-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.order-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(74, 85, 101, 0.4);
  border-radius: 20px;
  backdrop-filter: blur(4px);
}

.order-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background: linear-gradient(145deg, #2d2d2d, #1a1a1a);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.order-info {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.order-name {
  font-size: 16px;
  font-weight: 500;
  line-height: 1.3;
  display: flex;
  flex-direction: column;
}

.order-number {
  color: #27ae60;
  font-weight: 600;
  margin-right: 8px;
}

.order-flavors {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.flavor-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.8);
}

.flavor-name {
  color: #27ae60;
  font-weight: 500;
}

.flavor-quantity {
  color: rgba(255, 255, 255, 0.6);
  font-size: 13px;
}

.order-date {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 4px;
}

.order-amounts {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
  min-width: 90px;
  text-align: right;
}

.amount-primary {
  font-size: 18px;
  font-weight: 700;
  color: #27ae60;
}

.no-orders {
  padding: 24px;
  text-align: center;
  color: rgba(255, 255, 255, 0.5);
  font-size: 15px;
}

.support-button {
  width: 100%;
  border: none;
  border-radius: 18px;
  padding: 21px 25px;
  background: #111111;
  color: #ffffff;
  font-size: 15px;
  font-weight: 500;
  text-align: center;
  cursor: pointer;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
  border: solid 1px #4a5565a4;
  background: rgba(255, 255, 255, 0.1);
  transition: transform 0.1s ease;
}

.support-button:hover {
  transform: scale(1.01);
  cursor: pointer;
}

.profile-role {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  margin-top: 4px;
}

.role-super {
  background: linear-gradient(135deg, #ffd700, #ffa500);
  color: #000;
}

.role-admin {
  background: linear-gradient(135deg, #ff4444, #cc0000);
  color: #fff;
}

.role-seller {
  background: linear-gradient(135deg, #4CAF50, #45a049);
  color: #fff;
}

.role-user {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border: 1px solid rgba(255, 255, 255, 0.2);
}
</style>