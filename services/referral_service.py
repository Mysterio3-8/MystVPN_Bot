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
from config import config, REFERRAL_BONUS_DAYS, REFERRAL_MILESTONE, REFERRAL_MILESTONE_DAYS

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
        """
        if new_user_id == referrer_id:
            return  # нельзя пригласить самого себя

        # Помечаем нового пользователя
        new_user = await session.execute(select(User).where(User.user_id == new_user_id))
        new_user = new_user.scalar_one_or_none()
        if not new_user or new_user.referred_by is not None:
            return  # уже обработан

        new_user.referred_by = referrer_id
        await session.commit()

        # Начисляем дни реферреру
        referrer = await session.execute(select(User).where(User.user_id == referrer_id))
        referrer = referrer.scalar_one_or_none()
        if not referrer:
            return

        referrer.extra_days = (referrer.extra_days or 0) + REFERRAL_BONUS_DAYS
        await session.commit()

        # Считаем общее количество рефералов реферрера
        count_result = await session.execute(
            select(func.count()).where(User.referred_by == referrer_id)
        )
        total_refs = count_result.scalar() or 0

        # Проверяем milestone
        milestone_hit = (total_refs % REFERRAL_MILESTONE == 0) and total_refs > 0

        # Уведомляем реферрера
        if bot:
            try:
                if milestone_hit:
                    referrer.extra_days += REFERRAL_MILESTONE_DAYS
                    await session.commit()
                    msg = (
                        f"🎉 <b>Milestone {total_refs} рефералов!</b>\n\n"
                        f"🎁 +{REFERRAL_BONUS_DAYS} дней — обычный бонус\n"
                        f"🏆 +{REFERRAL_MILESTONE_DAYS} дней — milestone бонус\n\n"
                        f"Итого накоплено: <b>{referrer.extra_days} дней</b>\n\n"
                        f"Применить: /cabinet → 👥 Рефералы → Применить бонус"
                    )
                else:
                    left = REFERRAL_MILESTONE - (total_refs % REFERRAL_MILESTONE)
                    msg = (
                        f"👥 По вашей ссылке зарегистрировался новый пользователь!\n\n"
                        f"🎁 Начислено: <b>+{REFERRAL_BONUS_DAYS} дней</b>\n"
                        f"Всего рефералов: <b>{total_refs}</b>\n"
                        f"До бонуса ещё: <b>{left}</b> чел.\n"
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

        user = await session.execute(select(User).where(User.user_id == user_id))
        user = user.scalar_one_or_none()
        if not user or not user.extra_days:
            return 0

        sub = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.end_date.desc())
        )
        sub = sub.scalar_one_or_none()
        if not sub:
            return 0

        days = user.extra_days
        sub.end_date = sub.end_date + timedelta(days=days)
        user.extra_days = 0
        await session.commit()
        return days
