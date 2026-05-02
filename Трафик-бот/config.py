# Конфигурационный файл для Telegram-бота Welcome-гейт

import os
from dotenv import load_dotenv
load_dotenv()

# Токен бота (можно задать через переменную окружения)
BOT_TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТОКЕН_БОТА")

# Имя канала спонсора (без @)
SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "example_channel")

# ID приватного канала (можно получить через @getmyid_bot)
# Формат: -1001234567890
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID", "-1001234567890"))

# Путь к файлу с приветственным фото
WELCOME_PHOTO_PATH = os.getenv("WELCOME_PHOTO_PATH", "welcome_photo.jpg")

# Текст приветственного сообщения
WELCOME_TEXT = os.getenv("WELCOME_TEXT", """
🔒 Хочешь получить доступ к быстрым VPN без лимитов?

Чтобы открыть секретный канал с ключами, тебе нужно выполнить два условия:
1️⃣ Подпишись на наш новостной канал.
2️⃣ Нажми «Проверить подписку» здесь, в боте.
""")

# Настройки базы данных
DATABASE_PATH = os.getenv("DATABASE_PATH", "bot_data.db")

# Время жизни инвайт-ссылки (в секундах)
INVITE_LINK_EXPIRE_TIME = int(os.getenv("INVITE_LINK_EXPIRE_TIME", "3600"))  # 1 час

# ID администраторов (через запятую)
ADMIN_IDS = os.getenv("ADMIN_IDS", "").split(",") if os.getenv("ADMIN_IDS") else []

# Максимальное количество ссылок на одного пользователя
MAX_LINKS_PER_USER = int(os.getenv("MAX_LINKS_PER_USER", "1"))

# Настройки логирования
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
