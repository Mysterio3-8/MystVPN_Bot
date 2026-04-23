from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import AsyncSessionLocal
from services import UserService, i18n
from keyboards import gift_tariffs_keyboard, gift_payment_method_keyboard
from config import PLANS

router = Router()

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
        text,
        reply_markup=gift_payment_method_keyboard(plan_key, lang),
        parse_mode="HTML",
    )
    await callback.answer()
