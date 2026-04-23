"""
Фоновые уведомления об истечении подписки.
Запускается как asyncio-задача в main.py.
Проверяет каждые 6 часов, кому надо отправить напоминание.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Subscription
from config import EXPIRY_DISCOUNT_PERCENT

logger = logging.getLogger(__name__)

CHECK_INTERVAL = 6 * 3600   # раз в 6 часов


async def _send_expiry_notifications(bot) -> None:
    """Проверяет активные подписки и рассылает уведомления."""
    now = datetime.utcnow()

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(Subscription.status == "active")
        )
        subs = result.scalars().all()

    for sub in subs:
        days_left = (sub.end_date - now).days
        try:
            await _notify_if_needed(bot, sub, days_left)
        except Exception as e:
            logger.warning(f"Notification error for sub {sub.id}: {e}")


async def _notify_if_needed(bot, sub: Subscription, days_left: int) -> None:
    """Отправить уведомление если нужно и ещё не отправляли."""
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    async with AsyncSessionLocal() as session:
        # Обновляем объект внутри новой сессии
        from sqlalchemy import select as sel
        result = await session.execute(sel(Subscription).where(Subscription.id == sub.id))
        sub_db = result.scalar_one_or_none()
        if not sub_db or sub_db.status != "active":
            return

        if days_left == 5 and not sub_db.notified_5d:
            text = (
                f"🔔 <b>Твой VPN истекает через 5 дней</b>\n\n"
                f"Тариф: <b>{sub_db.plan.replace('_', ' ').title()}</b>\n"
                f"Дата окончания: <b>{sub_db.end_date.strftime('%d.%m.%Y')}</b>\n\n"
                f"Продли сейчас, чтобы не терять доступ 👇"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="menu_buy")],
            ])
            await bot.send_message(sub_db.user_id, text, reply_markup=keyboard, parse_mode="HTML")
            sub_db.notified_5d = True
            await session.commit()

        elif days_left == 1 and not sub_db.notified_1d:
            text = (
                f"⚠️ <b>Твой VPN истекает ЗАВТРА!</b>\n\n"
                f"Не теряй доступ — продли прямо сейчас 👇"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="menu_buy")],
                [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="menu_cabinet")],
            ])
            await bot.send_message(sub_db.user_id, text, reply_markup=keyboard, parse_mode="HTML")
            sub_db.notified_1d = True
            await session.commit()

        elif days_left == 0 and not sub_db.notified_0d:
            text = (
                f"🚨 <b>Твой VPN истёк сегодня!</b>\n\n"
                f"🎁 Специально для тебя — скидка <b>{EXPIRY_DISCOUNT_PERCENT}%</b> только сегодня!\n\n"
                f"Используй промокод: <code>RENEW{EXPIRY_DISCOUNT_PERCENT}</code>\n"
                f"при оплате любого тарифа 👇"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=f"🔥 Продлить со скидкой {EXPIRY_DISCOUNT_PERCENT}%", callback_data="menu_buy")],
            ])
            await bot.send_message(sub_db.user_id, text, reply_markup=keyboard, parse_mode="HTML")
            sub_db.notified_0d = True
            await session.commit()


async def run_notification_loop(bot) -> None:
    """
    Бесконечный цикл. Запускается через asyncio.create_task() в main.py.
    """
    logger.info("🔔 Notification service started")
    while True:
        try:
            await _send_expiry_notifications(bot)
        except Exception as e:
            logger.error(f"Notification loop error: {e}")
        await asyncio.sleep(CHECK_INTERVAL)
