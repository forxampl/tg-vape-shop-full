```markdown
# Telegram Bot + Admin Panel

## Запуск проекта

### Backend (API)

1. Перейдите в корень проекта
2. Создайте и активируйте виртуальное окружение

```bash
python -m venv venv
```

**Windows**
```bash
.\venv\Scripts\activate
```

**Linux / macOS**
```bash
source venv/bin/activate
```

3. Установите зависимости
```bash
pip install -r requirements.txt
```

4. Создайте файл `.env` из примера `config.example.env` и заполните значения:
   - токен бота
   - строку подключения к базе данных
   - другие необходимые ключи

5. Запустите сервер
```bash
uvicorn api.app:app --reload
```

API будет доступно по адресу:  
http://127.0.0.1:8000  
Документация: http://127.0.0.1:8000/docs

### Frontend (админ-панель)

1. Перейдите в папку фронтенда
```bash
cd frontend
```

2. Установите зависимости
```bash
npm install
```

3. Запустите разработческий сервер
```bash
npm run dev
```

Фронтенд будет доступен по адресу:  
http://localhost:5173

## Назначение суперадмина

Выполните в PostgreSQL:
```sql
UPDATE users
SET role = 'super_admin'
WHERE tg_id = 123456789;   -- ваш Telegram ID
```

## Установка PostgreSQL (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Дальше создайте пользователя и базу по вашим настройкам в `.env`.

Готово.
```