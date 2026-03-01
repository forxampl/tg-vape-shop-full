import { ref, computed, onMounted } from 'vue'
import { telegramService } from '@/services/telegramService'  // подставь свой путь

export const useTelegram = () => {
  const isReady = ref(false)
  const initError = ref<string | null>(null)

  onMounted(async () => {
    console.log('🔄 useTelegram mounted');
    
    try {
      const success = await telegramService.waitForInit(8000)
      isReady.value = success
      
      console.log('📊 Telegram state after init:', {
        success,
        user: telegramService.user,
        avatarUrl: telegramService.avatarUrl,
        isMock: telegramService.isMock,
      });

      if (!telegramService.user) {
        initError.value = 'Нет данных пользователя Telegram';
        console.warn('⚠️ Нет данных пользователя Telegram');
      } else if (telegramService.isMock) {
        console.warn('⚠️ MOCK-режим');
      } else {
        console.log('✅ Реальный Telegram Mini App');
      }
    } catch (error) {
      initError.value = error instanceof Error ? error.message : 'Ошибка инициализации';
      console.error('❌ Ошибка инициализации Telegram:', error);
    }
  })

  const enableMockMode = () => {
    if (import.meta.env.DEV) {
      // можно реализовать mock если нужно
    }
  }

  return {
    tg: computed(() => telegramService.tgInstance),
    user: computed(() => telegramService.user || null),
    avatarUrl: computed(() => telegramService.avatarUrl || null),
    fullName: computed(() => telegramService.getFullName()),
    initials: computed(() => telegramService.getInitials()),
    userId: computed(() => telegramService.user?.id?.toString() || ''),
    
    isMock: computed(() => telegramService.isMock),
    isReady,
    initError,

    closeApp: () => telegramService.tgInstance?.close?.(),
    expand: () => telegramService.tgInstance?.expand?.(),
    waitForInit: (timeout = 8000) => telegramService.waitForInit(timeout),
    enableMockMode,
  }
}