TELEGRAM_VPN_BOT_DOCUMENTATION.md
# 🔐 Документация: MystVPN Telegram Bot

## 🎯 Описание проекта

Полнофункциональный Telegram бот для продажи и управления VPN подписками. Поддержка множественных языков, личный кабинет пользователя, админ-панель и система платежей (YooKassa).

---

## 📋 Структура функциональности

### 1. **Главное меню** (`/start`, `/menu`)

**Inline кнопки:**
- 👤 Личный кабинет
- 💳 Купить подписку
- 💝 Поддержать проект
- ⭐ О нас
- ❓ Помощь
- 🗣️ Язык / Language
- 🔧 Admin Panel (только для администраторов)

**Команды (Slash commands):**
```
/start      - Главное меню
/menu       - Главное меню
/cabinet    - Личный кабинет
/buy        - Купить подписку
/about      - О нас
/help       - Помощь
/language   - Выбор языка
/admin      - Админ панель (private)
/test_xray  - Проверка подключения к XRay серверу
```

### 2. **Личный кабинет** (`/cabinet`)
Позволяет пользователям:
- 👁️ Просматривать активную подписку
- 🔄 Продлить подписку
- ❌ Отменить подписку
- 📖 Инструкции по подключению
- 📊 Историю платежей
- 🔑 Сбросить ключ VPN

### 3. **Покупка подписки** (`/buy`)

#### Доступные тарифы MystVPN:

| Период | Цена | Скидка | Цена в день |
|--------|------|--------|-------------|
| 1 месяц | 219 ₽ | - | 7.3 ₽ |
| 3 месяца | 549 ₽ | -16% | 6.1 ₽ |
| 6 месяцев | 999 ₽ | -24% | 5.5 ₽ |
| 1 год | 1799 ₽ | -32% | 4.9 ₽ |

#### Дополнительные возможности:
- 🎁 Подарочные подписки
- 🎟️ Промокоды (скидки и бесплатные тарифы)

### 4. **Методы оплаты:**
- 💳 YooKassa (карта, электронные кошельки) - основной метод оплаты

### 5. **Выбор языка** (`/language`)

Поддерживаемые языки:
- 🇷🇺 Русский (ru)
- 🇬🇧 English (en)
- 🇫🇷 Français (fr)
- 🇪🇸 Español (es)
- 🇵🇹 Português (pt)
- 🇹🇷 Türkçe (tr)
- 🇸🇦 العربية (ar)
- 🇮🇷 فارسی (fa)
- 🇺🇦 Українська (uk)
- 🇮🇩 Bahasa Indonesia (id)
- 🇨🇳 中文 (zh)
- 🇯🇵 日本語 (ja)
- 🇰🇷 한국어 (ko)
- 🇩🇪 Deutsch (de)
- 🇻🇳 Tiếng Việt (vi)
- 🇲🇾 Bahasa Melayu (ms)
- 🇮🇳 हिंदी (hi)

### 6. **О нас** (`/about`)

Информация о сервисе:
- Описание MystVPN
- Безопасность платежей
- Контактная информация

### 7. **Поддержка** (`/help`)

- Контакт на техническую поддержку: @Myst_support

### 8. **Админ панель** (`/admin`)

**Доступные функции (inline кнопки):**
- 📊 Статистика (пользователи, активные подписки, выручка)
- 👥 Управление пользователями (список)
- 💰 Статистика платежей
- 📢 Рассылка сообщений
- Выдача подписки пользователю
- 🎟️ Управление промокодами
- 🔌 Тест XRay/3x-ui подключения

**Требуется:**
- Добавить user_id администратора в .env файл (ADMIN_IDS)
- Проверка прав перед доступом

---

## 🛠️ Технический стек

### Backend:
- **Python 3.8+**
- **aiogram 3.13.0** - асинхронная библиотека для Telegram Bot API
- **PostgreSQL** - база данных
- **SQLAlchemy 2.0.36** - ORM для работы с БД
- **Redis** - кэширование и сессии
- **YooKassa** - обработка платежей
- **XRay/3x-ui** - VPN сервер
- **Aiohttp** - вебхуки и HTTP клиент

