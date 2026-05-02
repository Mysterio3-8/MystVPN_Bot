from aiogram import Router, F, Bot
from aiogram.filters import Filter
from aiogram.types import (
    CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, Message,
)
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, GiftService, XrayService, PromoService, fmt_key, i18n
from keyboards import back_keyboard
from config import PLANS, config

router = Router()


# ──────────────────────────────────────────────────
# Фильтр — только для администраторов
# ──────────────────────────────────────────────────

class IsAdmin(Filter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return callback.from_user.id in config.admin_ids


# ──────────────────────────────────────────────────
# Бесплатная активация для администратора
# ──────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("pay_admin_free_"))
async def pay_admin_free(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_admin_free_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        await callback.answer("Неверный тариф", show_alert=True)
        return

    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.create_pending(session, user_id, plan_key)
        await SubscriptionService.activate(session, sub.id)
        await PaymentService.create(
            session,
            user_id=user_id,
            amount=0,
            currency="RUB",
            payment_method="admin_free",
            plan=plan_key,
            subscription_id=sub.id,
            payment_ext_id=f"admin_free_{user_id}_{sub.id}",
        )

    sub_id = sub.id
    vpn_key, sub_url = await XrayService.create_client(user_id, plan["days"])
    if vpn_key:
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub_id, vpn_key, sub_url)

    await callback.message.edit_text(
        f"👑 <b>Подписка активирована (Админ)</b>\n"
        f"Тариф: <b>{plan['period']}</b>"
        f"{fmt_key(vpn_key, sub_url)}",
        parse_mode="HTML",
    )
    await callback.answer("✅ Активировано бесплатно", show_alert=True)


# ──────────────────────────────────────────────────
# YooKassa — создание платежа
# ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_yookassa_"))
async def pay_yookassa(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_yookassa_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.answer(i18n.t("err_invalid_plan", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    discount = await PromoService.get_discount(user_id)
    if discount:
        pct = discount["percent"]
        price = round(plan["price"] * (1 - pct / 100), 2)
        discount_note = f" (скидка {pct}%)"
    else:
        price = plan["price"]
        discount_note = ""

    if price == 0:
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            await SubscriptionService.activate(session, sub.id)
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=0,
                currency="RUB",
                payment_method="promo_free",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=f"promo_{discount['promo_id']}_{user_id}",
            )
            await PromoService.increment_usage(session, discount["promo_id"])
        await PromoService.clear_discount(user_id)
        sub_id = sub.id
        vpn_key, sub_url = await XrayService.create_client(user_id, plan["days"])
        if vpn_key:
            async with AsyncSessionLocal() as session:
                await SubscriptionService.save_key(session, sub_id, vpn_key, sub_url)
        await callback.message.edit_text(
            f"✅ <b>Подписка активирована!</b>\n"
            f"Тариф: <b>{plan['period']}</b>"
            f"{fmt_key(vpn_key, sub_url)}",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    try:
        result = await PaymentService.create_yookassa_payment(price, plan_key, user_id, return_url)
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=price,
                currency="RUB",
                payment_method="yookassa",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=result["id"],
            )

        if discount:
            async with AsyncSessionLocal() as session:
                await PromoService.increment_usage(session, discount["promo_id"])
            await PromoService.clear_discount(user_id)

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=i18n.t("btn_pay_card", lang), url=result["url"])],
            [InlineKeyboardButton(text=i18n.t("btn_paid", lang), callback_data=f"check_yookassa_{result['id']}_{sub.id}")],
            [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_buy")],
        ])
        await callback.message.edit_text(
            f"💳 Оплата картой\n\nТариф: <b>{plan['period']}</b>\n"
            f"Сумма: <b>{price:.0f} ₽</b>{discount_note}\n\n"
            "Нажмите кнопку ниже для перехода к оплате, затем вернитесь и нажмите «Я оплатил»:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.message.edit_text(
            i18n.t("err_payment_create", lang),
            reply_markup=back_keyboard("menu_buy"),
        )

    await callback.answer()


