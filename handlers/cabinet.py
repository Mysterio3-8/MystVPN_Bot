from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from database import AsyncSessionLocal
from services import UserService, SubscriptionService, PaymentService, XrayService, i18n
from keyboards import cabinet_keyboard, confirm_cancel_keyboard, back_keyboard, reset_key_keyboard
from config import PLANS

router = Router()


async def _cabinet_text(user_id: int, lang: str) -> tuple[str, bool]:
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

        text = (
            f"👤 <b>Личный кабинет</b>\n\n"
            f"📦 Тариф: <b>{plan_name}{trial_mark}</b>\n"
            f"📅 Истекает: <b>{sub.end_date.strftime('%d.%m.%Y')}</b> (осталось {days_left} д.)\n"
        )

        # Subscription URL — главное, сырой ключ не показываем
        text += fmt_key(sub.vpn_key, sub.sub_url)

        if extra_days:
            text += f"\n\n🎁 Бонусных дней: <b>{extra_days}</b>"
        if ref_count:
            text += f"\n👥 Рефералов: <b>{ref_count}</b>"
        return text, True

    text = (
        f"👤 <b>Личный кабинет</b>\n\n"
        f"У тебя нет активной подписки.\n"
    )
    if extra_days:
        text += f"\n🎁 Накоплено реф-дней: <b>{extra_days}</b> (применятся после покупки)"
    return text, False


@router.message(Command("cabinet"))
async def cmd_cabinet(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, message.from_user.id)
        lang = user.language if user else "ru"
    text, has_sub = await _cabinet_text(message.from_user.id, lang)
    await message.answer(text, reply_markup=cabinet_keyboard(has_sub, lang), parse_mode="HTML")


@router.callback_query(F.data == "menu_cabinet")
async def cabinet_callback(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text, has_sub = await _cabinet_text(callback.from_user.id, lang)
    await callback.message.edit_text(text, reply_markup=cabinet_keyboard(has_sub, lang), parse_mode="HTML")
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
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("connection_guide", lang)
    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_cabinet", lang), parse_mode="HTML")
    await callback.answer()


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
    old_key = None
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        sub = await SubscriptionService.get_active(session, user_id)
        if sub:
            old_key = sub.vpn_key
        cancelled = await SubscriptionService.cancel(session, user_id)

    if cancelled:
        if old_key:
            client_uuid = XrayService._extract_uuid(old_key)
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
