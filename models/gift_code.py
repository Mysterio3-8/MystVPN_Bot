from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database.db import Base


class GiftCode(Base):
    __tablename__ = "gift_codes"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    plan_key: Mapped[str] = mapped_column(String(50), nullable=False)
    buyer_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    activated_by: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