# ──────────────────────────────────────────────────
# YooKassa — проверка по кнопке (идемпотентная)
# ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("check_yookassa_"))
async def check_yookassa_payment(callback: CallbackQuery) -> None:
    parts = callback.data.replace("check_yookassa_", "").rsplit("_", 1)
    if len(parts) != 2:
        await callback.answer("Неверные данные", show_alert=True)
        return
    ext_id, sub_id_str = parts[0], parts[1]
    try:
        sub_id = int(sub_id_str)
    except ValueError:
        await callback.answer("Неверные данные", show_alert=True)
        return

    async with AsyncSessionLocal() as session:
        payment = await PaymentService.get_by_ext_id(session, ext_id)
        if payment and payment.status == "completed":
            sub = await SubscriptionService.get_active(session, callback.from_user.id)
            from services import fmt_key
            key_text = fmt_key(sub.vpn_key if sub else None, sub.sub_url if sub else None) if sub else ""
            await callback.message.edit_text(
                f"✅ <b>Подписка уже активирована!</b>{key_text}\n\n📋 Детали: /cabinet",
                parse_mode="HTML",
            )
            await callback.answer()
            return

    try:
        status = await PaymentService.check_yookassa(ext_id)
    except Exception:
        await callback.answer("❌ Ошибка проверки платежа", show_alert=True)
        return

    if status == "succeeded":
        plan_key = None
        async with AsyncSessionLocal() as session:
            payment = await PaymentService.get_by_ext_id(session, ext_id)
            if payment:
                if payment.status == "completed":
                    await callback.answer("✅ Уже активировано", show_alert=True)
                    return
                plan_key = payment.plan
                await PaymentService.complete(session, payment.id)
            await SubscriptionService.activate(session, sub_id)

        days = PLANS.get(plan_key or "", {}).get("days", 30)
        user_id = callback.from_user.id
        vpn_key, sub_url = await XrayService.create_client(user_id, days)
        if vpn_key:
            async with AsyncSessionLocal() as session:
                await SubscriptionService.save_key(session, sub_id, vpn_key, sub_url)

        await callback.message.edit_text(
            f"✅ <b>Оплата прошла!</b>\n"
            f"Подписка активирована."
            f"{fmt_key(vpn_key, sub_url)}",
            parse_mode="HTML",
        )
    elif status == "pending":
        await callback.answer("⏳ Платёж ещё не завершён", show_alert=True)
    else:
        await callback.answer(f"❌ Статус платежа: {status}", show_alert=True)

    await callback.answer()


# ──────────────────────────────────────────────────
# СБП — создание платежа
# ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_sbp_"))
async def pay_sbp(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_sbp_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.answer(i18n.t("err_invalid_plan", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    discount = await PromoService.get_discount(user_id)
    if discount:
        pct = discount["percent"]
        price = round(plan["price"] * (1 - pct / 100), 2)
        discount_note = f" (скидка {pct}%)"
    else:
        price = plan["price"]
        discount_note = ""

    if price == 0:
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            await SubscriptionService.activate(session, sub.id)
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=0,
                currency="RUB",
                payment_method="promo_free",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=f"promo_{discount['promo_id']}_{user_id}",
            )
            await PromoService.increment_usage(session, discount["promo_id"])
        await PromoService.clear_discount(user_id)
        sub_id = sub.id
        vpn_key, sub_url = await XrayService.create_client(user_id, plan["days"])
        if vpn_key:
            async with AsyncSessionLocal() as session:
                await SubscriptionService.save_key(session, sub_id, vpn_key, sub_url)
        await callback.message.edit_text(
            f"✅ <b>Подписка активирована!</b>\n"
            f"Тариф: <b>{plan['period']}</b>"
            f"{fmt_key(vpn_key, sub_url)}",
            parse_mode="HTML",
        )
        await callback.answer()
        return

    import logging as _log
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
    try:
        result = await PaymentService.create_yookassa_sbp(price, plan_key, user_id, return_url)
    except Exception as sbp_err:
        _log.getLogger(__name__).error(f"SBP create error user={user_id} plan={plan_key}: {sbp_err}", exc_info=True)
        await callback.message.edit_text(
            i18n.t("err_sbp_create", lang),
            reply_markup=back_keyboard("menu_buy"),
        )
        await callback.answer()
        return

    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.create_pending(session, user_id, plan_key)
        await PaymentService.create(
            session,
            user_id=user_id,
            amount=price,
            currency="RUB",
            payment_method="sbp",
            plan=plan_key,
            subscription_id=sub.id,
            payment_ext_id=result["id"],
        )

    if discount:
        async with AsyncSessionLocal() as session:
            await PromoService.increment_usage(session, discount["promo_id"])
        await PromoService.clear_discount(user_id)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t("btn_pay_sbp", lang), url=result["url"])],
        [InlineKeyboardButton(text=i18n.t("btn_paid", lang), callback_data=f"check_yookassa_{result['id']}_{sub.id}")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_buy")],
    ])
    await callback.message.edit_text(
        f"📱 <b>Оплата через СБП</b>\n\n"
        f"Тариф: <b>{plan['period']}</b>\n"
        f"Сумма: <b>{price:.0f} ₽</b>{discount_note}\n\n"
        f"Нажмите кнопку ниже — откроется приложение вашего банка.\n"
        f"После оплаты нажмите «Я оплатил»:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await callback.answer()


# ──────────────────────────────────────────────────
# Подарки через YooKassa
# ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_gift_yookassa_"))
async def pay_gift_yookassa(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_gift_yookassa_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.answer(i18n.t("err_invalid_plan", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    try:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, user_id)
            lang = user.language if user else "ru"
        result = await PaymentService.create_yookassa_payment(plan["price"], plan_key, user_id, return_url)
        async with AsyncSessionLocal() as session:
            sub = await SubscriptionService.create_pending(session, user_id, plan_key)
            gift = await GiftService.create(session, plan_key, user_id)
            from sqlalchemy import select as _select
            from models import GiftCode as _GiftCode
            g = await session.execute(_select(_GiftCode).where(_GiftCode.code == gift.code))
            g = g.scalar_one_or_none()
            if g:
                g.payment_ext_id = result["id"]
                await session.commit()
            await PaymentService.create(
                session,
                user_id=user_id,
                amount=plan["price"],
                currency="RUB",
                payment_method="yookassa_gift",
                plan=plan_key,
                subscription_id=sub.id,
                payment_ext_id=result["id"],
            )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=i18n.t("btn_pay_card", lang), url=result["url"])],
            [InlineKeyboardButton(text=i18n.t("btn_paid", lang), callback_data=f"check_gift_{result['id']}")],
            [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_gift")],
        ])
        await callback.message.edit_text(
            i18n.t("gift_payment_title", lang, period=plan['period']) + "\n\n"
            + i18n.t("gift_payment_sum", lang, price=plan['price']) + "\n\n"
            + i18n.t("gift_payment_after_card", lang),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, user_id)
            lang = user.language if user else "ru"
        await callback.message.edit_text(
            i18n.t("err_payment_create", lang),
            reply_markup=back_keyboard("menu_gift"),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("pay_gift_sbp_"))
