import json
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import PromoCode


class PromoService:

    @staticmethod
    async def list_all(session: AsyncSession) -> list[PromoCode]:
        result = await session.execute(select(PromoCode).order_by(PromoCode.created_at.desc()))
        return list(result.scalars().all())

    @staticmethod
    async def get(session: AsyncSession, promo_id: int) -> PromoCode | None:
        result = await session.execute(select(PromoCode).where(PromoCode.id == promo_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_code(session: AsyncSession, code: str) -> PromoCode | None:
        result = await session.execute(select(PromoCode).where(PromoCode.code == code))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        code: str,
        discount_percent: int = 0,
        free_plan: str | None = None,
        max_uses: int = 0,
        valid_until: datetime | None = None,
    ) -> PromoCode:
        promo = PromoCode(
            code=code,
            discount_percent=discount_percent,
            free_plan=free_plan,
            max_uses=max_uses,
            valid_until=valid_until,
            is_active=True,
        )
        session.add(promo)
        await session.commit()
        await session.refresh(promo)
        return promo

    @staticmethod
    async def delete(session: AsyncSession, promo_id: int) -> bool:
        promo = await PromoService.get(session, promo_id)
        if not promo:
            return False
        await session.delete(promo)
        await session.commit()
        return True

    @staticmethod
    async def toggle_active(session: AsyncSession, promo_id: int) -> PromoCode | None:
        promo = await PromoService.get(session, promo_id)
        if not promo:
            return None
        promo.is_active = not promo.is_active
        await session.commit()
        return promo

    @staticmethod
    async def validate(session: AsyncSession, code: str) -> PromoCode | None:
        promo = await PromoService.get_by_code(session, code)
        if not promo or not promo.is_active:
            return None
        if promo.valid_until and datetime.utcnow() > promo.valid_until:
            return None
        if promo.max_uses and promo.used_count >= promo.max_uses:
            return None
        return promo

    @staticmethod
    async def increment_usage(session: AsyncSession, promo_id: int) -> None:
        promo = await PromoService.get(session, promo_id)
        if promo:
            promo.used_count += 1
            await session.commit()

    # ── In-memory fallback (используется когда Redis недоступен) ─────
    _memory_discounts: dict = {}

    # ── Redis helpers для скидок ──────────────────────────────────────

    @staticmethod
    def _redis_key(user_id: int) -> str:
        return f"promo_discount:{user_id}"

    @staticmethod
    async def save_discount(user_id: int, percent: int, promo_id: int, code: str) -> None:
        from config import config
        import redis.asyncio as aioredis
        import logging
        payload = {"percent": percent, "promo_id": promo_id, "code": code}
        try:
            r = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
            try:
                await r.set(PromoService._redis_key(user_id), json.dumps(payload), ex=1800)
                PromoService._memory_discounts[user_id] = payload
            finally:
                await r.aclose()
        except Exception as e:
            logging.warning(f"Redis discount save failed: {e} (using memory fallback)")
            PromoService._memory_discounts[user_id] = payload

    @staticmethod
    async def get_discount(user_id: int) -> dict | None:
        from config import config
        import redis.asyncio as aioredis
        import logging
        try:
            r = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
            try:
                raw = await r.get(PromoService._redis_key(user_id))
                if raw:
                    result = json.loads(raw)
                    PromoService._memory_discounts[user_id] = result
                    return result
                return None
            finally:
                await r.aclose()
        except Exception as e:
            logging.warning(f"Redis discount get failed: {e} (using memory fallback)")
            return PromoService._memory_discounts.get(user_id)

    @staticmethod
    async def clear_discount(user_id: int) -> None:
        from config import config
        import redis.asyncio as aioredis
        import logging
        PromoService._memory_discounts.pop(user_id, None)
        try:
            r = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
            try:
                await r.delete(PromoService._redis_key(user_id))
            finally:
                await r.aclose()
        except Exception as e:
            logging.warning(f"Redis discount clear failed: {e} (graceful degradation)")
