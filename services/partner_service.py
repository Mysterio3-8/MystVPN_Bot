"""
Партнёрская программа MystVPN.
30% от всех платежей приведённых пользователей — пожизненно.
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import User, Payment

PARTNER_COMMISSION = 0.30


class PartnerService:

    @staticmethod
    async def get_stats(session: AsyncSession, partner_user_id: int) -> dict:
        """Полная статистика партнёра: рефералы, платящие, выручка, заработок."""

        # Все рефералы партнёра
        ref_result = await session.execute(
            select(func.count()).where(User.referred_by == partner_user_id)
        )
        total_referrals = ref_result.scalar() or 0

        # ID всех рефералов
        refs = await session.execute(
            select(User.user_id).where(User.referred_by == partner_user_id)
        )
        ref_ids = [r[0] for r in refs.all()]

        if not ref_ids:
            return {
                "total_referrals": 0,
                "paying_users": 0,
                "total_revenue": 0.0,
                "partner_earnings": 0.0,
                "last_payment": None,
            }

        # Завершённые платежи от рефералов
        payments_result = await session.execute(
            select(Payment)
            .where(
                Payment.user_id.in_(ref_ids),
                Payment.status == "completed",
                Payment.plan != "donation",
            )
            .order_by(Payment.created_at.desc())
        )
        payments = payments_result.scalars().all()

        total_revenue = sum(p.amount for p in payments)
        paying_users = len(set(p.user_id for p in payments))
        last_payment = payments[0].created_at if payments else None

        return {
            "total_referrals": total_referrals,
            "paying_users": paying_users,
            "total_revenue": total_revenue,
            "partner_earnings": round(total_revenue * PARTNER_COMMISSION, 2),
            "last_payment": last_payment,
        }

    @staticmethod
    async def get_all_partners(session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User).where(User.is_partner == True).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())
