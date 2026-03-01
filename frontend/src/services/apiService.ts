import { telegramService } from './telegramService'

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: string
}

class ApiService {
  private baseUrl: string
  private headers: HeadersInit

  // Кэш языка пользователя после получения из /api/me
  private userLanguage: string | null = null

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_BASE_URL || 'https://hatefully-resolved-heron.cloudpub.ru/'
    
    if (this.baseUrl.endsWith('/api')) {
      this.baseUrl = this.baseUrl.slice(0, -4)
    }
    if (this.baseUrl.endsWith('/')) {
      this.baseUrl = this.baseUrl.slice(0, -1)
    }
    
    this.headers = {
      'Content-Type': 'application/json',
    }
    
    console.log('ApiService baseUrl:', this.baseUrl)
  }

  getBaseUrl(): string {
    return this.baseUrl
  }

  // Загружает язык из /api/me один раз и кэширует
  private async loadUserLanguage(): Promise<string> {
    if (this.userLanguage !== null) {
      return this.userLanguage
    }

    try {
      console.log('→ Loading user language from /api/me...')
      const res = await this.request<{ language: string }>('/api/me')
      
      if (res.success && res.data?.language && typeof res.data.language === 'string') {
        this.userLanguage = res.data.language
        console.log('→ User language loaded and cached:', this.userLanguage)
        return this.userLanguage
      } else {
        console.warn('→ /api/me did not return valid language field')
      }
    } catch (err) {
      console.error('→ Failed to load user language:', err)
    }

    // Fallback
    this.userLanguage = 'ru'
    console.log('→ Using fallback language: ru')
    return this.userLanguage
  }

  private async getHeadersWithAuth(): Promise<HeadersInit> {
    await telegramService.waitForInit(8000)
    const authHeaders = telegramService.getAuthHeaders()
    return {
      ...this.headers,
      ...authHeaders
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    try {
      console.log('Making API request to endpoint:', endpoint);
      
      const authHeaders = await this.getHeadersWithAuth()
      console.log('Auth headers being sent:', JSON.stringify(authHeaders, null, 2));
      
      if (!authHeaders['X-TG-Data']) {
        console.error('❌ X-TG-Data отсутствует в заголовках!');
      } else {
        console.log('✅ X-TG-Data присутствует, длина:', authHeaders['X-TG-Data'].length);
        console.log('X-TG-Data первые 50 символов:', authHeaders['X-TG-Data'].substring(0, 50) + '...');
      }
      
      const finalHeaders = {
        ...authHeaders,
        ...(options.headers || {})
      }
      
      const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
      const url = `${this.baseUrl}${cleanEndpoint}`
      
      console.log('Full URL:', url);
      console.log('Final headers:', finalHeaders);
      
      const config: RequestInit = {
        ...options,
        headers: finalHeaders,
      }

      const response = await fetch(url, config)
      console.log('Response status:', response.status);
      
      const data = await response.json()
      console.log('Response data:', data);

      if (response.ok) {
        return { success: true, data }
      } else {
        return { success: false, error: data.detail || `HTTP Error: ${response.status}` }
      }
    } catch (error: any) {
      console.error('Request failed:', error);
      return { success: false, error: error.message || 'Network error' }
    }
  }

  // ────────────────────────────────────────────────
  // Методы с автоматическим lang из /api/me
  // ────────────────────────────────────────────────

  async getCities(lang?: string): Promise<ApiResponse> {
    const language = lang ?? (await this.loadUserLanguage())
    const query = language ? `?lang=${encodeURIComponent(language)}` : ''
    return this.request(`/api/cities${query}`)
  }

  async getProducts(
    cityId: number,
    params?: Record<string, any>,
    lang?: string
  ): Promise<ApiResponse> {
    const language = lang ?? (await this.loadUserLanguage())

    console.log('🔍 getProducts called with:', { cityId, params, lang: language })
    
    const searchParams = new URLSearchParams()
    searchParams.append('city_id', String(cityId))
    searchParams.append('lang', language)   // ← теперь всегда берётся из /api/me (если не переопределён)

    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value))
        }
      })
    }
    
    const endpoint = `/api/products?${searchParams.toString()}`
    console.log('📡 Final endpoint for products:', endpoint)
    
    return this.request(endpoint)
  }

  async getProductById(productId: number, lang?: string): Promise<ApiResponse> {
    const language = lang ?? (await this.loadUserLanguage())
    const query = language ? `?lang=${encodeURIComponent(language)}` : ''
    return this.request(`/api/products/${productId}${query}`)
  }

  // При смене языка — обновляем и кэш
  async updateLanguage(language: string): Promise<ApiResponse> {
    const res = await this.request('/api/me/language', {
      method: 'POST',
      body: JSON.stringify({ language })
    })

    if (res.success) {
      this.userLanguage = language
      console.log('→ Language cache updated after updateLanguage:', language)
    }

    return res
  }

  // Остальные методы без lang (оставлены без изменений)
  async createOrder(orderData: any): Promise<ApiResponse> {
    return this.request('/api/orders', {
      method: 'POST',
      body: JSON.stringify(orderData)
    })
  }

  async getUserOrders(): Promise<ApiResponse> {
    return this.request('/api/orders/my')
  }

  async getCurrentUser(): Promise<ApiResponse> {
    return this.request('/api/me')
  }
 
  async getBroadcastState(): Promise<ApiResponse<{ enabled: boolean }>> {
    return this.request('/api/broadcast')
  }

  async toggleBroadcast(enabled: boolean): Promise<ApiResponse<string>> {
    return this.request('/api/broadcast', {
      method: 'POST',
      body: JSON.stringify({ enabled })
    })
  }

  async updateNotifications(enabled: boolean): Promise<ApiResponse> {
    return this.toggleBroadcast(enabled)
  }

  async patchMe(data: any): Promise<ApiResponse> {
    return this.request('/api/me', {
      method: 'PATCH',
      body: JSON.stringify(data)
    })
  }

  async sendFeedback(text: string): Promise<ApiResponse<string>> {
    return this.request('/api/feedback', {
      method: 'POST',
      body: JSON.stringify({ text })
    })
  }
}

export const apiService = new ApiService()
export default ApiService