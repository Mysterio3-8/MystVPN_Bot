"""
Обработчик входящих сообщений из группы поддержки.

Схема работы:
  Саппорт отвечает (Reply) на любое сообщение бота в группе
  → бот находит тикет по ID пересланного сообщения
  → пересылает ответ пользователю
  → сохраняет ответный msg_id тоже в routing (для дальнейшей переписки)
"""

import logging

from aiogram import Router, F, Bot
from aiogram.filters import Command, Filter
from aiogram.types import Message, CallbackQuery

from config import config
from database.db import (
    get_routing, add_message, close_ticket,
    list_open_tickets, register_routing,
)
from keyboards.keyboards import ticket_actions_kb

logger = logging.getLogger(__name__)
router = Router()


class _IsGroupChat(Filter):
    """Пропускает только сообщения из группы поддержки."""
    async def __call__(self, message: Message) -> bool:
        return message.chat.id == config.support_group_id


# ─── Ответ саппорта на сообщение в группе ────────────────────────────────────

@router.message(_IsGroupChat(), F.reply_to_message, F.text)
async def handle_support_reply(message: Message, bot: Bot) -> None:
    replied_id = message.reply_to_message.message_id
    routing = await get_routing(replied_id)

    if not routing:
        # Ответили на сообщение, которое не в нашей системе — игнорируем
        return

    ticket_id: int = routing["ticket_id"]
    user_id: int = routing["user_id"]

    await add_message(ticket_id, message.text, from_support=True)

    # Регистрируем ответ саппорта тоже, чтобы можно было отвечать в цепочке
    await register_routing(message.message_id, ticket_id, user_id)

    try:
        await bot.send_message(
            user_id,
            f"💬 <b>Ответ поддержки:</b>\n\n{message.text}",
        )
        # Отмечаем что сообщение доставлено
        await message.reply(f"✅ Доставлено пользователю (тикет #{ticket_id})")
    except Exception as e:
        await message.reply(f"❌ Не удалось отправить пользователю: {e}")


# ─── Кнопка «Закрыть тикет» в группе ────────────────────────────────────────

@router.callback_query(F.data.startswith("close:"))
async def close_ticket_cb(callback: CallbackQuery, bot: Bot) -> None:
    ticket_id = int(callback.data.split(":", 1)[1])

    # Ищем user_id через любое сообщение этого тикета
    routing = await get_routing(callback.message.message_id)
    user_id = routing["user_id"] if routing else None

    await close_ticket(ticket_id)

    # Обновляем сообщение в группе
    try:
        original_text = callback.message.text or callback.message.caption or ""
        await callback.message.edit_text(
            original_text + f"\n\n🔒 <b>Тикет #{ticket_id} закрыт</b>",
        )
    except Exception:
        pass

    # Уведомляем пользователя
    if user_id:
        try:
            await bot.send_message(
                user_id,
                f"✅ Тикет #{ticket_id} закрыт.\n\n"
                "Если вопрос остался или появился новый — нажми «💬 Написать в поддержку».",
            )
        except Exception:
            pass

    await callback.answer(f"Тикет #{ticket_id} закрыт")


# ─── /tickets — список открытых тикетов ──────────────────────────────────────

@router.message(_IsGroupChat(), Command("tickets"))
async def cmd_tickets(message: Message) -> None:
    tickets = await list_open_tickets()
    if not tickets:
        await message.reply("Открытых тикетов нет.")
        return

    lines = ["<b>Открытые тикеты:</b>\n"]
    for t in tickets:
        user_str = f"@{t['username']}" if t["username"] else f"ID {t['user_id']}"
        lines.append(f"• Тикет #{t['id']} — {user_str} ({t['created_at'][:16]})")

    await message.reply("\n".join(lines))


# ─── /close <id> — закрыть тикет командой ────────────────────────────────────

@router.message(_IsGroupChat(), Command("close"))
async def cmd_close(message: Message, bot: Bot) -> None:
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.reply("Использование: /close <номер_тикета>")
        return

    ticket_id = int(parts[1])
    await close_ticket(ticket_id)
    await message.reply(f"✅ Тикет #{ticket_id} закрыт.")
