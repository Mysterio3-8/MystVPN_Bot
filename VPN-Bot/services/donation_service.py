from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from models import Donation


class DonationService:

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        username: str | None,
        first_name: str | None,
        amount_stars: int,
    ) -> Donation:
        donation = Donation(
            user_id=user_id,
            username=username,
            first_name=first_name,
            amount_stars=amount_stars,
        )
        session.add(donation)
        await session.commit()
        return donation

    @staticmethod
    async def record_rub(
        session: AsyncSession,
        user_id: int,
        username: str | None,
        first_name: str | None,
        amount_rub: float,
    ) -> Donation:
        """Записывает рублёвый донат (YooKassa) в таблицу donations для спонсорского рейтинга."""
        donation = Donation(
            user_id=user_id,
            username=username,
            first_name=first_name,
            amount_stars=int(amount_rub),  # храним рубли в том же поле
        )
        session.add(donation)
        await session.commit()
        return donation

    @staticmethod
    async def get_top_sponsors(session: AsyncSession, limit: int = 20) -> list[tuple[str, int]]:
        """Возвращает топ спонсоров из таблицы donations (рубли и Stars)."""
        result = await session.execute(
            select(
                Donation.user_id,
                Donation.username,
                Donation.first_name,
                func.sum(Donation.amount_stars).label("total"),
            )
            .group_by(Donation.user_id, Donation.username, Donation.first_name)
            .order_by(desc("total"))
            .limit(limit)
        )
        rows = result.all()
        sponsors = []
        for row in rows:
            name = f"@{row.username}" if row.username else (row.first_name or "Аноним")
            sponsors.append((name, int(row.total)))
        return sponsors
