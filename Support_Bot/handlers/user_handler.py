import logging

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import config
from database.db import (
    get_open_ticket, create_ticket, close_ticket,
    add_message, register_routing,
)
from keyboards.keyboards import main_menu_kb, support_active_kb, faq_kb, ticket_actions_kb
from content.faq import get_faq_text
from services.ai_stub import get_ai_response

logger = logging.getLogger(__name__)
router = Router()


class SupportState(StatesGroup):
    chatting = State()


# ─── /start ─────────────────────────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    name = message.from_user.first_name or "друг"
    await message.answer(
        f"👋 Привет, {name}!\n\n"
        "Я бот поддержки <b>MystVPN</b>. Здесь ты можешь:\n"
        "• Получить ответы на частые вопросы (FAQ)\n"
        "• Написать нашей команде поддержки\n\n"
        "Выбери нужное:",
        reply_markup=main_menu_kb(),
    )


# ─── FAQ ────────────────────────────────────────────────────────────────────

@router.message(F.text == "❓ FAQ")
@router.message(Command("faq"))
async def show_faq(message: Message) -> None:
    await message.answer(
        "📚 <b>Часто задаваемые вопросы</b>\n\nВыбери тему:",
        reply_markup=faq_kb(),
    )


@router.callback_query(F.data.startswith("faq:"))
async def faq_item(callback: CallbackQuery) -> None:
    faq_id = callback.data.split(":", 1)[1]
    text = get_faq_text(faq_id)
    if text:
        await callback.message.answer(text)
    else:
        await callback.answer("Раздел не найден", show_alert=True)
        return
    await callback.answer()


# ─── Начать чат с поддержкой ─────────────────────────────────────────────────

@router.message(F.text == "💬 Написать в поддержку")
async def start_support_chat(message: Message, state: FSMContext) -> None:
    ticket = await get_open_ticket(message.from_user.id)
    if ticket:
        await message.answer(
            "У тебя уже открыт тикет. Пиши — я передам всё в поддержку.\n\n"
            "Нажми «🔙 Главное меню» чтобы выйти.",
            reply_markup=support_active_kb(),
        )
    else:
        await message.answer(
            "Опиши свою проблему или вопрос.\n"
            "Можешь приложить скриншот — всё получат специалисты.\n\n"
            "Нажми «🔙 Главное меню» чтобы выйти.",
            reply_markup=support_active_kb(),
        )
    await state.set_state(SupportState.chatting)


@router.message(F.text == "🔙 Главное меню")
async def back_to_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


# ─── Сообщение от пользователя → группа поддержки ───────────────────────────

@router.message(SupportState.chatting, F.text | F.photo | F.document | F.video)
async def relay_to_support(message: Message, state: FSMContext, bot: Bot) -> None:
    user = message.from_user
    text = message.text or message.caption or ""

    # Сначала пробуем ИИ-ответ (сейчас всегда None — заглушка)
    if text:
        ai_reply = await get_ai_response(text)
        if ai_reply:
            await message.answer(
                f"🤖 <b>Автоответ:</b>\n\n{ai_reply}\n\n"
                "Если это не решило вопрос, специалист ответит дополнительно.",
            )

    # Получаем или создаём тикет
    ticket = await get_open_ticket(user.id)
    if not ticket:
        ticket_id = await create_ticket(user.id, user.username)
        is_new = True
    else:
        ticket_id = ticket["id"]
        is_new = False

    await add_message(ticket_id, text, from_support=False)

    # Формируем шапку сообщения для группы саппорта
    user_mention = f"<b>{user.full_name}</b>"
    if user.username:
        user_mention += f" @{user.username}"
    user_mention += f" (ID: <code>{user.id}</code>)"

    if is_new:
        header = f"🎫 <b>Новый тикет #{ticket_id}</b>\n{user_mention}"
    else:
        header = f"↩️ <b>Тикет #{ticket_id}</b>\n{user_mention}"

    # Отправляем в группу поддержки
    try:
        kb = ticket_actions_kb(ticket_id) if is_new else None

        if message.photo:
            sent = await bot.send_photo(
                config.support_group_id,
                message.photo[-1].file_id,
                caption=f"{header}\n\n{text}" if text else header,
                reply_markup=kb,
            )
        elif message.document:
            sent = await bot.send_document(
                config.support_group_id,
                message.document.file_id,
                caption=f"{header}\n\n{text}" if text else header,
                reply_markup=kb,
            )
        elif message.video:
            sent = await bot.send_video(
                config.support_group_id,
                message.video.file_id,
                caption=f"{header}\n\n{text}" if text else header,
                reply_markup=kb,
            )
        else:
            sent = await bot.send_message(
                config.support_group_id,
                f"{header}\n\n💬 {text}",
                reply_markup=kb,
            )

        await register_routing(sent.message_id, ticket_id, user.id)

    except Exception as e:
        logger.error("Не удалось переслать в группу поддержки: %s", e)

    await message.answer(
        "✅ Сообщение отправлено в поддержку. Ответим в ближайшее время!\n"
        "Можешь продолжать писать — всё попадёт в тот же тикет."
    )
