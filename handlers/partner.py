"""
Партнёрский кабинет — команда /partner для партнёров-каналов.
Показывает: рефералов, платящих юзеров, выручку, заработок 30%.
"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database import AsyncSessionLocal
from services import UserService, ReferralService
from services.partner_service import PartnerService

router = Router()

PARTNER_COMMISSION_PCT = 30


@router.message(Command("partner"))
async def cmd_partner(message: Message) -> None:
    user_id = message.from_user.id

    async with AsyncSessionLocal() as session:
        user = await UserService.get(session, user_id)
        if not user or not user.is_partner:
            await message.answer(
                "❌ У вас нет партнёрского доступа.\n\n"
                "Для подключения к партнёрской программе напишите @Myst_support"
            )
            return

        stats = await PartnerService.get_stats(session, user_id)

    ref_link = ReferralService.get_ref_link(user_id)
    channel = user.partner_channel or "не указан"
    last_str = (
        stats["last_payment"].strftime("%d.%m.%Y") if stats["last_payment"] else "—"
    )

    text = (
        f"💼 <b>Партнёрский кабинет MystVPN</b>\n"
        f"Канал: <b>{channel}</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Привлечено пользователей: <b>{stats['total_referrals']}</b>\n"
        f"• Из них платящих: <b>{stats['paying_users']}</b>\n"
        f"• Суммарные платежи: <b>{stats['total_revenue']:.0f} ₽</b>\n"
        f"• Последний платёж: <b>{last_str}</b>\n\n"
        f"💰 <b>Ваш заработок ({PARTNER_COMMISSION_PCT}%):</b>\n"
        f"<b>{stats['partner_earnings']:.0f} ₽</b>\n\n"
        f"🔗 <b>Ваша реф-ссылка:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>Выплаты производятся по запросу. Для вывода напишите @Myst_support</i>"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Скопировать ссылку", url=ref_link)],
        [InlineKeyboardButton(text="💬 Запросить выплату", url="https://t.me/Myst_support")],
    ])

    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
