from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Subscription, User
from config import PLANS, TRIAL_DAYS


class SubscriptionService:

    @staticmethod
    async def get_active(session: AsyncSession, user_id: int) -> Subscription | None:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id, Subscription.status == "active")
            .order_by(Subscription.end_date.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_all_for_user(session: AsyncSession, user_id: int) -> list[Subscription]:
        result = await session.execute(
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_pending(session: AsyncSession, user_id: int, plan_key: str) -> Subscription:
        plan = PLANS[plan_key]
        end_date = datetime.utcnow() + timedelta(days=plan["days"])
        sub = Subscription(
            user_id=user_id,
            plan=plan_key,
            price=plan["price"],
            status="pending",
            end_date=end_date,
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub

    @staticmethod
    async def create_trial(session: AsyncSession, user_id: int) -> Subscription | None:
        """
        Создаёт и активирует пробную подписку (TRIAL_DAYS дней, бесплатно).
        Возвращает None если пользователь уже использовал триал или есть активная подписка.
        """
        # Проверяем что нет активной подписки
        active = await SubscriptionService.get_active(session, user_id)
        if active:
            return None

        # Проверяем флаг trial_used у пользователя
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        if not user or user.trial_used:
            return None

        end_date = datetime.utcnow() + timedelta(days=TRIAL_DAYS)
        sub = Subscription(
            user_id=user_id,
            plan="trial",
            price=0.0,
            status="active",
            start_date=datetime.utcnow(),
            end_date=end_date,
            is_trial=True,
        )
        session.add(sub)
        user.trial_used = True
        await session.commit()
        await session.refresh(sub)
        return sub

    @staticmethod
    async def is_trial_available(session: AsyncSession, user_id: int) -> bool:
        """Может ли пользователь воспользоваться триалом."""
        active = await SubscriptionService.get_active(session, user_id)
        if active:
            return False
        user_result = await session.execute(select(User).where(User.user_id == user_id))
        user = user_result.scalar_one_or_none()
        return bool(user and not user.trial_used)

    @staticmethod
    async def activate(session: AsyncSession, subscription_id: int) -> Subscription | None:
        result = await session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.status = "active"
            sub.start_date = datetime.utcnow()
            await session.commit()
        return sub

    @staticmethod
    async def cancel(session: AsyncSession, user_id: int) -> bool:
        sub = await SubscriptionService.get_active(session, user_id)
        if sub:
            sub.status = "cancelled"
            await session.commit()
            return True
        return False

    @staticmethod
    async def save_key(session: AsyncSession, subscription_id: int, vpn_key: str, sub_url: str | None = None) -> None:
        result = await session.execute(
            select(Subscription).where(Subscription.id == subscription_id)
        )
        sub = result.scalar_one_or_none()
        if sub:
            sub.vpn_key = vpn_key
            if sub_url:
                sub.sub_url = sub_url
            await session.commit()

    @staticmethod
    async def count_active(session: AsyncSession) -> int:
        result = await session.execute(
            select(Subscription).where(Subscription.status == "active")
        )
        return len(result.scalars().all())
