import logging
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, PaymentService, DonationService, i18n
from keyboards import support_keyboard, back_keyboard
from keyboards.inline import donate_method_keyboard
from config import config

router = Router()
logger = logging.getLogger(__name__)

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


@router.callback_query(F.data.in_({"donate_bread", "donate_pie", "donate_bbq"}))
async def donate_fixed(callback: CallbackQuery) -> None:
    amount = DONATION_AMOUNTS[callback.data]
    await callback.message.edit_text(
        f"❤️ <b>Поддержка проекта — {amount} ₽</b>\n\nВыберите способ оплаты:",
        reply_markup=donate_method_keyboard(amount),
        parse_mode="HTML",
    )
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
    await message.answer(
        f"❤️ <b>Поддержка проекта — {amount} ₽</b>\n\nВыберите способ оплаты:",
        reply_markup=donate_method_keyboard(amount),
        parse_mode="HTML",
    )


async def _process_donation(callback: CallbackQuery, user_id: int, amount: int, method: str) -> None:
    return_url = f"https://t.me/{config.bot_username}"
    try:
        if method == "sbp":
            result = await PaymentService.create_yookassa_sbp_donation(float(amount), user_id, return_url)
            pay_btn_text = "📱 Открыть СБП"
        else:
            result = await PaymentService.create_yookassa_donation(float(amount), user_id, return_url)
            pay_btn_text = "💳 Оплатить картой"

        async with AsyncSessionLocal() as session:
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=float(amount),
                currency="RUB",
                payment_method=f"yookassa_donate_{method}",
                plan="donation",
                payment_ext_id=result["id"],
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=pay_btn_text, url=result["url"])],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_support")],
        ])
        await callback.message.edit_text(
            f"❤️ <b>Поддержка проекта — {amount} ₽</b>\n\nНажмите кнопку для перехода к оплате:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Donation error user={user_id} amount={amount} method={method}: {e}", exc_info=True)
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа. Попробуйте позже.",
            reply_markup=back_keyboard("menu_support"),
        )


@router.callback_query(F.data.startswith("donate_pay_card_"))
async def donate_pay_card(callback: CallbackQuery) -> None:
    try:
        amount = int(callback.data.replace("donate_pay_card_", ""))
    except ValueError:
        await callback.answer("Неверная сумма", show_alert=True)
        return
    await _process_donation(callback, callback.from_user.id, amount, "card")
    await callback.answer()


@router.callback_query(F.data.startswith("donate_pay_sbp_"))
async def donate_pay_sbp(callback: CallbackQuery) -> None:
    try:
        amount = int(callback.data.replace("donate_pay_sbp_", ""))
    except ValueError:
        await callback.answer("Неверная сумма", show_alert=True)
        return
    await _process_donation(callback, callback.from_user.id, amount, "sbp")
    await callback.answer()


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
