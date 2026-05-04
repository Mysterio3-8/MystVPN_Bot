"""
Реферальная программа MystVPN
─────────────────────────────
• +REFERRAL_BONUS_DAYS дней к подписке за каждого приведённого друга
• При достижении REFERRAL_MILESTONE рефералов — REFERRAL_MILESTONE_DAYS дней бесплатно
• Уникальная реф-ссылка: t.me/BOT?start=ref_USER_ID
"""
import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Subscription
from config import config, REFERRAL_BONUS_DAYS

logger = logging.getLogger(__name__)


class ReferralService:

    @staticmethod
    def get_ref_link(user_id: int) -> str:
        """Возвращает уникальную реф-ссылку пользователя."""
        return f"https://t.me/{config.bot_username}?start=ref_{user_id}"

    @staticmethod
    async def get_referral_count(session: AsyncSession, user_id: int) -> int:
        """Количество пользователей, которых привёл user_id."""
        result = await session.execute(
            select(func.count()).where(User.referred_by == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def process_referral(
        session: AsyncSession,
        new_user_id: int,
        referrer_id: int,
        bot=None,
    ) -> None:
        """
        Обработать реферал: записать кто привёл, добавить дни реферреру.
        Вызывается один раз при регистрации нового пользователя.
        Одна атомарная транзакция с row lock для избежания race condition.
        """
        if new_user_id == referrer_id:
            return

        new_user = await session.execute(select(User).where(User.user_id == new_user_id).with_for_update())
        new_user = new_user.scalar_one_or_none()
        if not new_user or new_user.referred_by is not None:
            return

        new_user.referred_by = referrer_id

        referrer = await session.execute(select(User).where(User.user_id == referrer_id).with_for_update())
        referrer = referrer.scalar_one_or_none()
        if not referrer:
            await session.rollback()
            return

        referrer.extra_days = (referrer.extra_days or 0) + REFERRAL_BONUS_DAYS

        await session.flush()

        count_result = await session.execute(
            select(func.count()).where(User.referred_by == referrer_id)
        )
        total_refs = count_result.scalar() or 0

        await session.commit()

        if bot:
            try:
                msg = (
                    f"👥 По вашей ссылке зарегистрировался новый пользователь!\n\n"
                    f"🎁 Начислено: <b>+{REFERRAL_BONUS_DAYS} дней</b>\n"
                    f"Всего рефералов: <b>{total_refs}</b>\n"
                    f"Накоплено: <b>{referrer.extra_days} дней</b>\n\n"
                    f"Применить: /cabinet → 👥 Рефералы → Применить бонус"
                )
                await bot.send_message(referrer_id, msg, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Cannot notify referrer {referrer_id}: {e}")

    @staticmethod
    async def apply_bonus_days(session: AsyncSession, user_id: int) -> int:
        """
        Применить накопленные дни к активной подписке.
        Возвращает количество применённых дней (0 если нечего применять или нет подписки).
        """
        from datetime import timedelta
        from models import Subscription

        user = await session.execute(select(User).where(User.user_id == user_id).with_for_update())
        user = user.scalar_one_or_none()
        if not user or not user.extra_days:
            return 0

        sub = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.end_date.desc())
            .with_for_update()
        )
        sub = sub.scalar_one_or_none()
        if not sub:
            return 0

        days = user.extra_days
        sub.end_date = sub.end_date + timedelta(days=days)
        user.extra_days = 0
        await session.commit()
        return days

    @staticmethod
    async def run_monthly_credit(bot=None) -> None:
        """Ежемесячное начисление дней за активных рефералов (только с активной подпиской)."""
        from datetime import date
        from database import AsyncSessionLocal
        import redis.asyncio as aioredis

        month_key = f"referral_monthly_credit:{date.today().strftime('%Y-%m')}"
        r = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        try:
            already_ran = await r.exists(month_key)
        finally:
            await r.aclose()
        if already_ran:
            return

        async with AsyncSessionLocal() as session:
            rows = await session.execute(
                select(User.referred_by).where(User.referred_by.isnot(None)).distinct()
            )
            referrer_ids = [row[0] for row in rows.fetchall()]

        for referrer_id in referrer_ids:
            async with AsyncSessionLocal() as session:
                active_count_result = await session.execute(
                    select(func.count())
                    .select_from(User)
                    .join(
                        Subscription,
                        (Subscription.user_id == User.user_id)
                        & (Subscription.status == "active")
                        & (Subscription.is_trial.is_(False)),
                    )
                    .where(User.referred_by == referrer_id)
                )
                active_count = active_count_result.scalar() or 0
                if active_count == 0:
                    continue

                days_to_add = active_count * REFERRAL_BONUS_DAYS
                referrer_res = await session.execute(
                    select(User).where(User.user_id == referrer_id).with_for_update()
                )
                referrer = referrer_res.scalar_one_or_none()
                if not referrer:
                    continue

                referrer.extra_days = (referrer.extra_days or 0) + days_to_add
                await session.commit()

                if bot:
                    try:
                        await bot.send_message(
                            referrer_id,
                            f"💰 <b>Ежемесячный реферальный бонус!</b>\n\n"
                            f"Активных рефералов: <b>{active_count}</b>\n"
                            f"Начислено: <b>+{days_to_add} дней</b>\n\n"
                            f"Применить: /cabinet → 👥 Рефералы → Применить бонус",
                            parse_mode="HTML",
                        )
                    except Exception as e:
                        logger.warning(f"Cannot notify referrer {referrer_id} monthly: {e}")

        r = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        try:
            await r.set(month_key, "1", ex=35 * 86400)
        finally:
            await r.aclose()
        logger.info(f"Monthly referral credit done for {len(referrer_ids)} referrers")
