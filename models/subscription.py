from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.db import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    plan: Mapped[str] = mapped_column(String(50), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    start_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    auto_renewal: Mapped[bool] = mapped_column(Boolean, default=False)
    vpn_key: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ── Subscription URL для клиентов типа v2rayTUN / Hiddify ─────────────────
    sub_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # ── Пробный период ────────────────────────────────────────────────────────
    is_trial: Mapped[bool] = mapped_column(Boolean, default=False)
    # ── Флаг — было ли отправлено уведомление об истечении ───────────────────
    notified_5d: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_1d: Mapped[bool] = mapped_column(Boolean, default=False)
    notified_0d: Mapped[bool] = mapped_column(Boolean, default=False)
    # ── Ротация ключей (grace period 24ч) ────────────────────────────────────
    # Новый ключ выдаётся заранее; старый удаляется только после deadline
    new_vpn_key: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    new_sub_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    key_rotation_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="subscriptions")
    payments: Mapped[list["Payment"]] = relationship(back_populates="subscription")
