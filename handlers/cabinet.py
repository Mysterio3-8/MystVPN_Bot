from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, XrayService, WireGuardService, i18n
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
        plan_name = PLANS.get(sub.plan, {}).get("period", sub.plan) if sub.plan != "trial" else f"Пробный ({sub.plan})"
        trial_mark = " 🎁" if sub.is_trial else ""
        days_left = max(0, (sub.end_date - datetime.utcnow()).days)
        rotation_pending = bool(sub.new_vpn_key and sub.key_rotation_deadline and sub.key_rotation_deadline > datetime.utcnow())

        text = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"📦 Тариф: <b>{plan_name}{trial_mark}</b>\n"
            f"📅 Истекает: <b>{sub.end_date.strftime('%d.%m.%Y')}</b> (осталось {days_left} д.)\n"
        )

        # Баннер ротации — показываем оба ключа
        if rotation_pending:
            hours_left = max(0, int((sub.key_rotation_deadline - datetime.utcnow()).total_seconds() // 3600))
            text += (
                f"\n\n🔄 <b>Обновление ключей</b>\n"
                f"⏰ Старый ключ отключится через <b>{hours_left} ч.</b>\n\n"
                f"<b>Текущий ключ (работает до отключения):</b>"
                f"{fmt_key(sub.vpn_key, sub.sub_url)}\n\n"
                f"<b>Новый ключ (переключись сейчас):</b>"
                f"{fmt_key(sub.new_vpn_key, sub.new_sub_url)}"
            )
        elif sub.vpn_key or sub.sub_url:
            # Subscription URL — главное, сырой ключ не показываем
            text += fmt_key(sub.vpn_key, sub.sub_url)
        else:
            text += "\n\n⚠️ <b>Ключ не выдан</b> — обратись в поддержку: @Myst_support"

        if extra_days:
            text += f"\n\n🎁 Бонусных дней: <b>{extra_days}</b>"
        if ref_count:
            text += f"\n👥 Рефералов: <b>{ref_count}</b>"
        return text, True, bool(sub.vpn_key or sub.sub_url), rotation_pending

    text = (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"У тебя нет активной подписки.\n"
    )
    if extra_days:
        text += f"\n🎁 Накоплено реф-дней: <b>{extra_days}</b> (применятся после покупки)"
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
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)
    text = i18n.t("connection_guide", lang)
    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    await callback.answer()
    # Автоматически отправить WireGuard файл если подписка активна
    if sub:
        wg_peer_id = sub.wg_peer_id
        if not wg_peer_id:
            wg_peer_id = await WireGuardService.create_peer(user_id)
            if wg_peer_id:
                async with AsyncSessionLocal() as session:
                    await SubscriptionService.save_wg_peer_id(session, sub.id, wg_peer_id)
        if wg_peer_id:
            conf = await WireGuardService.get_config(wg_peer_id)
            if conf:
                conf_file = BufferedInputFile(conf.encode(), filename="MystVPN.conf")
                await callback.message.answer_document(
                    conf_file,
                    caption=(
                        "📡 <b>Твой WireGuard ключ</b>\n\n"
                        "Импортируй в приложение <b>WireGuard</b>:\n"
                        "📱 Android / iPhone → «+» → Импорт из файла\n"
                        "💻 Windows / Mac → Импортировать туннель\n\n"
                        "✅ Работает для всех приложений без настройки"
                    ),
                    parse_mode="HTML",
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
            sub_snapshot = {"vpn_key": sub.vpn_key, "wg_peer_id": sub.wg_peer_id}
        cancelled = await SubscriptionService.cancel(session, user_id)

    if cancelled:
        if sub_snapshot:
            if sub_snapshot["vpn_key"]:
                client_uuid = XrayService._extract_uuid(sub_snapshot["vpn_key"])
                await XrayService.remove_client(user_id, client_uuid)
            if sub_snapshot["wg_peer_id"]:
                await WireGuardService.delete_peer(sub_snapshot["wg_peer_id"])
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
        await callback.answer("❌ Нет активной подписки", show_alert=True)
        return

    if sub.vpn_key or sub.sub_url:
        await callback.answer("✅ Ключ уже выдан — обнови кабинет", show_alert=True)
        return

    await callback.answer("⏳ Создаю ключ...")
    days_left = max(1, (sub.end_date - datetime.utcnow()).days)
    vpn_key, sub_url = await XrayService.create_client(user_id, days_left)

    if vpn_key:
        from services import fmt_key
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub.id, vpn_key, sub_url)
        text = f"✅ <b>Ключ успешно получен!</b>{fmt_key(vpn_key, sub_url)}"
        await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    else:
        await callback.message.edit_text(
            "❌ <b>Не удалось подключиться к VPN-панели.</b>\n\n"
            "Попробуй позже или напиши в поддержку: @Myst_support",
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