async def pay_gift_sbp(callback: CallbackQuery) -> None:
    plan_key = callback.data.replace("pay_gift_sbp_", "")
    plan = PLANS.get(plan_key)
    if not plan:
        async with AsyncSessionLocal() as session:
            user = await UserService.get(session, callback.from_user.id)
            lang = user.language if user else "ru"
        await callback.answer(i18n.t("err_invalid_plan", lang), show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = f"https://t.me/{config.bot_username}"

    import logging as _log
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
    try:
        result = await PaymentService.create_yookassa_sbp(plan["price"], plan_key, user_id, return_url)
    except Exception as sbp_err:
        _log.getLogger(__name__).error(f"Gift SBP error user={user_id}: {sbp_err}", exc_info=True)
        await callback.message.edit_text(
            i18n.t("err_sbp_create", lang),
            reply_markup=back_keyboard("menu_gift"),
        )
        await callback.answer()
        return

    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.create_pending(session, user_id, plan_key)
        gift = await GiftService.create(session, plan_key, user_id)
        from sqlalchemy import select as _select
        from models import GiftCode as _GiftCode
        g = await session.execute(_select(_GiftCode).where(_GiftCode.code == gift.code))
        g = g.scalar_one_or_none()
        if g:
            g.payment_ext_id = result["id"]
            await session.commit()
        await PaymentService.create(
            session,
            user_id=user_id,
            amount=plan["price"],
            currency="RUB",
            payment_method="yookassa_gift",
            plan=plan_key,
            subscription_id=sub.id,
            payment_ext_id=result["id"],
        )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t("btn_pay_sbp", lang), url=result["url"])],
        [InlineKeyboardButton(text=i18n.t("btn_paid", lang), callback_data=f"check_gift_{result['id']}")],
        [InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data="menu_gift")],
    ])
    await callback.message.edit_text(
        i18n.t("gift_payment_title", lang, period=plan['period']) + "\n\n"
        + i18n.t("gift_payment_sum", lang, price=plan['price']) + "\n\n"
        + i18n.t("gift_payment_after_sbp", lang),
        reply_markup=keyboard,
        parse_mode="HTML",
    )
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


# ──────────────────────────────────────────────────
# Донат через YooKassa
# ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_donate_yookassa_"))
async def pay_donate_yookassa(callback: CallbackQuery) -> None:
    try:
        amount = int(callback.data.replace("pay_donate_yookassa_", ""))
    except ValueError:
        await callback.answer("Неверная сумма", show_alert=True)
        return
    if amount < 1:
        await callback.answer("Минимум 1 ₽", show_alert=True)
        return

    user_id = callback.from_user.id
    return_url = config.webhook_url or "https://t.me/"

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
        await callback.message.edit_text(
            f"❤️ <b>Поддержка проекта — {amount} ₽</b>\n\n"
            "Нажмите кнопку для перехода к оплате:",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.edit_text(
            "❌ Ошибка при создании платежа. Попробуйте позже.",
            reply_markup=back_keyboard("menu_support"),
        )
    await callback.answer()
