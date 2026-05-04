import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, GiftService, XrayService, i18n
from keyboards import gift_tariffs_keyboard, gift_payment_method_keyboard, back_keyboard
from config import PLANS, config

router = Router()
_log = logging.getLogger(__name__)

PLAN_PERIOD_KEYS = {
    "1_month": "plan_period_1m",
    "3_months": "plan_period_3m",
    "6_months": "plan_period_6m",
    "1_year": "plan_period_1y",
}


@router.callback_query(F.data == "menu_gift")
async def gift_menu(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("gift_choose_plan", lang)
    await callback.message.edit_text(text, reply_markup=gift_tariffs_keyboard(lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data.startswith("gift_plan_"))
async def choose_gift_plan(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("gift_plan_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"

    period = i18n.t(PLAN_PERIOD_KEYS.get(plan_key, "plan_period_1m"), lang)
    text = i18n.t("plan_details", lang, period=period, price=f"{plan['price']:.0f}")
    await callback.message.edit_text(
        text, reply_markup=gift_payment_method_keyboard(plan_key, lang), parse_mode="HTML",
    )
    await callback.answer()


# ──────────────────────────────────────────────────
# Оплата подарка
# ──────────────────────────────────────────────────

async def _create_gift_payment(callback: CallbackQuery, plan_key: str, method: str) -> None:
    """method: 'card' | 'sbp'"""
    plan = PLANS.get(plan_key)
    if not plan:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.answer(i18n.t("err_invalid_plan", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    async with AsyncSessionLocal() as session:
        _u = await UserService.get(session, user_id)
        lang = _u.language if _u else "ru"

    is_card = method == "card"
    create_payment = PaymentService.create_yookassa_payment if is_card else PaymentService.create_yookassa_sbp
    pay_btn_key = "btn_pay_card" if is_card else "btn_pay_sbp"
    after_key = "gift_payment_after_card" if is_card else "gift_payment_after_sbp"

    try:
        result = await create_payment(plan["price"], plan_key, user_id, return_url)
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            gift = await GiftService.create(session, plan_key, user_id)
            from sqlalchemy import select as _sel
            from models import GiftCode as _GiftCode
            g = await session.execute(_sel(_GiftCode).where(_GiftCode.code == gift.code))
            g = g.scalar_one_or_none()
            if g:
                g.payment_ext_id = result["id"]
                await session.commit()
            await PaymentService.create(
                session, user_id=user_id, amount=plan["price"], currency="RUB",
                payment_method="yookassa_gift", plan=plan_key,
                subscription_id=sub.id, payment_ext_id=result["id"],
            )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=i18n.t(pay_btn_key, lang), url=result["url"])],
            [InlineKeyboardButton(text=i18n.t("btn_paid", lang), callback_data=f"check_gift_{result['id']}")],
            [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_gift")],
        ])
        await callback.message.edit_text(
            i18n.t("gift_payment_title", lang, period=plan["period"]) + "\n\n"
            + i18n.t("gift_payment_sum", lang, price=plan["price"]) + "\n\n"
            + i18n.t(after_key, lang),
            reply_markup=keyboard, parse_mode="HTML",
        )
    except Exception as _e:
        _log.error(f"Gift {method} error user={user_id} plan={plan_key}: {_e}", exc_info=True)
        await callback.message.edit_text(
            i18n.t("err_payment_create", lang), reply_markup=back_keyboard("menu_gift"),
        )


@router.callback_query(F.data.startswith("pay_gift_yookassa_"))
async def pay_gift_yookassa(callback: CallbackQuery) -> None:
    await _create_gift_payment(callback, callback.data.replace("pay_gift_yookassa_", ""), "card")
    await callback.answer()


@router.callback_query(F.data.startswith("pay_gift_sbp_"))
async def pay_gift_sbp(callback: CallbackQuery) -> None:
    await _create_gift_payment(callback, callback.data.replace("pay_gift_sbp_", ""), "sbp")
    await callback.answer()


@router.callback_query(F.data.startswith("check_gift_"))
async def check_gift_payment(callback: CallbackQuery) -> None:
    ext_id = callback.data.replace("check_gift_", "")
    try:
        status = await PaymentService.check_yookassa(ext_id)
    except Exception:
        await callback.answer("❌ Ошибка проверки платежа", show_alert=True)
        return

    if status == "succeeded":
        async with AsyncSessionLocal() as session:
            payment = await PaymentService.get_by_ext_id(session, ext_id)
            if payment and payment.status != "completed":
                await PaymentService.complete(session, payment.id)
            gift = await GiftService.get_by_payment_ext_id(session, ext_id)
            if gift and not gift.is_paid:
                gift.is_paid = True
                await session.commit()
        if gift:
            gift_link = f"https://t.me/{config.bot_username}?start=gift_{gift.code}"
            await callback.message.edit_text(
                f"✅ <b>Оплата получена!</b>\n\n"
                f"🎁 Вот ссылка-подарок — отправь другу:\n\n"
                f"<code>{gift_link}</code>\n\n"
                f"Друг перейдёт по ссылке и получит VPN автоматически.",
                parse_mode="HTML",
            )
        await callback.answer()
    elif status == "pending":
        await callback.answer("⏳ Платёж ещё не завершён", show_alert=True)
    else:
        await callback.answer(f"❌ Статус: {status}", show_alert=True)
