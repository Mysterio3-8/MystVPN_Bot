import asyncio
import logging
import os
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramForbiddenError, TelegramAPIError
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    PhotoSize,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3
from typing import Optional

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация (будет читаться из config.py или переменных окружения)
from config import (
    BOT_TOKEN,
    SPONSOR_CHANNEL,
    PRIVATE_CHANNEL_ID,
    WELCOME_PHOTO_PATH,
    WELCOME_TEXT,
)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_check TIMESTAMP
        )
    """)
    
    # Таблица инвайт-ссылок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            invite_link TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            is_used BOOLEAN DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    """)
    
    # Таблица статистики
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS statistics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE DEFAULT CURRENT_DATE,
            total_starts INTEGER DEFAULT 0,
            total_subscriptions INTEGER DEFAULT 0,
            UNIQUE(date)
        )
    """)
    
    conn.commit()
    conn.close()
    logger.info("База данных инициализирована")

# Вспомогательные функции для работы с БД
def get_user(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_or_update_user(user_id: int, username: str, first_name: str, last_name: str):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_name, joined_at)
        VALUES (?, ?, ?, ?, COALESCE((SELECT joined_at FROM users WHERE user_id = ?), CURRENT_TIMESTAMP))
    """, (user_id, username, first_name, last_name, user_id))
    conn.commit()
    conn.close()

def get_active_invite_link(user_id: int):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT invite_link FROM invite_links
        WHERE user_id = ? AND is_used = 0 AND expires_at > CURRENT_TIMESTAMP
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    link = cursor.fetchone()
    conn.close()
    return link[0] if link else None

