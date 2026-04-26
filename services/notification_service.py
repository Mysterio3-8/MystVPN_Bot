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
INBOUND_CHECK_INTERVAL = 3600  # раз в час


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


async def _check_inbound_health(bot) -> None:
    """Проверяет доступность xray inbound. При отсутствии — пересоздаёт и рассылает новые ключи."""
    from services.xray_service import XrayService
    from config import config
    from models import Subscription
    from sqlalchemy import select

    status = await XrayService.test_connection()
    if "✅ 3x-ui подключён" in status:
        return

    logger.warning(f"Inbound watchdog: inbound недоступен — {status}")

    success, new_id = await XrayService.recreate_inbound()
    if not success:
        for admin_id in config.admin_ids:
            try:
                await bot.send_message(
                    admin_id,
                    f"🚨 <b>VPN inbound недоступен!</b>\n\n"
                    f"Попытка пересоздать — <b>провалилась</b>.\n"
                    f"Статус: {status}\n\n"
                    f"Проверь панель 3x-ui вручную.",
                    parse_mode="HTML",
                )
            except Exception:
                pass
        return

    # Переиздаём ключи всем активным пользователям
    reissued = 0
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Subscription).where(Subscription.status == "active"))
        subs = result.scalars().all()
        for sub in subs:
            days_left = max(1, (sub.end_date - datetime.utcnow()).days)
            try:
                vpn_key, sub_url = await XrayService.reset_client(sub.user_id, days_left, sub.vpn_key)
                if vpn_key:
                    sub.vpn_key = vpn_key
                    if sub_url:
                        sub.sub_url = sub_url
                    reissued += 1
                    await bot.send_message(
                        sub.user_id,
                        f"🔄 <b>Ваш VPN-ключ обновлён</b>\n\n"
                        f"Мы улучшили сервер. Новый ключ:\n\n"
                        f"<code>{vpn_key}</code>\n\n"
                        f"Замените старый ключ в приложении.",
                        parse_mode="HTML",
                    )
            except Exception as e:
                logger.warning(f"Inbound watchdog: reissue failed for user {sub.user_id}: {e}")
        await db.commit()

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                admin_id,
                f"✅ <b>Inbound автоматически пересоздан</b>\n\n"
                f"Новый ID: <b>{new_id}</b>\n"
                f"Ключи переизданы: <b>{reissued}/{len(subs)}</b>",
                parse_mode="HTML",
            )
        except Exception:
            pass


async def run_notification_loop(bot) -> None:
    """
    Бесконечный цикл. Запускается через asyncio.create_task() в main.py.
    """
    logger.info("🔔 Notification service started")
    inbound_check_counter = 0
    while True:
        try:
            await _send_expiry_notifications(bot)
        except Exception as e:
            logger.error(f"Notification loop error: {e}")

        # Проверяем inbound каждый час (раз в цикл, цикл = 6 часов → каждые 6 итераций)
        # Но CHECK_INTERVAL = 6ч, поэтому watchdog запустим отдельно со своим таймером
        await asyncio.sleep(CHECK_INTERVAL)


async def run_inbound_watchdog(bot) -> None:
    """Отдельный цикл проверки inbound. Запускается параллельно с основным."""
    logger.info("🛡️ Inbound watchdog started")
    await asyncio.sleep(60)  # первый запуск через минуту после старта
    while True:
        try:
            await _check_inbound_health(bot)
        except Exception as e:
            logger.error(f"Inbound watchdog error: {e}")
        await asyncio.sleep(INBOUND_CHECK_INTERVAL)
