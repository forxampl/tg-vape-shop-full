<!-- SupportModal.vue -->
<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="close">
      <!-- Блок успешной отправки с анимацией -->
      <div v-if="showSuccess" class="success-overlay">
        <div class="success-animation">
          <div class="success-checkmark">
            <svg class="checkmark" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 52 52">
              <circle class="checkmark__circle" cx="26" cy="26" r="25" fill="none" />
              <path class="checkmark__check" fill="none" d="M14.1 27.2l7.1 7.2 16.7-16.8" />
            </svg>
          </div>
          <div class="success-text">{{ t('support.successMessage') }}</div>
        </div>
      </div>

      <!-- Основная форма (показывается, когда НЕ успех) -->
      <div v-else class="modal-content">
        <!-- Заголовок -->
        <div class="modal-header">
          <h3 class="modal-title">{{ t('support.title') }}</h3>
          <button class="modal-close" @click="close">✕</button>
        </div>

        <!-- Форма -->
        <div class="modal-form">
          <!-- Статус ошибки -->
          <div v-if="error" class="error-message">
            {{ error }}
          </div>

          <!-- Текстовое поле -->
          <div class="form-group">
            <label class="form-label">{{ t('support.message') }}</label>
            <textarea
              v-model="message"
              class="form-textarea"
              :class="{ 'form-textarea--error': validationError }"
              :placeholder="t('support.placeholder')"
              rows="5"
              maxlength="1000"
              @input="clearError"
            ></textarea>
            <div class="form-counter" :class="{ 'form-counter--error': message.length < 10 }">
              {{ message.length }}/1000
            </div>
            <div v-if="validationError" class="validation-error">
              {{ validationError }}
            </div>
          </div>

          <!-- Выбор типа (для UX, на бэк не идёт) -->
          <div class="form-group">
            <label class="form-label">{{ t('support.type') }}</label>
            <div class="type-selector">
              <button
                type="button"
                class="type-btn"
                :class="{ 'type-btn--active': type === 'question' }"
                @click="type = 'question'"
              >
                {{ t('support.question') }}
              </button>
              <button
                type="button"
                class="type-btn"
                :class="{ 'type-btn--active': type === 'complaint' }"
                @click="type = 'complaint'"
              >
                {{ t('support.complaint') }}
              </button>
            </div>
          </div>

          <!-- Кнопки -->
          <div class="form-actions">
            <button
              type="button"
              class="submit-btn"
              :disabled="!isValid || loading"
              @click="submit"
            >
              <span v-if="!loading">{{ t('support.send') }}</span>
              <span v-else class="loader"></span>
            </button>

            <button
              type="button"
              class="cancel-btn"
              @click="close"
              :disabled="loading"
            >
              {{ t('support.cancel') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { apiService } from '@/services/apiService'

const props = defineProps<{
  modelValue: boolean
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
}>()

const { t } = useI18n()

// ── Состояния ────────────────────────────────────────
const message         = ref('')
const type            = ref<'question' | 'complaint'>('question')
const loading         = ref(false)
const error           = ref('')
const validationError = ref('')
const showSuccess     = ref(false)

// ── Валидация ────────────────────────────────────────
const isValid = computed(() => {
  const trimmed = message.value.trim()
  return trimmed.length >= 10 && trimmed.length <= 1000
})

// ── Функции ──────────────────────────────────────────
const clearError = () => {
  error.value = ''
  validationError.value = ''
}

const close = () => {
  if (loading.value) return
  emit('update:modelValue', false)

  setTimeout(() => {
    message.value         = ''
    type.value            = 'question'
    error.value           = ''
    validationError.value = ''
    showSuccess.value     = false
  }, 350)
}

const validateForm = (): boolean => {
  const trimmed = message.value.trim()

  if (trimmed.length < 10) {
    validationError.value = t('support.errorMinLength')
    return false
  }

  if (trimmed.length > 1000) {
    validationError.value = t('support.errorMaxLength')
    return false
  }

  return true
}

const submit = async () => {
  if (!validateForm() || loading.value) return

  loading.value = true
  error.value = ''

  try {
    const textToSend =
      type.value === 'question'
        ? `❓ Вопрос: ${message.value.trim()}`
        : `⚠️ Жалоба: ${message.value.trim()}`

    const response = await apiService.sendFeedback(textToSend)

    if (response.success) {
      showSuccess.value = true
      setTimeout(() => {
        close()
      }, 2200) // сколько секунд показываем анимацию успеха
    } else {
      error.value = response.error || t('support.errorUnknown')
    }
  } catch (err: any) {
    console.error('Error sending feedback:', err)
    error.value = err.message || t('support.errorNetwork')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
  animation: fadeIn 0.2s ease;
}

.modal-content {
  width: 100%;
  max-width: 500px;
  background: #111111;
  border: 1px solid rgba(74, 85, 101, 0.6);
  border-radius: 32px;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.8);
  animation: slideUp 0.3s ease;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(74, 85, 101, 0.3);
}

.modal-title {
  font-size: 20px;
  font-weight: 600;
  color: #ffffff;
  margin: 0;
}

.modal-close {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid rgba(74, 85, 101, 0.6);
  background: rgba(255, 255, 255, 0.05);
  color: #ffffff;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-close:hover {
  background: rgba(255, 255, 255, 0.15);
  transform: scale(1.05);
}

.modal-form {
  padding: 24px;
}

.form-group {
  margin-bottom: 24px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 8px;
}

.form-textarea {
  width: 100%;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(74, 85, 101, 0.6);
  border-radius: 16px;
  color: #ffffff;
  font-size: 15px;
  line-height: 1.5;
  resize: vertical;
  transition: all 0.2s ease;
  font-family: inherit;
}

.form-textarea:focus {
  outline: none;
  border-color: #ffffff;
  background: rgba(255, 255, 255, 0.08);
}

.form-textarea::placeholder {
  color: rgba(255, 255, 255, 0.3);
}

.form-counter {
  text-align: right;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 6px;
}

.form-counter--error {
  color: #ff4444 !important;
}

.type-selector {
  display: flex;
  gap: 12px;
}

.type-btn {
  flex: 1;
  padding: 14px;
  border-radius: 14px;
  border: 1px solid rgba(74, 85, 101, 0.6);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
}

.type-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(1.02);
}

.type-btn--active {
  background: #ffffff;
  color: #000000;
  border-color: #ffffff;
}

.form-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 32px;
}