def create_invite_link(user_id: int, invite_link: str, expires_at: datetime):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO invite_links (user_id, invite_link, expires_at)
        VALUES (?, ?, ?)
    """, (user_id, invite_link, expires_at))
    conn.commit()
    conn.close()

def update_statistics(total_starts: int = 0, total_subscriptions: int = 0):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute("""
        INSERT INTO statistics (date, total_starts, total_subscriptions)
        VALUES (?, ?, ?)
        ON CONFLICT(date) DO UPDATE SET
            total_starts = total_starts + ?,
            total_subscriptions = total_subscriptions + ?
    """, (today, total_starts, total_subscriptions, total_starts, total_subscriptions))
    conn.commit()
    conn.close()

def get_today_stats():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    today = datetime.now().date()
    cursor.execute("SELECT total_starts, total_subscriptions FROM statistics WHERE date = ?", (today,))
    stats = cursor.fetchone()
    conn.close()
    return stats if stats else (0, 0)

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Сохраняем/обновляем пользователя
    create_or_update_user(user_id, username, first_name, last_name)
    
    # Обновляем статистику
    update_statistics(total_starts=1)
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(
            text="📢 Подписаться на канал",
            url=f"https://t.me/{SPONSOR_CHANNEL}"
        )
    )
    keyboard.row(
        InlineKeyboardButton(
            text="✅ Проверить подписку",
            callback_data="check_sub"
        )
    )
    
    # Отправляем приветственное сообщение с фото
    try:
        if os.path.exists(WELCOME_PHOTO_PATH):
            with open(WELCOME_PHOTO_PATH, "rb") as photo:
                await message.answer_photo(
                    photo=photo,
                    caption=WELCOME_TEXT,
                    reply_markup=keyboard.as_markup(),
                    parse_mode=ParseMode.HTML
                )
        else:
            await message.answer(
                WELCOME_TEXT,
                reply_markup=keyboard.as_markup(),
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        logger.error(f"Ошибка при отправке сообщения: {e}")
        await message.answer(
            WELCOME_TEXT,
            reply_markup=keyboard.as_markup(),
            parse_mode=ParseMode.HTML
        )

# Проверка подписки на бота (не заблокирован ли)
async def check_bot_subscription(user_id: int) -> bool:
    """
    Проверяет, не заблокировал ли пользователь бота.
    Отправляет невидимое служебное сообщение и сразу удаляет его.
    Если отправка успешна - пользователь подписан на бота.
    Если ошибка 403 (Forbidden) - бот заблокирован.
    """
    try:
        test_msg = await bot.send_message(user_id, "🔍", disable_notification=True)
        await bot.delete_message(user_id, test_msg.message_id)
        return True
    except TelegramForbiddenError:
        logger.warning(f"Пользователь {user_id} заблокировал бота")
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки на бота для {user_id}: {e}")
        return False

# Обработчик проверки подписки
@dp.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery):
    user_id = callback.from_user.id
    
    try:
        # Проверка 1: подписка на канал спонсора
        chat_member = await bot.get_chat_member(
            chat_id=f"@{SPONSOR_CHANNEL}",
            user_id=user_id
        )
        
        status = chat_member.status
        logger.info(f"Статус подписки на канал пользователя {user_id}: {status}")
        
        if status not in ["member", "administrator", "creator"]:
            await callback.answer(
                "⛔️ Вы не подписаны на канал! Пожалуйста, подпишитесь и попробуйте снова.",
                show_alert=True
            )
            return
        
        # Проверка 2: подписка на бота (не заблокирован ли)
        if not await check_bot_subscription(user_id):
            await callback.answer(
                "⛔️ Вы заблокировали бота. Разблокируйте его, чтобы получить доступ.",
                show_alert=True
            )
            return
        
        # Обе проверки пройдены - выдаем ссылку
        active_link = get_active_invite_link(user_id)
        
        if active_link:
            # Отправляем существующую ссылку
            await callback.message.answer(
                "🎉 <b>Подписка на канал и бота подтверждена!</b>\n\n"
                f"Доступ открыт. Вот твоя личная ссылка в закрытый канал с VPN. Действует 1 час.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(
                        text="🔐 Войти в приватный канал",
                        url=active_link
                    )
                ).as_markup()
            )
        else:
            # Генерируем новую ссылку
            invite_link = await bot.create_chat_invite_link(
                chat_id=PRIVATE_CHANNEL_ID,
                member_limit=1,
                expire_date=datetime.now() + timedelta(hours=1)
            )
            
            # Сохраняем ссылку в БД
            create_invite_link(
                user_id=user_id,
                invite_link=invite_link.invite_link,
                expires_at=datetime.now() + timedelta(hours=1)
            )
            
            # Обновляем статистику
            update_statistics(total_subscriptions=1)
            
            # Отправляем новую ссылку
            await callback.message.answer(
                "🎉 <b>Подписка на канал и бота подтверждена!</b>\n\n"
                f"Доступ открыт. Вот твоя личная ссылка в закрытый канал с VPN. Действует 1 час.",
                parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardBuilder().row(
                    InlineKeyboardButton(
                        text="🔐 Войти в приватный канал",
                        url=invite_link.invite_link
                    )
                ).as_markup()
            )
    
    except TelegramAPIError as e:
        logger.error(f"Ошибка Telegram API при проверке подписки: {e}")
        await callback.answer(
            "⚠️ Ошибка проверки. Попробуйте позже.",
            show_alert=True
        )
    except Exception as e:
        logger.error(f"Ошибка при проверке подписки: {e}")
        await callback.answer(
            "❌ Произошла ошибка при проверке подписки. Попробуйте позже.",
            show_alert=True
        )
    
    await callback.answer()

# Команда для администратора - статистика
@dp.message(Command("stats"))
async def cmd_stats(message: Message):
    # В реальном проекте здесь должна быть проверка на администратора
    total_starts, total_subscriptions = get_today_stats()
    
    stats_text = f"📊 Статистика за сегодня:\n"
    stats_text += f"Всего запусков: {total_starts}\n"
    stats_text += f"Новых подписок: {total_subscriptions}\n"
    
    if total_starts > 0:
        conversion = (total_subscriptions / total_starts) * 100
        stats_text += f"Конверсия: {conversion:.1f}%"
    
    await message.answer(stats_text)

# Команда для администратора - обновление приветственного фото
@dp.message(Command("setphoto"))
async def cmd_setphoto(message: Message):
    # В реальном проекте здесь должна быть проверка на администратора
    if message.photo:
        photo: PhotoSize = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        with open(WELCOME_PHOTO_PATH, "wb") as new_photo:
            new_photo.write(downloaded_file.read())
        
        await message.answer("✅ Новое приветственное фото сохранено!")
    else:
        await message.answer("❌ Пожалуйста, отправьте фото с помощью команды /setphoto")

# Команда для администратора - обновление текста
@dp.message(Command("settext"))
async def cmd_settext(message: Message):
    # В реальном проекте здесь должна быть проверка на администратора
    new_text = message.text.replace("/settext ", "")
    if new_text:
        # В реальном проекте текст должен сохраняться в БД или файл конфигурации
        await message.answer("✅ Текст обновлен (в демо-режиме)")
    else:
        await message.answer("❌ Укажите новый текст: /settext <текст>")

# Главная функция
async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
