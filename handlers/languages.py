from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services import UserService, i18n
from keyboards import language_keyboard, main_menu_keyboard

router = Router()


@router.message(Command("language"))
async def cmd_language(message: Message) -> None:
    await message.answer("🗣️ Выберите язык / Choose language:", reply_markup=language_keyboard())


@router.callback_query(F.data == "menu_language")
async def language_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🗣️ Выберите язык / Choose language:",
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery) -> None:
    lang = callback.data.replace("lang_", "")
    async with AsyncSessionLocal() as session:
        await UserService.update_language(session, callback.from_user.id, lang)
        user = await UserService.get(session, callback.from_user.id)
        is_admin = user.is_admin if user else False

    text = i18n.t("language_changed", lang)
    welcome = i18n.t("welcome_message", lang)
    await callback.message.edit_text(
        f"{text}\n\n{welcome}",
        reply_markup=main_menu_keyboard(is_admin, lang),
    )
    await callback.answer(text)