.submit-btn {
  width: 100%;
  padding: 18px;
  border-radius: 16px;
  border: none;
  background: #27ae60;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 58px;
}

.submit-btn:hover:not(:disabled) {
  background: #2ecc71;
  transform: scale(1.01);
}

.submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.cancel-btn {
  width: 100%;
  padding: 18px;
  border-radius: 16px;
  border: none;
  background: #ff4444;
  color: #ffffff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.cancel-btn:hover:not(:disabled) {
  background: #ff6666;
  transform: scale(1.01);
}

.cancel-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loader {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #ffffff;
  animation: spin 0.8s linear infinite;
}

.error-message {
  background: rgba(255, 68, 68, 0.1);
  border: 1px solid #ff4444;
  border-radius: 12px;
  padding: 12px 16px;
  margin-bottom: 20px;
  color: #ff4444;
  font-size: 14px;
  text-align: center;
}

.form-textarea--error {
  border-color: #ff4444 !important;
  background: rgba(255, 68, 68, 0.05) !important;
}

.validation-error {
  color: #ff4444;
  font-size: 12px;
  margin-top: 4px;
  padding-left: 4px;
}

/* ── Анимация успеха ───────────────────────────────── */
.success-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.85);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.success-animation {
  text-align: center;
  color: white;
}

.success-checkmark {
  width: 120px;
  height: 120px;
  margin: 0 auto 24px;
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

.success-text {
  font-size: 22px;
  font-weight: 600;
  opacity: 0;
  animation: fadeInText 0.7s ease forwards 1s;
}

/* Анимации */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes stroke {
  100% { stroke-dashoffset: 0; }
}

@keyframes fadeInText {
  to {
    opacity: 1;
    transform: translateY(0);
  }
  from {
    opacity: 0;
    transform: translateY(12px);
  }
}
</style>