### Frontend:
- **Inline кнопки** (InlineKeyboardButton)
- **Reply кнопки** (ReplyKeyboardMarkup)
- **Callback запросы**

### Структура папок:
```
telegram_vpn_bot/
├── main.py                 # Точка входа (polling + webhook)
├── config.py              # Конфигурация
├── handlers/
│   ├── start.py          # Обработчик /start
│   ├── cabinet.py        # Управление личным кабинетом
│   ├── subscriptions.py  # Управление подписками
│   ├── payments.py       # Обработка платежей
│   ├── admin.py          # Админ панель
│   ├── languages.py      # Выбор языка
│   ├── gift.py           # Подарочные подписки
│   └── donate.py         # Пожертвования
├── models/
│   ├── user.py          # Модель пользователя
│   ├── subscription.py  # Модель подписки
│   └── payment.py       # Модель платежа
├── keyboards/
│   ├── inline.py        # Inline кнопки
│   └── reply.py         # Reply кнопки
├── services/
│   ├── payment_service.py        # Сервис платежей
│   ├── subscription_service.py   # Сервис подписок
│   ├── user_service.py           # Сервис пользователей
│   ├── xray_service.py           # Сервис XRay/VPN
│   ├── promo_service.py          # Сервис промокодов
│   ├── gift_service.py           # Сервис подарков
│   └── i18n.py                 # Интернационализация
├── database/
│   ├── db.py           # Инициализация БД
│   └── models/         # SQLAlchemy модели
└── locales/            # i18n файлы (JSON)
    ├── ru.json
    ├── en.json
    └── ...
```

---

## 🔑 Ключевые компоненты

### 1. Система пользователей

**Данные пользователя:**
```python
- id (int)                # Первичный ключ
- user_id (int)           # Telegram ID
- username (str)          # Username в Telegram
- first_name (str)        # Имя
- language (str)          # Выбранный язык (по умолчанию 'ru')
- is_premium (bool)       # Статус премиум
- is_banned (bool)        # Заблокирован ли
- is_admin (bool)         # Администратор ли
- created_at (datetime)   # Дата регистрации
```

### 2. Система подписок

**Данные подписки:**
```python
- id (int)                    # Первичный ключ
- user_id (int)               # Владелец подписки
- plan (str)                  # 1_month, 3_months, 6_months, 1_year
- price (float)               # Цена в рублях
- status (str)                # pending, active, expired, cancelled
- start_date (datetime)       # Дата начала
- end_date (datetime)         # Дата окончания
- auto_renewal (bool)         # Автопродление включено
- vpn_key (str)               # VPN ключ (vless/vmess/trojan)
- created_at (datetime)       # Дата создания
```

**Статусы подписки:**
- `pending` - ожидает оплаты
- `active` - активная подписка
- `expired` - истекла
- `cancelled` - отменена пользователем

### 3. Система платежей

**Данные платежа:**
```python
- id (int)                    # Первичный ключ
- user_id (int)               # Пользователь
- subscription_id (int)       # Связанная подписка (опционально)
- amount (float)              # Сумма
- currency (str)              # Валюта (RUB)
- payment_ext_id (str)        # Внешний ID платежа (YooKassa)
- status (str)                # pending, completed, failed, cancelled
- payment_method (str)        # yookassa, yookassa_gift, yookassa_donate
- plan (str)                  # Ключ тарифа
- created_at (datetime)       # Дата создания
- completed_at (datetime)     # Дата завершения
```

**Методы оплаты:**
- `yookassa` - YooKassa (карта, электронные кошельки)
- `yookassa_gift` - YooKassa для подарочных подписок
- `yookassa_donate` - YooKassa для пожертвований

**Статусы платежа:**
- `pending` - ожидает оплаты
- `completed` - успешно оплачено
- `failed` - ошибка при оплате
- `cancelled` - отменено пользователем

---

## 💳 Интеграция платежей (YooKassa)

### 1. **Создание платежа через YooKassa**

```python
async def pay_yookassa(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_yookassa_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    # Применяем скидку из Redis (если есть)
    discount = await PromoService.get_discount(user_id)
    if discount:
        pct = discount["percent"]
        price = round(plan["price"] * (1 - pct / 100), 2)
        discount_note = f" (скидка {pct}%)"
    else:
        price = plan["price"]
        discount_note = ""

    # Бесплатная активация при 100% скидке
    if price == 0:
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            await SubscriptionService.activate(session, sub.id)
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=0,
                currency="RUB",
                payment_method="promo_free",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=f"promo_{discount['promo_id']}_{user_id}",
            )
            await PromoService.increment_usage(session, discount["promo_id"])
        await PromoService.clear_discount(user_id)
        sub_id = sub.id
        vpn_key = await XrayService.create_client(user_id, plan["days"])
        if vpn_key:
            async with AsyncSessionLocal() as session:
                await SubscriptionService.save_key(session, sub_id, vpn_key)
            key_text = f"\n\n🔑 <b>Ваш VPN-ключ:</b>\n<code>{vpn_key}</code>"
        else:
            key_text = "\n\n📋 Ключ будет доступен в /cabinet"
        await callback.message.edit_text(
            f"🎉 <b>Подписка активирована бесплатно!</b>\n\nТариф: <b>{plan['period']}</b>{key_text}",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    try:
        result = await PaymentService.create_yookassa_payment(price, plan_key, user_id, return_url)
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=price,
                currency="RUB",
                payment_method="yookassa",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=result["id"],
            )

        # Применяем промокод: инкрементируем использование и очищаем Redis
        if discount:
            async with AsyncSessionLocal() as session:
                await PromoService.increment_usage(session, discount["promo_id"])
            await PromoService.clear_discount(user_id)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить картой", url=result["url"])],
            [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check_yookassa_{result['id']}_{sub.id}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_buy")],
        ])
        await callback.message.edit_text(
            f"💳 Оплата картой\n\nТариф: <b>{plan['period']}</b>\n"
            f"Сумма: <b>{price:.0f} ₽</b>{discount_note}\n\n"
            "Нажмите кнопку ниже для перехода к оплате, затем вернитесь и нажмите «Я оплатил»:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа. Попробуйте позже.",
            reply_markup=back_keyboard("menu_buy"),
        )

    await callback.answer()
```

### 2. **Обработка вебхука от YooKassa**

```python
async def handle_yookassa(request: web.Request) -> web.Response:
    try:
        body = await request.read()
        data = json.loads(body)
    except Exception:
        return web.Response(status=400)

    event_type = data.get("event", "")
    if event_type not in ("payment.succeeded", "payment.canceled"):
        return web.Response(status=200)

    payment_obj = data.get("object", {})
    ext_id = payment_obj.get("id")
    if not ext_id:
        return web.Response(status=400)

    if event_type == "payment.canceled":
        logger.info(f"Payment {ext_id} canceled by YooKassa")
        return web.Response(status=200)

    # Verify via API (prevents spoofed webhooks)
    try:
        status = await PaymentService.check_yookassa(ext_id)
    except Exception as e:
        logger.error(f"YooKassa API verify failed for {ext_id}: {e}")
        return web.Response(status=500)

    if status != "succeeded":
        logger.info(f"Payment {ext_id} status={status}, skipping")
        return web.Response(status=200)

    sub_id = None
    user_id = None
    plan_key = None

    async with AsyncSessionLocal() as session:
        payment = await PaymentService.get_by_ext_id(session, ext_id)
        if not payment:
            logger.warning(f"Payment {ext_id} not found in DB")
            return web.Response(status=200)
        if payment.status == "completed":
            logger.info(f"Payment {ext_id} already completed, skipping")
            return web.Response(status=200)

        await PaymentService.complete(session, payment.id)
        if payment.subscription_id:
            await SubscriptionService.activate(session, payment.subscription_id)

        sub_id = payment.subscription_id
        user_id = payment.user_id
        plan_key = payment.plan

    days = PLANS.get(plan_key or "", {}).get("days", 30)
    vpn_key = await XrayService.create_client(user_id, days)
    if vpn_key and sub_id:
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub_id, vpn_key)

    bot = request.app.get("bot")
    if bot and user_id:
        key_text = f"\n\n🔑 <b>Ваш VPN-ключ:</b>\n<code>{vpn_key}</code>" if vpn_key else "\n\n📋 Ключ будет в /cabinet"
        try:
            await bot.send_message(
                user_id,
                f"✅ <b>Оплата получена!</b>\n\nПодписка активирована автоматически.{key_text}",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Cannot notify user {user_id}: {e}")

    logger.info(f"Webhook: payment {ext_id} activated for user {user_id}")
    return web.Response(status=200)
```

---

## 🔐 Система безопасности

### Валидация:
- ✅ Проверка user_id перед обработкой
- ✅ Валидация callback_data
- ✅ Проверка статуса пользователя (не забанен)
- ✅ Проверка прав доступа для админ-панели
- ✅ Проверка подлинности платежей через YooKassa API

### Защита данных:
- ✅ Использование environment переменных для чувствительных данных
- ✅ HTTPS для всех запросов
- ✅ Использование SQLAlchemy ORM для защиты от SQL-инъекций
- ✅ Rate limiting через Redis

---

## 📊 База данных (PostgreSQL)

### Таблица пользователей:
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    is_premium BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_id ON users(user_id);
```

### Таблица подписок:
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    plan VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_date TIMESTAMP NOT NULL,
    auto_renewal BOOLEAN DEFAULT FALSE,
    vpn_key TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_user_subscription ON subscriptions(user_id);
CREATE INDEX idx_subscription_status ON subscriptions(status);
```

### Таблица платежей:
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    subscription_id INTEGER REFERENCES subscriptions(id) ON DELETE SET NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'RUB',
    payment_ext_id VARCHAR(255) UNIQUE,
    status VARCHAR(20) DEFAULT 'pending',
    payment_method VARCHAR(50),
    plan VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX idx_payment_user ON payments(user_id);
CREATE INDEX idx_payment_status ON payments(status);
CREATE INDEX idx_payment_ext_id ON payments(payment_ext_id);
```

---

## 🚀 Развертывание

### 1. Установка зависимостей:
```bash
pip install -r requirements.txt
```

### 2. Конфигурация (.env):
```bash
# Токен Telegram бота
BOT_TOKEN=your_token_here
BOT_USERNAME=MystVPN_bot

# База данных
DATABASE_URL=postgresql://user:password@localhost/mystvpn_bot

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Настройки YooKassa
YOOKASSA_ACCOUNT_ID=your_account_id
YOOKASSA_SECRET_KEY=your_secret_key

# XRay/3x-ui панель
XRAY_HOST=your_vpn_server_ip
XRAY_PORT=54321
XRAY_USERNAME=admin
XRAY_PASSWORD=your_password
XRAY_INBOUND_ID=1

# Администраторы (через запятую)
ADMIN_IDS=123456789,987654321

# Вебхук для платежей
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_SECRET=your_secret_key

# Прокси (опционально)
PROXY_HOST=proxy_ip
PROXY_PORT=1080
PROXY_LOGIN=username
PROXY_PASS=password
```

### 3. Запуск бота:

```python
async def main() -> None:
    setup_logging()
    logger.info("🚀 Initializing MystVPN Bot...")

    await init_db()
    logger.info("✅ База данных инициализирована")

    try:
        import redis.asyncio as aioredis
        test_redis = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        await asyncio.wait_for(test_redis.ping(), timeout=3)
        await test_redis.aclose()
        storage = RedisStorage.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        logger.info("✅ Redis подключён")
    except Exception:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.warning("⚠️ Redis недоступен — используется MemoryStorage")

    bot = create_bot()

    if not await test_connection(bot):
        logger.error("❌ Не удалось подключиться к Telegram. Проверьте прокси/токен.")
        await bot.session.close()
        return

    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(languages_router)
    dp.include_router(cabinet_router)
    dp.include_router(subscriptions_router)
    dp.include_router(gift_router)
    dp.include_router(donate_router)
    dp.include_router(payments_router)
    dp.include_router(admin_router)

    webhook_app = create_webhook_app(bot=bot)

    logger.info("🚀 Бот запускается (polling + webhook server)...")
    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            run_webhook_server(webhook_app, config.webhook_port),
        )
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("🛑 Остановка по сигналу пользователя")
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")
```

### Dockerfile:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

---

## 🔧 VPN XRay/3x-ui интеграция

### Создание VPN клиента:

```python
@classmethod
async def create_client(cls, user_id: int, days: int) -> str | None:
    from config import config
    if not (config.xray_address or config.xray_host) or not config.xray_password:
        logger.warning("XRay not configured — skipping key issuance")
        return None

    client_uuid = str(uuid.uuid4())
    # Email уникален за счёт части UUID — позволяет пользователю покупать повторно
    email = f"user_{user_id}_{client_uuid[:8]}"
    expiry_ms = int((datetime.utcnow().timestamp() + days * 86400) * 1000)

    async with aiohttp.ClientSession() as session:
        if not await cls._login(session):
            logger.error("XRay login failed during create_client")
            return None

        client_settings = {
            "id": int(config.xray_inbound_id),
            "settings": json.dumps({
                "clients": [{
                    "id": client_uuid,
                    "email": email,
                    "flow": "xtls-rprx-vision",
                    "limitIp": 0,
                    "totalGB": 0,
                    "expiryTime": expiry_ms,
                    "enable": True,
                    "tgId": str(user_id),
                    "subId": "",
                    "comment": f"MystVPN user {user_id}",
                    "reset": 0,
                }]
            }),
        }

        try:
            url = f"{cls._base_url()}/panel/api/inbounds/addClient"
            resp = await session.post(
                url,
                json=client_settings,
                timeout=aiohttp.ClientTimeout(total=10),
            )
            add_data = await resp.json(content_type=None)
            if not add_data.get("success"):
                logger.error(f"XRay addClient failed: {add_data.get('msg', add_data)}")
                return None
        except Exception as e:
            logger.error(f"XRay addClient error: {e}")
            return None

        inbound = await cls._get_inbound(session, config.xray_inbound_id)
        if not inbound:
            logger.error("XRay: inbound not found after addClient")
            return None

        return cls._build_key(inbound, client_uuid, user_id)
```

---

## 📈 Аналитика и статистика

Отслеживаемые метрики:
- 📊 Количество активных пользователей
- 💰 Общая выручка
- 🏦 Статистика платежей
- ✅ Количество активных подписок

---

## 🐛 Логирование и мониторинг

```python
def setup_logging() -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        RotatingFileHandler("bot.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"),
        logging.StreamHandler(),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)

logger = logging.getLogger(__name__)
```

---

## 📞 Поддержка и FAQ

### Основные вопросы:
1. **Как подключить VPN?** - Инструкции в разделе "Помощь"
2. **Как получить возврат?** - Связаться со службой поддержки

### Контакты поддержки:
- 💬 Telegram: @Myst_support

---

## 📚 Дополнительные ресурсы

- [Документация aiogram](https://docs.aiogram.dev/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [PostgreSQL документация](https://www.postgresql.org/docs/)
- [YooKassa документация](https://yookassa.ru/developers)
- [Redis документация](https://redis.io/documentation)
- [XRay Core документация](https://xtls.github.io/)

---

**Версия документации:** 2.0  
**Последнее обновление:** 2026-04-22  
**Автор:** MystVPN Development Team