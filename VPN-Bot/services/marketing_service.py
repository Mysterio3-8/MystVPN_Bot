import asyncio
import json
import logging
import time
from datetime import datetime

import redis.asyncio as aioredis
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import select

from config import EXPIRY_DISCOUNT_PERCENT, config
from database import AsyncSessionLocal
from models import Payment, Subscription
from services.promo_service import PromoService
from services.referral_service import ReferralService

logger = logging.getLogger(__name__)

SCHEDULE_KEY = "marketing:scheduled"
ABANDONED_SCORES_KEY = "marketing:abandoned_scores"
ABANDONED_PLANS_KEY  = "marketing:abandoned_plans"
CHECK_INTERVAL = 60


def _now_ts() -> int:
    return int(time.time())


async def _redis():
    return aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")


async def _schedule(kind: str, user_id: int, delay_seconds: int, **payload) -> None:
    item = {
        "kind": kind,
        "user_id": user_id,
        "scheduled_at": datetime.utcnow().isoformat(),
        **payload,
    }
    member = json.dumps(item, ensure_ascii=False, sort_keys=True)
    try:
        r = await _redis()
        try:
            await r.zadd(SCHEDULE_KEY, {member: _now_ts() + delay_seconds})
        finally:
            await r.aclose()
    except Exception as e:
        logger.warning(f"Marketing schedule failed: {e}")


async def schedule_trial_sequence(user_id: int, trial_end: datetime) -> None:
    await _schedule("trial_speed_check", user_id, 3600)
    await _schedule("trial_24h_discount", user_id, 24 * 3600)
    delay = max(60, int((trial_end - datetime.utcnow()).total_seconds()) - 12 * 3600)
    await _schedule("trial_12h_last_chance", user_id, delay)


async def schedule_abandoned_checkout(user_id: int, plan_key: str) -> None:
    fire_at = _now_ts() + 30 * 60
    try:
        r = await _redis()
        try:
            await r.hset(ABANDONED_PLANS_KEY, str(user_id), plan_key)
            await r.zadd(ABANDONED_SCORES_KEY, {str(user_id): fire_at})
        finally:
            await r.aclose()
    except Exception as e:
        logger.warning(f"Marketing schedule abandoned failed: {e}")


async def _has_completed_after(user_id: int, since: datetime) -> bool:
    async with AsyncSessionLocal() as session:
        payment = await session.execute(
            select(Payment)
            .where(
                Payment.user_id == user_id,
                Payment.status == "completed",
                Payment.created_at >= since,
            )
            .limit(1)
        )
        if payment.scalar_one_or_none():
            return True
        sub = await session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.start_date >= since,
                Subscription.plan != "trial",
            )
            .limit(1)
        )
        return sub.scalar_one_or_none() is not None


async def _has_active_trial(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.is_trial.is_(True),
                Subscription.end_date > datetime.utcnow(),
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None


async def _send_trial_message(bot, item: dict) -> None:
    user_id = int(item["user_id"])
    if not await _has_active_trial(user_id):
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Продлить со скидкой {EXPIRY_DISCOUNT_PERCENT}%", callback_data="menu_buy")],
        [InlineKeyboardButton(text="Личный кабинет", callback_data="menu_cabinet")],
    ])
    kind = item["kind"]
    if kind == "trial_speed_check":
        text = (
            "🚀 <b>Ну как скорость MystVPN?</b>\n\n"
            "Если всё работает хорошо, можешь заранее продлить доступ и не ждать конца пробника."
        )
    elif kind == "trial_24h_discount":
        await PromoService.save_discount(user_id, EXPIRY_DISCOUNT_PERCENT, 0, f"TRIAL{EXPIRY_DISCOUNT_PERCENT}")
        text = (
            "⏳ <b>Осталось 2 дня пробного доступа</b>\n\n"
            f"Продли сейчас со скидкой <b>{EXPIRY_DISCOUNT_PERCENT}%</b>, чтобы VPN не отключился."
        )
    else:
        await PromoService.save_discount(user_id, EXPIRY_DISCOUNT_PERCENT, 0, f"TRIAL{EXPIRY_DISCOUNT_PERCENT}")
        text = (
            "🔥 <b>Сегодня последний шанс продлить пробник со скидкой</b>\n\n"
            f"Скидка <b>{EXPIRY_DISCOUNT_PERCENT}%</b> уже применена к следующей оплате."
        )
    await bot.send_message(user_id, text, reply_markup=keyboard, parse_mode="HTML")


async def _send_abandoned_checkout_user(bot, user_id: int, plan_key: str) -> None:
    from datetime import timedelta
    since = datetime.utcnow() - timedelta(minutes=31)
    if await _has_completed_after(user_id, since):
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Оплатить", callback_data=f"plan_{plan_key}")],
        [InlineKeyboardButton(text="Выбрать другой тариф", callback_data="menu_buy")],
    ])
    await bot.send_message(
        user_id,
        "💳 <b>Ты почти подключил MystVPN</b>\n\n"
        "Тариф уже выбран. Вернись к оплате, чтобы получить ключ без ожидания.",
        reply_markup=keyboard,
        parse_mode="HTML",
    )



async def run_marketing_loop(bot) -> None:
    logger.info("📣 Marketing service started")
    while True:
        try:
            # Trial sequence messages
            r = await _redis()
            try:
                due = await r.zrangebyscore(SCHEDULE_KEY, 0, _now_ts(), start=0, num=25)
                if due:
                    await r.zrem(SCHEDULE_KEY, *due)
            finally:
                await r.aclose()

            for raw in due:
                item = json.loads(raw)
                try:
                    if item["kind"].startswith("trial_"):
                        await _send_trial_message(bot, item)
                except Exception as e:
                    logger.warning(f"Marketing item failed: {e}")

            # Abandoned checkout (per-user dedup)
            r = await _redis()
            try:
                due_ids = await r.zrangebyscore(ABANDONED_SCORES_KEY, 0, _now_ts(), start=0, num=25)
                if due_ids:
                    await r.zrem(ABANDONED_SCORES_KEY, *due_ids)
                    plan_vals = await r.hmget(ABANDONED_PLANS_KEY, *due_ids)
                    await r.hdel(ABANDONED_PLANS_KEY, *due_ids)
                else:
                    due_ids, plan_vals = [], []
            finally:
                await r.aclose()

            for uid_b, plan_b in zip(due_ids, plan_vals):
                uid = int(uid_b)
                pk = (plan_b or b"1_month").decode()
                try:
                    await _send_abandoned_checkout_user(bot, uid, pk)
                except Exception as e:
                    logger.warning(f"Abandoned checkout uid={uid}: {e}")

            # Monthly referral credit
            try:
                from services.referral_service import ReferralService
                await ReferralService.run_monthly_credit(bot)
            except Exception as e:
                logger.warning(f"Monthly referral credit error: {e}")

        except Exception as e:
            logger.warning(f"Marketing loop error: {e}")

        await asyncio.sleep(CHECK_INTERVAL)
