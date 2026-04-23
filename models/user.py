from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(10), default="ru")
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Реферальная программа ─────────────────────────────────────────────────
    referred_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True, default=None)
    extra_days: Mapped[int] = mapped_column(Integer, default=0)   # накоплено за рефералов

    # ── Пробный период ────────────────────────────────────────────────────────
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)

    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[list["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")
