from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import config

_connect_args = {"check_same_thread": False} if config.database_url.startswith("sqlite") else {}
engine = create_async_engine(config.database_url, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


_MIGRATIONS: list[str] = [
    "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS vpn_key VARCHAR(2048)",
]


async def init_db():
    from models import User, Subscription, Payment, Donation, GiftCode, PromoCode  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for sql in _MIGRATIONS:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass
