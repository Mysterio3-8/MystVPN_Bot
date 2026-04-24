# Обход блокировки API Telegram через встроенный прокси

## Введение

В некоторых регионах, включая Россию, могут возникать проблемы с доступом к API Telegram из-за цензуры и блокировок. Для решения этой проблемы бот MystVPN имеет встроенную функцию использования прокси-сервера, которая позволяет обходить ограничения и обеспечивать стабильную работу бота.

## Как работает обход блокировок

### 1. Настройка прокси в конфигурации

В файле [.env](file:///c%3A/Users/Professional/Desktop/VPN_BOT/DOCS_RU.md#L170-L170) предусмотрены следующие параметры для настройки прокси:

```env
# ─── Прокси (для Telegram в ограниченных регионах) ────
PROXY_HOST=127.0.0.1
PROXY_PORT=12334
# PROXY_LOGIN=login    # Опционально
# PROXY_PASS=password  # Опционально
```

### 2. Реализация в коде

В файле [main_new.py](file:///c%3A/Users/Professional/Desktop/VPN_BOT/main_new.py) реализована функция `_create_bot()`, которая создает экземпляр бота с поддержкой прокси:

```python
def _create_bot(self) -> Bot:
    """Create bot instance with optional proxy"""
    # Use proxy if configured
    if settings.has_proxy:
        proxy_url = settings.proxy_url
        logger.info(f"🔒 Using proxy: {proxy_url}")
        try:
            from aiogram.client.session.aiohttp import AiohttpSession
            session = AiohttpSession(proxy=proxy_url)
            return Bot(
                token=settings.BOT_TOKEN,
                session=session,
                default=DefaultBotProperties(parse_mode="HTML")
            )
        except Exception as e:
            logger.warning(f"⚠️ Proxy setup failed: {e}")

    # No proxy or proxy failed
    logger.info("🔓 Creating bot without proxy")
    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
```

### 3. Обработка настроек прокси

В файле [config/settings.py](file:///c%3A/Users/Professional/Desktop/VPN_BOT/config/settings.py) определены параметры прокси и соответствующие методы:

```python
# === PROXY (for Telegram bot in restricted regions) ===
PROXY_HOST: Optional[str] = None
PROXY_PORT: Optional[int] = None
PROXY_LOGIN: Optional[str] = None
PROXY_PASS: Optional[str] = None

@property
def proxy_url(self) -> str:
    """Генерация URL прокси"""
    if not self.PROXY_HOST or not self.PROXY_PORT:
        return ""
    
    if self.PROXY_LOGIN and self.PROXY_PASS:
        return f"socks5://{self.PROXY_LOGIN}:{self.PROXY_PASS}@{self.PROXY_HOST}:{self.PROXY_PORT}"
    else:
        return f"socks5://{self.PROXY_HOST}:{self.PROXY_PORT}"

@property
def has_proxy(self) -> bool:
    """Есть ли прокси"""
    return bool(self.PROXY_HOST and self.PROXY_PORT)
```

## Настройка прокси

### 1. Подключение внешнего прокси

Для обхода блокировок вы можете использовать SOCKS5 прокси. В файле [.env](file:///c%3A/Users/Professional/Desktop/VPN_BOT/DOCS_RU.md#L170-L170) укажите данные вашего прокси-сервера:

```env
PROXY_HOST=ваш.адрес.прокси
PROXY_PORT=порт_прокси
PROXY_LOGIN=логин_при_необходимости
PROXY_PASS=пароль_при_необходимости
```

### 2. Использование локального прокси

Вы можете запустить локальный прокси-сервер, который будет перенаправлять трафик через прокси-сервер в неблокируемом регионе. Примеры бесплатных SOCKS5 прокси, рекомендованных в старом файле конфигурации:

- 185.219.84.151:1080 (Telegram DC1)
- 149.154.167.50:1080 (Telegram DC2)
- 91.108.4.0:1080 (Telegram DC3)

### 3. Проверка соединения

При запуске бота в файле [main_new.py](file:///c%3A/Users/Professional/Desktop/VPN_BOT/main_new.py) происходит тестирование соединения с API Telegram:

```python
async def _test_connection(self, timeout: int = 10) -> bool:
    try:
        await self.bot.get_me()
        return True
    except Exception as e:
        logger.error(f"❌ Connection to Telegram failed: {e}")
        return False
```

## Рекомендуемые способы настройки прокси

### 1. SSH туннель

Создание SSH туннеля с перенаправлением портов:

```bash
ssh -D 12334 пользователь@ваш_сервер
```

Это создаст SOCKS-прокси на localhost:12334, который можно использовать в настройках.

### 2. Danted или ss5

Настройка SOCKS-прокси-сервера на удаленном VPS:

```bash
# Установка danted
apt-get install dante-server

# Настройка в /etc/danted.conf
```

### 3. Shadowsocks

Использование Shadowsocks для создания шифрованного прокси:

```bash
# Установка shadowsocks
pip install shadowsocks

# Запуск клиента
sslocal -s server_ip -p port -l 1080 -k password -m chacha20-ietf-poly1305
```

## Резервные серверы Telegram API

В файле [config.py](file:///c%3A/Users/Professional/Desktop/VPN_BOT/config.py) также предусмотрен список резервных серверов Telegram API:

```python
TELEGRAM_API_SERVERS: list = [
    "185.219.84.151",  # MystVPN Germany proxy (ger30.linkey13.ru)
    "149.154.167.50",  # Server 1
    "149.154.167.51",  # Server 2
    "91.108.4.0",      # Server 3
    "91.108.8.0",      # Server 4
    "95.161.51.100",   # Server 5 (MTProxy)
]
```

## Проверка работы обхода блокировок

После настройки прокси запустите бота и проверьте логи:

```
2026-04-18 21:31:01 - 🚀 Initializing MystVPN Bot v3.0...
2026-04-18 21:31:02 - 🔒 Using proxy: socks5://proxy_host:proxy_port
2026-04-18 21:31:02 - ✅ Bot created
2026-04-18 21:31:03 - 🔍 Testing Telegram connection...
2026-04-18 21:31:04 - ✅ Connected to Telegram
```

Если все настроено правильно, вы увидите сообщение "✅ Connected to Telegram", что означает успешное подключение через прокси.

## Возможные проблемы и решения

### 1. Прокси не работает

- Проверьте правильность введенных данных
- Убедитесь, что порт открыт и доступен
- Проверьте сетевые настройки брандмауэра

### 2. Низкая скорость

- Попробуйте использовать другой прокси-сервер
- Проверьте нагрузку на текущий прокси-сервер

### 3. Ошибка при запуске

- Проверьте формат строки прокси (должна быть в формате socks5://)
- Убедитесь, что установлены необходимые зависимости для работы с прокси