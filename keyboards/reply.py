from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def admin_reply_keyboard() -> ReplyKeyboardMarkup:
    buttons = [
        [KeyboardButton(text="📊 Статистика"), KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="💰 Платежи"), KeyboardButton(text="📢 Рассылка")],
        [KeyboardButton(text="🔒 Заблокировать"), KeyboardButton(text="🔓 Разблокировать")],
        [KeyboardButton(text="◀️ Назад в меню")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=False)


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
