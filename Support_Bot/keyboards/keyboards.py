from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from content.faq import FAQ_ITEMS


def main_menu_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text="❓ FAQ")
    builder.button(text="💬 Написать в поддержку")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def support_active_kb() -> ReplyKeyboardMarkup:
    """Клавиатура когда пользователь в режиме общения с поддержкой."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔙 Главное меню")
    return builder.as_markup(resize_keyboard=True)


def faq_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in FAQ_ITEMS:
        builder.button(text=item["title"], callback_data=f"faq:{item['id']}")
    builder.adjust(1)
    return builder.as_markup()


def ticket_actions_kb(ticket_id: int) -> InlineKeyboardMarkup:
    """Кнопки для саппорта в группе поддержки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Закрыть тикет", callback_data=f"close:{ticket_id}")
    return builder.as_markup()
