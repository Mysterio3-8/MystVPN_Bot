"""
Watchdog истечения подписок.

Цикл каждые 30 минут:
1. Уведомление за 3 дня до конца
2. При истечении — disable ключа в 3x-ui (grace period 24ч)
3. После 24ч grace period — удаление ключа из 3x-ui
4. Синхронизация expiryTime для всех активных ключей (batch, первый раз при запуске)
"""
import asyncio
import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from database import AsyncSessionLocal
from models import Subscription, User
from services.xray_service import XrayService

logger = logging.getLogger(__name__)

GRACE_PERIOD_HOURS = 24
NOTIFY_DAYS_BEFORE = 3
WATCHDOG_INTERVAL = 30 * 60  # 30 минут

# Флаг: первый запуск — выполняем batch sync всех активных ключей
_batch_synced = False


async def _notify_expiring(bot) -> None:
    """Отправляет уведомление юзерам у кого <= 3 дней до конца, один раз."""
    threshold = datetime.utcnow() + timedelta(days=NOTIFY_DAYS_BEFORE)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == "active",
                Subscription.end_date <= threshold,
                Subscription.end_date > datetime.utcnow(),
                Subscription.notified_5d == False,  # переиспользуем поле как "notified_3d"
            )
        )
        subs = result.scalars().all()
        if not subs:
            return

        for sub in subs:
            sub.notified_5d = True
        await session.commit()

    for sub in subs:
        if not bot:
            continue
        days_left = max(0, (sub.end_date - datetime.utcnow()).days)
        try:
            await bot.send_message(
                sub.user_id,
                f"⏰ <b>Подписка заканчивается через {days_left} дн.</b>\n\n"
                f"Чтобы VPN продолжил работу — продли подписку 👇",
                reply_markup=_renew_keyboard(),
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Cannot notify user {sub.user_id}: {e}")


def _renew_keyboard():
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Продлить подписку", callback_data="menu_buy")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="menu_cabinet")],
    ])


async def _disable_expired(bot) -> None:
    """
    Находит подписки у которых end_date прошёл, но ключ ещё активен.
    Дисейблит ключ в 3x-ui и ставит key_disabled_at.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == "active",
                Subscription.end_date < datetime.utcnow(),
                Subscription.key_disabled_at == None,
                Subscription.vpn_key != None,
            )
        )
        expired = result.scalars().all()
        if not expired:
            return

        ids = [s.id for s in expired]
        user_keys = [(s.user_id, s.vpn_key, s.id) for s in expired]

        for sub in expired:
            sub.key_disabled_at = datetime.utcnow()
            sub.status = "expired"
        await session.commit()

    for user_id, vpn_key, sub_id in user_keys:
        try:
            await XrayService.disable_client(user_id, vpn_key)
            logger.info(f"Disabled key for user {user_id} sub {sub_id}")
        except Exception as e:
            logger.error(f"Failed to disable key for user {user_id}: {e}")


async def _delete_grace_period_keys() -> None:
    """
    Находит ключи которые дисейблены > 24ч назад и удаляет их из 3x-ui.
    """
    cutoff = datetime.utcnow() - timedelta(hours=GRACE_PERIOD_HOURS)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == "expired",
                Subscription.key_disabled_at != None,
                Subscription.key_disabled_at <= cutoff,
                Subscription.vpn_key != None,
            )
        )
        to_delete = result.scalars().all()
        if not to_delete:
            return

        user_keys = [(s.user_id, s.vpn_key, s.id) for s in to_delete]
        for sub in to_delete:
            sub.vpn_key = None
            sub.sub_url = None
        await session.commit()

    for user_id, vpn_key, sub_id in user_keys:
        try:
            client_uuid = XrayService._extract_uuid(vpn_key)
            if client_uuid:
                await XrayService.remove_client(user_id, client_uuid)
                logger.info(f"Deleted key from 3x-ui for user {user_id} sub {sub_id}")
        except Exception as e:
            logger.error(f"Failed to delete key for user {user_id}: {e}")


async def _sync_active_expiry_times() -> None:
    """
    Синхронизирует expiryTime в 3x-ui для всех активных подписок с ключами.
    Критически важно при первом запуске — фиксит ключи без срока.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription).where(
                Subscription.status == "active",
                Subscription.vpn_key != None,
                Subscription.end_date > datetime.utcnow(),
            )
        )
        active = result.scalars().all()

    if not active:
        return

    ok = 0
    fail = 0
    for sub in active:
        try:
            synced = await XrayService.sync_client_expiry(sub.user_id, sub.vpn_key, sub.end_date)
            if synced:
                ok += 1
            else:
                fail += 1
        except Exception as e:
            fail += 1
            logger.warning(f"Sync expiry failed for user {sub.user_id}: {e}")

    logger.info(f"Batch expiry sync: {ok} ok, {fail} failed out of {len(active)} active subs")


async def run_expiry_watchdog(bot=None) -> None:
    """Основной цикл watchdog. Запускается из main.py через asyncio.gather."""
    global _batch_synced
    logger.info("Expiry watchdog started")
    await asyncio.sleep(10)  # дать боту стартануть

    while True:
        try:
            # При первом запуске синхронизируем все ключи (batch fix для 15 юзеров)
            if not _batch_synced:
                logger.info("Running initial batch expiry sync for all active subscriptions...")
                await _sync_active_expiry_times()
                _batch_synced = True

            await _notify_expiring(bot)
            await _disable_expired(bot)
            await _delete_grace_period_keys()

        except Exception as e:
            logger.error(f"Expiry watchdog cycle error: {e}", exc_info=True)

        await asyncio.sleep(WATCHDOG_INTERVAL)
