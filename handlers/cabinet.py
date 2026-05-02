from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, XrayService, i18n
from keyboards import cabinet_keyboard, confirm_cancel_keyboard, back_keyboard, reset_key_keyboard
from config import PLANS

router = Router()


async def _cabinet_text(user_id: int, lang: str) -> tuple[str, bool, bool, bool]:
    """Возвращает (text, has_sub, has_key, rotation_pending)."""
    from services import ReferralService, fmt_key
    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.get_active(session, user_id)
        user = await UserService.get(session, user_id)
        ref_count = await ReferralService.get_referral_count(session, user_id)
        extra_days = user.extra_days if user else 0

    if sub:
        plan_name = PLANS.get(sub.plan, {}).get("period", sub.plan) if sub.plan != "trial" else i18n.t("plan_trial", lang)
        trial_mark = " 🎁" if sub.is_trial else ""
        days_left = max(0, (sub.end_date - datetime.utcnow()).days)
        rotation_pending = bool(sub.new_vpn_key and sub.key_rotation_deadline and sub.key_rotation_deadline > datetime.utcnow())

        text = i18n.t("cabinet_title", lang) + "\n\n"
        text += i18n.t("cabinet_plan", lang, plan=f"{plan_name}{trial_mark}") + "\n"
        text += i18n.t("cabinet_expires", lang, date=sub.end_date.strftime('%d.%m.%Y'), days=days_left) + "\n"

        if rotation_pending:
            hours_left = max(0, int((sub.key_rotation_deadline - datetime.utcnow()).total_seconds() // 3600))
            text += "\n\n" + i18n.t("cabinet_rotation_title", lang) + "\n"
            text += i18n.t("cabinet_rotation_deadline", lang, hours=hours_left) + "\n\n"
            text += i18n.t("cabinet_rotation_old_label", lang)
            text += fmt_key(sub.vpn_key, sub.sub_url) + "\n\n"
            text += i18n.t("cabinet_rotation_new_label", lang)
            text += fmt_key(sub.new_vpn_key, sub.new_sub_url)
        elif sub.vpn_key or sub.sub_url:
            text += fmt_key(sub.vpn_key, sub.sub_url)
        else:
            text += "\n\n" + i18n.t("cabinet_no_key_warning", lang)

        if extra_days:
            text += "\n\n" + i18n.t("cabinet_bonus_days", lang, days=extra_days)
        if ref_count:
            text += "\n" + i18n.t("cabinet_ref_count", lang, count=ref_count)
        return text, True, bool(sub.vpn_key or sub.sub_url), rotation_pending

    text = i18n.t("cabinet_title", lang) + "\n\n" + i18n.t("cabinet_no_active_sub", lang) + "\n"
    if extra_days:
        text += "\n" + i18n.t("cabinet_accumulated_days", lang, days=extra_days)
    return text, False, False, False


@router.message(Command("cabinet"))
async def cmd_cabinet(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, message.from_user.id)
        lang = user.language if user else "ru"
    text, has_sub, has_key, rotation_pending = await _cabinet_text(message.from_user.id, lang)
    await message.answer(text, reply_markup=cabinet_keyboard(has_sub, has_key, lang, rotation_pending), parse_mode="HTML")


@router.callback_query(F.data == "menu_cabinet")
async def cabinet_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text, has_sub, has_key, rotation_pending = await _cabinet_text(callback.from_user.id, lang)
    await callback.message.edit_text(text, reply_markup=cabinet_keyboard(has_sub, has_key, lang, rotation_pending), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cabinet_history")
async def payment_history(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
        payments = await PaymentService.get_history(session, callback.from_user.id)

    title = i18n.t("payment_history_title", lang)
    if not payments:
        text = f"{title}{i18n.t('payment_history_empty', lang)}"
    else:
        lines = [f"{title}\n"]
        for p in payments:
            lines.append(
                f"• {p.created_at.strftime('%d.%m.%Y')} — {p.amount:.0f} {p.currency} 💳 [{p.status}]"
            )
        text = "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cabinet_guide")
async def connection_guide(callback: CallbackQuery) -> None:
    """Fallback — кнопка стала URL-кнопкой, но оставляем хендлер на случай старых клиентов."""
    await callback.answer()
    await callback.message.answer(
        "📖 Инструкция по подключению: http://keybest.cc/guide",
        disable_web_page_preview=False,
    )


@router.callback_query(F.data == "cabinet_cancel")
async def cancel_subscription_confirm(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    await callback.message.edit_text(
        i18n.t("cancel_sub_confirm", lang),
        reply_markup=confirm_cancel_keyboard(lang),
    )
    await callback.answer()


@router.callback_query(F.data == "cabinet_cancel_confirmed")
async def cancel_subscription_confirmed(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    sub_snapshot = None
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)
        if sub:
            sub_snapshot = {"vpn_key": sub.vpn_key}
        cancelled = await SubscriptionService.cancel(session, user_id)

    if cancelled:
        if sub_snapshot and sub_snapshot["vpn_key"]:
            client_uuid = XrayService._extract_uuid(sub_snapshot["vpn_key"])
            await XrayService.remove_client(user_id, client_uuid)
        await callback.message.edit_text(
            i18n.t("sub_cancelled", lang),
            reply_markup=back_keyboard("menu_cabinet", lang),
        )
    else:
        await callback.message.edit_text(
            i18n.t("sub_not_found", lang),
            reply_markup=back_keyboard("menu_cabinet", lang),
        )
    await callback.answer()


@router.callback_query(F.data == "cabinet_get_key")
async def get_key(callback: CallbackQuery) -> None:
    """Выдать ключ если он не был выдан при оплате (XRay был недоступен)."""
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)

    if not sub:
        await callback.answer(i18n.t("alert_no_active_sub", lang), show_alert=True)
        return

    if sub.vpn_key or sub.sub_url:
        await callback.answer(i18n.t("alert_key_already", lang), show_alert=True)
        return

    await callback.answer(i18n.t("alert_creating_key", lang))
    days_left = max(1, (sub.end_date - datetime.utcnow()).days)
    vpn_key, sub_url = await XrayService.create_client(user_id, days_left)

    if vpn_key:
        from services import fmt_key
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub.id, vpn_key, sub_url)
        text = i18n.t("alert_key_received", lang) + fmt_key(vpn_key, sub_url)
        await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(
            i18n.t("alert_xray_error", lang),
            reply_markup=back_keyboard("menu_cabinet", lang),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "cabinet_apply_rotation")
async def apply_rotation(callback: CallbackQuery) -> None:
    """Пользователь сам переключается на новый ключ досрочно."""
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)

    if not sub or not sub.new_vpn_key:
        await callback.answer("✅ Ротация уже применена", show_alert=True)
        return

    old_uuid = XrayService._extract_uuid(sub.vpn_key) if sub.vpn_key else None

    async with AsyncSessionLocal() as session:
        await SubscriptionService.apply_rotation(session, sub.id)

    # Удаляем старый ключ из 3x-ui
    if old_uuid:
        await XrayService.remove_client(user_id, old_uuid)

    await callback.answer("✅ Новый ключ активирован!", show_alert=True)

    # Обновляем кабинет
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
    text, has_sub, has_key, rotation_pending = await _cabinet_text(user_id, lang)
    await callback.message.edit_text(text, reply_markup=cabinet_keyboard(has_sub, has_key, lang, rotation_pending), parse_mode="HTML")


@router.callback_query(F.data == "cabinet_reset_key")
async def reset_key_confirm(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("reset_key_text", lang)
    await callback.message.edit_text(text, reply_markup=reset_key_keyboard(lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cabinet_reset_key_confirm")
async def reset_key_confirmed(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)

    if not sub:
        await callback.message.edit_text(
            i18n.t("sub_not_found", lang),
            reply_markup=back_keyboard("menu_cabinet", lang),
        )
        await callback.answer()
        return

    days_left = max(1, (sub.end_date - datetime.utcnow()).days)
    old_key = sub.vpn_key
    new_key, new_sub_url = await XrayService.reset_client(user_id, days_left, old_key)

    if new_key:
        from services import fmt_key
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub.id, new_key, new_sub_url)
        text = i18n.t("reset_key_success", lang) + fmt_key(new_key, new_sub_url)
    else:
        text = "❌ Не удалось сбросить ключ. Попробуйте позже или обратитесь в поддержку."

    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cabinet_bypass_help")
async def bypass_help(callback: CallbackQuery) -> None:
    """Инструкция: как настроить клиент, чтобы РФ-сервисы шли мимо VPN."""
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    await callback.message.answer(
        i18n.t("bypass_help_text", lang),
        parse_mode="HTML",
        disable_web_page_preview=True,
        reply_markup=back_keyboard("menu_cabinet", lang),
    )
    await callback.answer()


@router.callback_query(F.data == "cabinet_no_connection")
async def no_connection_help(callback: CallbackQuery) -> None:
    """Помощь при проблемах с подключением."""
    await callback.answer()
    await callback.message.answer(
        "⚠️ <b>Не подключается?</b>\n\n"
        "<b>1. Обнови подписку в приложении</b>\n"
        "Hiddify / v2rayTUN → нажми «Обновить» (Refresh).\n"
        "Получишь оба протокола: Reality + XHTTP — приложение само выберет рабочий.\n\n"
        "<b>2. Региональное отключение</b>\n"
        "В некоторых регионах РФ мобильный интернет временно ограничивается.\n"
        "Это не проблема с ключом — переключись на Wi-Fi или подожди.\n\n"
        "<b>3. Смени сервер в приложении</b>\n"
        "Выбери <b>🌐 MystVPN XHTTP</b> — лучше проходит через мобильный интернет.\n\n"
        "<b>4. Сброс ключа</b>\n"
        "Кабинет → 🔑 Сбросить ключ → получишь новый.\n\n"
        "💬 Поддержка: @Myst_support",
        parse_mode="HTML",
        reply_markup=back_keyboard("menu_cabinet", "ru"),
    )
