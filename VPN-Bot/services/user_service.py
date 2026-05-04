from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import User
from config import config


class UserService:

    @staticmethod
    async def get(session: AsyncSession, user_id: int) -> User | None:
        result = await session.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_or_create(
        session: AsyncSession,
        user_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> tuple[User, bool]:
        user = await UserService.get(session, user_id)
        if user:
            return user, False
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            is_admin=user_id in config.admin_ids,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user, True

    @staticmethod
    async def update_language(session: AsyncSession, user_id: int, lang: str) -> None:
        user = await UserService.get(session, user_id)
        if user:
            user.language = lang
            await session.commit()

    @staticmethod
    async def ban(session: AsyncSession, user_id: int, banned: bool = True) -> None:
        user = await UserService.get(session, user_id)
        if user:
            user.is_banned = banned
            await session.commit()

    @staticmethod
    async def get_all(session: AsyncSession) -> list[User]:
        result = await session.execute(select(User))
        return list(result.scalars().all())

    @staticmethod
    async def count(session: AsyncSession) -> int:
        result = await session.execute(select(User))
        return len(result.scalars().all())

    @staticmethod
    async def is_banned(session: AsyncSession, user_id: int) -> bool:
        user = await UserService.get(session, user_id)
        return user.is_banned if user else False
