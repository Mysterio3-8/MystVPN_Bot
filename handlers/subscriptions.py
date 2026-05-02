from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PromoService, XrayService, i18n, schedule_abandoned_checkout
from config import config as bot_config
from keyboards import tariffs_keyboard, payment_method_keyboard, back_keyboard
from config import PLANS

router = Router()

PLAN_PERIOD_KEYS = {
    "1_month": "plan_period_1m",
    "3_months": "plan_period_3m",
    "6_months": "plan_period_6m",
    "1_year": "plan_period_1y",
}


class PromoStates(StatesGroup):
    waiting_for_code = State()


@router.message(Command("buy"))
async def cmd_buy(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, message.from_user.id)
        lang = user.language if user else "ru"
        trial_available = await SubscriptionService.is_trial_available(session, message.from_user.id)
    text = i18n.t("choose_plan", lang)
    await message.answer(text, reply_markup=tariffs_keyboard(lang, show_trial=trial_available))


@router.callback_query(F.data == "menu_buy")
async def buy_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
        trial_available = await SubscriptionService.is_trial_available(session, callback.from_user.id)
    text = i18n.t("choose_plan", lang)
    await callback.message.edit_text(text, reply_markup=tariffs_keyboard(lang, show_trial=trial_available))
    await callback.answer()


@router.callback_query(F.data.startswith("plan_"))
async def choose_plan(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("plan_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    is_admin = callback.from_user.id in bot_config.admin_ids

    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"

    # Проверяем активную скидку в Redis
    discount = await PromoService.get_discount(callback.from_user.id)
    period = i18n.t(PLAN_PERIOD_KEYS.get(plan_key, "plan_period_1m"), lang)

    if discount:
        pct = discount["percent"]
        original = plan["price"]
        discounted = round(original * (1 - pct / 100), 2)
        price_line = f"<s>{original:.0f} ₽</s> → <b>{discounted:.0f} ₽</b> 🏷 -{pct}%"
        text = f"📋 <b>{period}</b>\n\nЦена: {price_line}\n\n✅ Промокод <b>{discount['code']}</b> применён"
    else:
        text = i18n.t("plan_details", lang, period=period, price=f"{plan['price']:.0f}")

    await callback.message.edit_text(
        text,
        reply_markup=payment_method_keyboard(plan_key, lang, is_admin=is_admin),
        parse_mode="HTML",
    )
    await schedule_abandoned_checkout(callback.from_user.id, plan_key)
    await callback.answer()


@router.callback_query(F.data == "cabinet_renew")
async def renew_subscription(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("choose_plan", lang)
    await callback.message.edit_text(text, reply_markup=tariffs_keyboard(lang, show_trial=False))
    await callback.answer()


@router.callback_query(F.data == "enter_promo")
async def enter_promo(callback: CallbackQuery, state: FSMContext) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    await state.set_state(PromoStates.waiting_for_code)
    await state.update_data(lang=lang)
    await callback.message.edit_text(
        i18n.t("promo_ask", lang),
        reply_markup=back_keyboard("menu_buy", lang),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(PromoStates.waiting_for_code)
async def process_promo(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    lang = data.get("lang", "ru")
    code = (message.text or "").strip().upper()
    await state.clear()

    async with AsyncSessionLocal() as session:
        promo = await PromoService.validate(session, code)
        if not promo:
            await message.answer(
                i18n.t("promo_invalid", lang),
                reply_markup=back_keyboard("menu_buy", lang),
            )
            return

        if promo.free_plan:
            # Бесплатный тариф — активируем сразу
            sub = await SubscriptionService.create_pending(session, message.from_user.id, promo.free_plan)
            await SubscriptionService.activate(session, sub.id)
            await PromoService.increment_usage(session, promo.id)
            sub_id = sub.id

    if promo.free_plan:
        from services import fmt_key
        days = PLANS.get(promo.free_plan, {}).get("days", 30)
        vpn_key, sub_url = await XrayService.create_client(message.from_user.id, days)
        if vpn_key:
            async with AsyncSessionLocal() as s:
                await SubscriptionService.save_key(s, sub_id, vpn_key, sub_url)
            key_text = fmt_key(vpn_key, sub_url)
        else:
            key_text = "\n\n📋 Ключ будет доступен в /cabinet"
        await message.answer(
            f"🎉 <b>Промокод активирован!</b>\n\nВам выдан бесплатный тариф: <b>{promo.free_plan}</b>{key_text}",
            reply_markup=back_keyboard("menu_cabinet", lang),
            parse_mode="HTML",
        )
    else:
        # Скидка — сохраняем в Redis, НЕ инкрементируем использование
        await PromoService.save_discount(
            user_id=message.from_user.id,
            percent=promo.discount_percent,
            promo_id=promo.id,
            code=promo.code,
        )
        await message.answer(
            f"✅ <b>Промокод <code>{promo.code}</code> применён!</b>\n\n"
            f"Скидка <b>{promo.discount_percent}%</b> будет применена к следующей оплате.\n\n"
            "Выберите тариф:",
            reply_markup=tariffs_keyboard(lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "menu_donate")
async def donate_handler(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("donate_text", lang)
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("menu_buy", lang),
        parse_mode="HTML",
    )
    await callback.answer()
