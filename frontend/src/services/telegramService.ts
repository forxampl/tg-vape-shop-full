class TelegramService {
  private tg: any = null;
  private _user: any = null;
  private _avatarUrl: string = '';
  private _initialized = false;
  private _isMock = false;
  private _initData: string = '';
  private _initDataUnsafe: any = {};

  constructor() {
    if (typeof window !== 'undefined') {
      this.initialize();
    }
  }

  private initialize() {
    console.log('🔍 Looking for Telegram WebApp...');

    const telegram = (window as any).Telegram?.WebApp;

    if (telegram) {
      console.log('✅ Telegram WebApp найден!');
      this.tg = telegram;

      // Обязательно вызываем ready и expand
      this.tg.ready();
      this.tg.expand();

      // Сохраняем initData и initDataUnsafe
      this._initData = this.tg.initData || '';
      this._initDataUnsafe = this.tg.initDataUnsafe || {};

      console.log('initData:', this._initData ? '✅ присутствует' : '❌ отсутствует');
      console.log('initDataUnsafe:', this._initDataUnsafe);

      this._user = this._initDataUnsafe.user || null;

      if (this._user) {
        console.log('👤 Пользователь:', this._user);

        // ────────────────────────────────────────────────────────────────
        // ПРИОРИТЕТ 1: используем официальное поле photo_url (самый надёжный способ 2025–2026)
        if (this._user.photo_url) {
          this._avatarUrl = this._user.photo_url;
          console.log('✅ Аватарка взята из photo_url:', this._avatarUrl);
        }
        // ПРИОРИТЕТ 2: fallback — старая конструкция URL (работает не всегда)
        else if (this._user.id) {
          // Пробуем .jpg — самый частый вариант
          this._avatarUrl = `https://t.me/i/userpic/320/${this._user.id}.jpg`;
          console.log('⚠️ photo_url отсутствует → fallback на constructed URL:', this._avatarUrl);
        }
        // ────────────────────────────────────────────────────────────────

        this._isMock = false;
      } else {
        console.warn('⚠️ Нет пользователя в initDataUnsafe.user');
      }

      this._initialized = true;
    } else {
      console.error('❌ Telegram WebApp НЕ найден! Проверь подключение скрипта');
      this._initialized = true;
    }
  }

  async waitForInit(timeoutMs = 5000): Promise<boolean> {
    if (this._initialized) return true;

    const startTime = Date.now();
    while (!this._initialized && Date.now() - startTime < timeoutMs) {
      await new Promise(resolve => setTimeout(resolve, 100));
      this.initialize(); // повторная попытка
    }

    if (!this._initialized) {
      console.warn(`⚠️ Инициализация Telegram не завершилась за ${timeoutMs} мс`);
    }

    return this._initialized;
  }

  // Геттеры
  get user() { return this._user; }
  get avatarUrl() { return this._avatarUrl; }
  get initialized() { return this._initialized; }
  get isMock() { return this._isMock; }
  get initData() { return this._initData; }
  get initDataUnsafe() { return this._initDataUnsafe; }
  get tgInstance() { return this.tg; }

  getAuthHeaders() {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this._user?.id) {
      headers['X-TG-ID'] = String(this._user.id);
    }

    const initData = this.tg?.initData || this._initData || '';

    if (initData) {
      console.log('Setting X-TG-Data, length:', initData.length);
      headers['X-TG-Data'] = initData;
      headers['authorization'] = `tma ${initData}`;
    } else {
      console.error('❌ initData is empty!');
    }

    return headers;
  }

  getInitData(): string {
    return this._initData;
  }

  getFullName(): string {
    if (!this._user) return 'Пользователь';
    const { first_name = '', last_name = '' } = this._user;
    return `${first_name} ${last_name}`.trim() || this._user.username || 'Пользователь';
  }

  getInitials(): string {
    if (!this._user?.first_name) return '?';
    const first = this._user.first_name.charAt(0) || '';
    const last = this._user.last_name?.charAt(0) || '';
    return (first + last).toUpperCase() || this._user.username?.charAt(0)?.toUpperCase() || '?';
  }
}

export const telegramService = new TelegramService();

// Для отладки в консоли
if (typeof window !== 'undefined') {
  (window as any).debugTelegram = () => {
    console.log('Telegram Service state:', {
      user: telegramService.user,
      avatarUrl: telegramService.avatarUrl || '(пусто)',
      isMock: telegramService.isMock,
      initialized: telegramService.initialized,
      initData: telegramService.initData ? '✅ присутствует' : '❌ отсутствует',
      initDataLength: telegramService.initData.length,
      photo_url: telegramService.user?.photo_url || 'отсутствует',
    });
  };

  // Тест broadcast (оставил как было)
  (window as any).testBroadcast = async () => {
    try {
      const initData = telegramService.getInitData();
      console.log('Testing broadcast with initData:', initData ? '✅' : '❌');

      const getResponse = await fetch('/api/broadcast', {
        headers: { 'X-TG-Data': initData }
      });
      console.log('GET /api/broadcast status:', getResponse.status);

      const postResponse = await fetch('/api/broadcast', {
        method: 'POST',
        headers: {
          'X-TG-Data': initData,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ enabled: true })
      });
      console.log('POST /api/broadcast status:', postResponse.status);
    } catch (error) {
      console.error('Test failed:', error);
    }
  };
}