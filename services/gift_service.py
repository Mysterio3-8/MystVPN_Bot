import secrets
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import GiftCode


class GiftService:

    @staticmethod
    async def create(session: AsyncSession, plan_key: str, buyer_id: int) -> GiftCode:
        code = secrets.token_urlsafe(16)
        gift = GiftCode(code=code, plan_key=plan_key, buyer_id=buyer_id)
        session.add(gift)
        await session.commit()
        await session.refresh(gift)
        return gift

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> GiftCode | None:
        result = await session.execute(
            select(GiftCode).where(GiftCode.code == code)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def activate(session: AsyncSession, code: str, recipient_id: int) -> GiftCode | None:
        result = await session.execute(
            select(GiftCode).where(GiftCode.code == code)
        )
        gift = result.scalar_one_or_none()
        if not gift or gift.is_used:
            return None
        gift.is_used = True
        gift.activated_by = recipient_id
        gift.activated_at = datetime.utcnow()
        await session.commit()
        return gift
