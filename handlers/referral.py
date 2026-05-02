"""
Реферальная программа — хендлеры.
/referral — показать реф-ссылку и статистику
cabinet_referral — кнопка из кабинета (назад → кабинет)
menu_referral — кнопка из главного меню (назад → главное меню)
cabinet_apply_bonus — применить накопленные дни к подписке
"""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, ReferralService, SubscriptionService
from config import REFERRAL_BONUS_DAYS, REFERRAL_MILESTONE, REFERRAL_MILESTONE_DAYS

router = Router()


async def _referral_text(user_id: int, back_target: str = "menu_cabinet") -> tuple[str, InlineKeyboardMarkup]:
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        count = await ReferralService.get_referral_count(session, user_id)
        extra_days = user.extra_days if user else 0
        has_active = bool(await SubscriptionService.get_active(session, user_id))

    lang = user.language if user else "ru"
    ref_link = ReferralService.get_ref_link(user_id)
    until_milestone = REFERRAL_MILESTONE - (count % REFERRAL_MILESTONE) if count % REFERRAL_MILESTONE != 0 else REFERRAL_MILESTONE

    text = (
        i18n.t("ref_screen_title", lang) + "\n\n"
        + i18n.t("ref_screen_intro", lang) + "\n\n"
        + i18n.t("ref_screen_link_label", lang) + "\n<code>" + ref_link + "</code>\n\n"
        + i18n.t("ref_screen_stats_label", lang) + "\n"
        + i18n.t("ref_screen_friends_count", lang, count=count) + "\n"
        + i18n.t("ref_screen_days_total", lang, days=extra_days) + "\n"
        + i18n.t("ref_screen_until_milestone", lang, milestone=REFERRAL_MILESTONE, remaining=until_milestone) + "\n\n"
        + i18n.t("ref_screen_terms_title", lang) + "\n"
        + i18n.t("ref_screen_per_friend", lang, days=REFERRAL_BONUS_DAYS) + "\n"
        + i18n.t("ref_screen_milestone_bonus", lang, milestone=REFERRAL_MILESTONE, days=REFERRAL_MILESTONE_DAYS) + "\n\n"
        + i18n.t("ref_screen_apply_hint", lang)
    )

    buttons = []
    if extra_days > 0 and has_active:
        buttons.append([InlineKeyboardButton(
            text=i18n.t("btn_apply_bonus", lang, days=extra_days),
            callback_data="cabinet_apply_bonus",
        )])
    elif extra_days > 0:
        buttons.append([InlineKeyboardButton(
            text=i18n.t("btn_no_active_sub", lang),
            callback_data="menu_buy",
        )])
    buttons.append([InlineKeyboardButton(text=i18n.t("btn_back", lang), callback_data=back_target)])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return text, keyboard


@router.message(Command("referral"))
async def cmd_referral(message: Message) -> None:
    text, keyboard = await _referral_text(message.from_user.id, back_target="back_to_menu")
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# Открытие рефералов из ГЛАВНОГО МЕНЮ → назад в главное меню
@router.callback_query(F.data == "menu_referral")
async def menu_referral(callback: CallbackQuery) -> None:
    text, keyboard = await _referral_text(callback.from_user.id, back_target="back_to_menu")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


# Открытие рефералов из КАБИНЕТА → назад в кабинет
@router.callback_query(F.data == "cabinet_referral")
async def cabinet_referral(callback: CallbackQuery) -> None:
    text, keyboard = await _referral_text(callback.from_user.id, back_target="menu_cabinet")
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "cabinet_apply_bonus")
async def apply_bonus(callback: CallbackQuery) -> None:
    user_id = callback.from_user.id
    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        lang = user.language if user else "ru"
        days_applied = await ReferralService.apply_bonus_days(session, user_id)

    if days_applied:
        await callback.message.edit_text(
            i18n.t("ref_applied_title", lang, days=days_applied),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=i18n.t("btn_cabinet", lang), callback_data="menu_cabinet")],
            ]),
            parse_mode="HTML",
        )
    else:
        await callback.answer(i18n.t("alert_no_bonus", lang), show_alert=True)
    await callback.answer()
