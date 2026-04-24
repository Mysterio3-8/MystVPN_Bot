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

    ref_link = ReferralService.get_ref_link(user_id)
    until_milestone = REFERRAL_MILESTONE - (count % REFERRAL_MILESTONE) if count % REFERRAL_MILESTONE != 0 else REFERRAL_MILESTONE

    text = (
        f"👥 <b>Реферальная программа MystVPN</b>\n\n"
        f"Приводи друзей — получай дни бесплатного VPN!\n\n"
        f"🔗 <b>Твоя ссылка:</b>\n<code>{ref_link}</code>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Приведено друзей: <b>{count}</b>\n"
        f"• Накоплено дней: <b>{extra_days}</b>\n"
        f"• До milestone ({REFERRAL_MILESTONE} рефералов): <b>{until_milestone}</b>\n\n"
        f"🎁 <b>Условия:</b>\n"
        f"• За каждого друга: +<b>{REFERRAL_BONUS_DAYS} дней</b>\n"
        f"• За {REFERRAL_MILESTONE} рефералов: +<b>{REFERRAL_MILESTONE_DAYS} дней</b> (1 месяц!)\n\n"
        f"<i>Дни можно применить к активной подписке 👇</i>"
    )

    buttons = []
    if extra_days > 0 and has_active:
        buttons.append([InlineKeyboardButton(
            text=f"🎁 Применить {extra_days} дней к подписке",
            callback_data="cabinet_apply_bonus",
        )])
    elif extra_days > 0:
        buttons.append([InlineKeyboardButton(
            text=f"⚠️ Нет активной подписки (дни сохранены)",
            callback_data="menu_buy",
        )])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_target)])
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
        days_applied = await ReferralService.apply_bonus_days(session, user_id)

    if days_applied:
        await callback.message.edit_text(
            f"✅ <b>Готово!</b>\n\n"
            f"К твоей подписке добавлено <b>{days_applied} дней</b>!\n\n"
            f"Переходи в кабинет, чтобы увидеть новую дату окончания 👇",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="menu_cabinet")],
            ]),
            parse_mode="HTML",
        )
    else:
        await callback.answer("❌ Нет накопленных дней или нет активной подписки", show_alert=True)
    await callback.answer()
