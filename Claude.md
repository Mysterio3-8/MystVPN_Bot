# 🔐 CLAUDE.md — MystVPN Telegram Bot

## 🚀 Быстрые команды
- **Запуск бота:** `python main.py` (или `python main_new.py`)
- **Установка зависимостей:** `pip install -r requirements.txt`
- **Проверка связи с API:** `curl.exe https://api.telegram.org`
- **Очистка кэша Redis:** `redis-cli flushall`

## 🛠 Технический стек
- **Backend:** Python 3.8+ (aiogram 3.x)
- **База данных:** PostgreSQL (SQLAlchemy ORM)
- **Кэш/FSM:** Redis
- **Платежи:** Telegram Stars + YooKassa
- **Локализация:** i18n (JSON locales)

## 📁 Структура проекта
- `handlers/`: Логика команд (`start`, `buy`, `cabinet`, `admin`)
- `models/`: Схемы БД (User, Subscription, Payment)
- `services/`: Бизнес-логика (процессинг платежей, активация VPN)
- `keyboards/`: Сборка Inline и Reply меню
- `locales/`: Файлы переводов (RU, EN, DE и др.)
- `config/`: Настройки (`settings.py`, `.env`)

## 🌐 Обход блокировок (Proxy)
Проект поддерживает работу через SOCKS5 для доступа к API Telegram в ограниченных регионах.
- **Настройка:** В файле `.env` укажи `PROXY_HOST` и `PROXY_PORT`.
- **Логика:** Инициализация бота в `main_new.py` автоматически подтягивает `AiohttpSession` с прокси.
- **Резервные IP:** Список DC серверов Telegram находится в `config.py`.

## 📝 Гайдлайны по разработке
- **Стиль:** PEP 8 для Python. Используй асинхронность (`async/await`) везде.
- **Безопасность:** Никогда не хардкодь токены. Используй `settings.BOT_TOKEN`.
- **Админка:** Доступ к `/admin` разрешен только ID из списка `ADMIN_IDS`.
- **Платежи:** - `XTR` — валюта для Telegram Stars.
  - `RUB` — для YooKassa.
  - Обработка успешной оплаты происходит в `payments.py`.

## ⚠️ Важные заметки
- Перед запуском убедись, что запущены PostgreSQL и Redis.
- При изменении моделей БД создавай миграции через Alembic.
- Для корректной работы прокси в Windows может потребоваться отключение IPv6.