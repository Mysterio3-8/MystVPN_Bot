import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
import sqlite3

from config import ADMIN_IDS, BOT_TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

def is_admin(user_id: int) -> bool:
    """Проверка, является ли пользователь администратором"""
    return str(user_id) in ADMIN_IDS

def get_db_connection():
    conn = sqlite3.connect("bot_data.db")
    conn.row_factory = sqlite3.Row
    return conn

# Команда админ-панели
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔️ У вас нет доступа к админ-панели.")
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 Обновить ссылку", callback_data="admin_refresh_link")
    )
    keyboard.row(
        InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export")
    )
    
    await message.answer(
        "🔐 Админ-панель Welcome-гейт",
        reply_markup=keyboard.as_markup()
    )

# Обработчик кнопок админ-панели
@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔️ У вас нет доступа.", show_alert=True)
        return
    
    action = callback.data.replace("admin_", "")
    
    if action == "stats":
        await show_statistics(callback)
    elif action == "refresh_link":
        await refresh_all_links(callback)
    elif action == "export":
        await export_data(callback)
    
    await callback.answer()

async def show_statistics(callback: CallbackQuery):
    """Показать статистику"""
    conn = get_db_connection()
    
    # Общее количество пользователей
    total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    
    # Общее количество сгенерированных ссылок
    total_links = conn.execute("SELECT COUNT(*) FROM invite_links").fetchone()[0]
    
    # Активные ссылки
    active_links = conn.execute(
        "SELECT COUNT(*) FROM invite_links WHERE is_used = 0 AND expires_at > CURRENT_TIMESTAMP"
    ).fetchone()[0]
    
    # Статистика за сегодня
    today = datetime.now().date()
    today_stats = conn.execute(
        "SELECT total_starts, total_subscriptions FROM statistics WHERE date = ?",
        (today,)
    ).fetchone()
    
    conn.close()
    
    stats_text = "📊 Статистика бота:\n\n"
    stats_text += f"👥 Всего пользователей: {total_users}\n"
    stats_text += f"🔗 Всего ссылок: {total_links}\n"
    stats_text += f"✅ Активных ссылок: {active_links}\n\n"
    
    if today_stats:
        stats_text += f"📅 За сегодня:\n"
        stats_text += f"Запусков: {today_stats[0]}\n"
        stats_text += f"Подписок: {today_stats[1]}\n"
        if today_stats[0] > 0:
            conversion = (today_stats[1] / today_stats[0]) * 100
            stats_text += f"Конверсия: {conversion:.1f}%"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")
    )
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.HTML
    )

async def refresh_all_links(callback: CallbackQuery):
    """Отозвать все активные ссылки"""
    conn = get_db_connection()
    
    # Помечаем все активные ссылки как использованные
    conn.execute(
        "UPDATE invite_links SET is_used = 1 WHERE is_used = 0 AND expires_at > CURRENT_TIMESTAMP"
    )
    conn.commit()
    conn.close()
    
    await callback.message.answer(
        "✅ Все активные ссылки были отозваны. Пользователям нужно будет получить новые ссылки."
    )
    
    # Возвращаем в меню
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
    )
    keyboard.row(
        InlineKeyboardButton(text="🔄 Обновить ссылку", callback_data="admin_refresh_link")
    )
    keyboard.row(
        InlineKeyboardButton(text="📤 Экспорт данных", callback_data="admin_export")
    )
    
    await callback.message.answer(
        "🔐 Админ-панель",
        reply_markup=keyboard.as_markup()
    )

async def export_data(callback: CallbackQuery):
    """Экспорт данных"""
    conn = get_db_connection()
    
    # Экспорт пользователей
    users = conn.execute("SELECT * FROM users ORDER BY joined_at DESC").fetchall()
    
    # Экспорт ссылок
    links = conn.execute(
        "SELECT * FROM invite_links ORDER BY created_at DESC"
    ).fetchall()
    
    conn.close()
    
    # Формируем текст экспорта
    export_text = "📤 Экспорт данных\n\n"
    export_text += "=== ПОЛЬЗОВАТЕЛИ ===\n"
    for user in users[:50]:  # Ограничиваем 50 последними
        export_text += f"ID: {user['user_id']}, Username: {user['username']}, "
        export_text += f"Имя: {user['first_name']}, Дата: {user['joined_at']}\n"
    
    export_text += "\n=== ИНВАЙТ-ССЫЛКИ ===\n"
    for link in links[:50]:  # Ограничиваем 50 последними
        export_text += f"User: {link['user_id']}, Link: {link['invite_link']}, "
        export_text += f"Created: {link['created_at']}, Expires: {link['expires_at']}, "
        export_text += f"Used: {link['is_used']}\n"
    
    # Отправляем файлом, если текст слишком длинный
    if len(export_text) > 4000:
        with open("export_data.txt", "w", encoding="utf-8") as f:
            f.write(export_text)
        
        with open("export_data.txt", "rb") as f:
            await callback.message.answer_document(
                document=f,
                caption="📤 Данные экспортированы"
            )
    else:
        await callback.message.answer(
            f"```\n{export_text}\n```",
            parse_mode=ParseMode.MARKDOWN
        )

# Главная функция для админ-панели
async def admin_main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(admin_main())
