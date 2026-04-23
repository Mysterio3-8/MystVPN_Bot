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
    async def get_top_sponsors(session: AsyncSession, limit: int = 20) -> list[tuple[str, int]]:
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
