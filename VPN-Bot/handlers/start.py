import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal

_log = logging.getLogger(__name__)
from services import (
    UserService,
    SubscriptionService,
    GiftService,
    XrayService,
    ReferralService,
    PromoService,
    fmt_key,
    i18n,
    schedule_trial_sequence,
    send_referral_offer,
)
from keyboards import main_menu_keyboard, about_keyboard, back_keyboard
from config import PLANS, TRIAL_DAYS

router = Router()


async def _show_menu(message: Message, user_id: int, is_admin: bool, lang: str) -> None:
    text = i18n.t("welcome_message", lang)
    await message.answer(text, reply_markup=main_menu_keyboard(is_admin, lang))


async def _offer_trial(message: Message, lang: str) -> None:
    """Предложить пробный период новому пользователю."""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎁 {TRIAL_DAYS} дня бесплатно — попробовать", callback_data="trial_activate")],
        [InlineKeyboardButton(text="💳 Купить сразу", callback_data="menu_buy")],
    ])
    await message.answer(
        f"👋 <b>MystVPN</b>\n\n"
        f"VPN который работает в России.\n\n"
        f"Попробуй <b>{TRIAL_DAYS} дня бесплатно</b> прямо сейчас 👇",
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def _activate_gift(message: Message, code: str) -> None:
    vpn_key = None
    sub_url = None
    lang = "ru"
    async with AsyncSessionLocal() as session:
        user, _ = await UserService.get_or_create(
            session,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        lang = user.language

        gift = await GiftService.get_by_code(session, code)
        if not gift:
            await message.answer(i18n.t("gift_invalid", lang))
            return
        if not gift.is_paid:
            await message.answer("⏳ <b>Подарок ещё не оплачен.</b>\n\nОжидаем подтверждения платежа. Попробуй позже.", parse_mode="HTML")
            return
        if gift.is_used:
            await message.answer(i18n.t("gift_already_used", lang))
            return
        if gift.buyer_id == message.from_user.id:
            await message.answer(i18n.t("gift_self_use", lang))
            return

        plan = PLANS.get(gift.plan_key)
        if not plan:
            await message.answer(i18n.t("gift_invalid", lang))
            return

        await GiftService.activate(session, code, message.from_user.id)
        sub = await SubscriptionService.create_pending(session, message.from_user.id, gift.plan_key)
        await SubscriptionService.activate(session, sub.id)

        vpn_key, sub_url = await XrayService.create_client(message.from_user.id, plan["days"])
        if vpn_key:
            sub.vpn_key = vpn_key
            if sub_url:
                sub.sub_url = sub_url
            await session.commit()

    await message.answer(
        i18n.t("gift_activated", lang) + fmt_key(vpn_key, sub_url),
        parse_mode="HTML",
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    args = message.text.split()[1] if message.text and len(message.text.split()) > 1 else None

    if args and args.startswith("gift_"):
        await _activate_gift(message, args[5:])
        return

    # Deeplink с промокодом: /start promo_CODE или /start p_CODE
    if args and (args.startswith("promo_") or args.startswith("p_")):
        code = args[6:] if args.startswith("promo_") else args[2:]
        if code:
            async with AsyncSessionLocal() as session:
                from models import User as _User
                from sqlalchemy import select as _sel
                _u, _ = await UserService.get_or_create(
                    session, user_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                )
                promo = await PromoService.get_by_code(session, code)
                if promo and promo.is_active:
                    await PromoService.save_discount(message.from_user.id, promo.discount_percent, promo.id, code)
                    await message.answer(
                        f"🎟 <b>Промокод <code>{code}</code> активирован!</b>\n\n"
                        f"Скидка <b>{promo.discount_percent}%</b> будет применена автоматически.\n\n"
                        f"Выбери тариф 👇",
                        parse_mode="HTML",
                    )
                else:
                    await message.answer("❌ Промокод не найден или недействителен.", parse_mode="HTML")
            return

    # Обрабатываем реферальную ссылку: ?start=ref_USER_ID
    referrer_id: int | None = None
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args[4:])
        except ValueError:
            pass

    async with AsyncSessionLocal() as session:
        user, is_new = await UserService.get_or_create(
            session,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        if user.is_banned:
            await message.answer("❌ Вы заблокированы.")
            return

        # Обрабатываем реферал для нового или существующего пользователя без referred_by
        if referrer_id and referrer_id != message.from_user.id and user.referred_by is None:
            try:
                await ReferralService.process_referral(
                    session, message.from_user.id, referrer_id,
                    bot=message.bot,
                )
            except Exception as _e:
                _log.error(
                    f"Referral processing failed new_user={message.from_user.id} ref={referrer_id}: {_e}",
                    exc_info=True,
                )

        lang = user.language
        is_admin = user.is_admin
        trial_available = await SubscriptionService.is_trial_available(session, message.from_user.id)

    # Новым пользователям предлагаем триал
    if is_new and trial_available:
        await _offer_trial(message, lang)
        return

    await _show_menu(message, message.from_user.id, is_admin, lang)


@router.callback_query(F.data == "trial_activate")
async def trial_activate(callback: CallbackQuery) -> None:
    """Активировать пробный период по кнопке."""
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        sub = await SubscriptionService.create_trial(session, user_id)
        if not sub:
            await callback.answer("❌ Пробный период недоступен", show_alert=True)
            return

        vpn_key, sub_url = await XrayService.create_client(user_id, TRIAL_DAYS)
        if vpn_key:
            await SubscriptionService.save_key(session, sub.id, vpn_key, sub_url)
        trial_end = sub.end_date

    renew_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить подписку", callback_data="menu_buy")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="menu_cabinet")],
    ])
    await callback.message.edit_text(
        f"🎉 <b>Пробный период активирован!</b>\n"
        f"{TRIAL_DAYS} дня бесплатного VPN"
        f"{fmt_key(vpn_key, sub_url)}\n\n"
        f"<i>После триала — от 219 ₽/мес</i>",
        reply_markup=renew_keyboard,
        parse_mode="HTML",
    )
    await schedule_trial_sequence(user_id, trial_end)
    try:
        await send_referral_offer(callback.bot, user_id)
    except Exception:
        pass
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: Message) -> None:
    await cmd_start(message)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
        is_admin = user.is_admin if user else False
    text = i18n.t("welcome_message", lang)
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard(is_admin, lang))
    await callback.answer()


@router.callback_query(F.data == "menu_about")
async def about_handler(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("about_text", lang)
    await callback.message.edit_text(text, reply_markup=about_keyboard(lang))
    await callback.answer()


@router.callback_query(F.data == "about_payment_safety")
async def about_payment_safety(callback: CallbackQuery) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, callback.from_user.id)
        lang = user.language if user else "ru"
    text = i18n.t("payment_safety_text", lang)
    await callback.message.edit_text(text, reply_markup=back_keyboard("menu_about", lang), parse_mode="HTML")
    await callback.answer()


@router.message(Command("about"))
async def cmd_about(message: Message) -> None:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, message.from_user.id)
        lang = user.language if user else "ru"
    await message.answer(i18n.t("about_text", lang), reply_markup=about_keyboard(lang))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer("💬 Напишите нам: @Myst_support")
