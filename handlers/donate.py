from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, PaymentService, DonationService, i18n
from keyboards import support_keyboard, back_keyboard
from config import config

router = Router()

DONATION_AMOUNTS = {
    "donate_bread": 99,
    "donate_pie": 299,
    "donate_bbq": 599,
}


class DonateStates(StatesGroup):
    waiting_for_amount = State()


@router.callback_query(F.data == "menu_support")
async def support_menu(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("support_project_text", lang)
    await callback.message.edit_text(text, reply_markup=support_keyboard(lang), parse_mode="HTML")
    await callback.answer()


async def _start_donation(callback_or_message, user_id: int, amount: int, lang: str) -> None:
    return_url = f"https://t.me/{config.bot_username}"
    try:
        result = await PaymentService.create_yookassa_donation(float(amount), user_id, return_url)
        async with AsyncSessionLocal() as session:
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=float(amount),
                currency="RUB",
                payment_method="yookassa_donate",
                plan="donation",
                payment_ext_id=result["id"],
            )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить картой", url=result["url"])],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_support")],
        ])
        text = f"❤️ <b>Поддержка проекта — {amount} ₽</b>\n\nНажмите кнопку для перехода к оплате:"
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback_or_message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        err = "❌ Ошибка при создании платежа. Попробуйте позже."
        if isinstance(callback_or_message, CallbackQuery):
            await callback_or_message.message.edit_text(err, reply_markup=back_keyboard("menu_support", lang))
        else:
            await callback_or_message.answer(err, reply_markup=back_keyboard("menu_support", lang))


@router.callback_query(F.data.in_({"donate_bread", "donate_pie", "donate_bbq"}))
async def donate_fixed(callback: CallbackQuery) -> None:
    amount = DONATION_AMOUNTS[callback.data]
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    await _start_donation(callback, callback.from_user.id, amount, lang)
    await callback.answer()


@router.callback_query(F.data == "donate_custom")
async def donate_custom_start(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    await state.set_state(DonateStates.waiting_for_amount)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        "💎 Введите сумму в рублях (минимум 1 ₽):",
        reply_markup=back_keyboard("menu_support", lang),
    )
    await callback.answer()


@router.message(DonateStates.waiting_for_amount)
async def donate_custom_amount(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    text = message.text.strip() if message.text else ""
    if not text.isdigit() or int(text) < 1:
        await message.answer("❌ Введите корректное число, минимум 1 ₽.")
        return
    amount = int(text)
    await state.clear()
    await _start_donation(message, message.from_user.id, amount, lang)


@router.callback_query(F.data == "sponsors_list")
async def show_sponsors(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
        sponsors = await DonationService.get_top_sponsors(session, limit=20)

    if not sponsors:
        text = i18n.t("sponsors_empty", lang)
    else:
        lines = [i18n.t("sponsors_title", lang)]
        medals = ["🥇", "🥈", "🥉"]
        for idx, (name, total) in enumerate(sponsors):
            medal = medals[idx] if idx < 3 else f"{idx + 1}."
            lines.append(f"{medal} {name} — {total} ₽")
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_support", lang))
    await callback.answer()
