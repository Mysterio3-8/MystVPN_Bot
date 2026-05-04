from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from models import Payment
from config import config

try:
    from yookassa import Configuration, Payment as YooPayment
    Configuration.account_id = config.yookassa_account_id
    Configuration.secret_key = config.yookassa_secret_key
    YOOKASSA_AVAILABLE = True
except ImportError:
    YOOKASSA_AVAILABLE = False


class PaymentService:

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: int,
        amount: float,
        currency: str,
        payment_method: str,
        plan: str,
        subscription_id: int | None = None,
        payment_ext_id: str | None = None,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            payment_method=payment_method,
            plan=plan,
            subscription_id=subscription_id,
            payment_ext_id=payment_ext_id,
            status="pending",
        )
        session.add(payment)
        await session.commit()
        await session.refresh(payment)
        return payment

    @staticmethod
    async def complete(session: AsyncSession, payment_id: int) -> Payment | None:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = "completed"
            payment.completed_at = datetime.utcnow()
            await session.commit()
        return payment

    @staticmethod
    async def get_by_ext_id(session: AsyncSession, ext_id: str) -> Payment | None:
        result = await session.execute(
            select(Payment).where(Payment.payment_ext_id == ext_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_history(session: AsyncSession, user_id: int, limit: int = 10) -> list[Payment]:
        result = await session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def total_revenue(session: AsyncSession) -> float:
        result = await session.execute(
            select(func.sum(Payment.amount)).where(Payment.status == "completed", Payment.currency == "RUB")
        )
        return result.scalar_one_or_none() or 0.0

    @staticmethod
    async def create_yookassa_payment(amount: float, plan_key: str, user_id: int, return_url: str) -> dict:
        if not YOOKASSA_AVAILABLE:
            raise RuntimeError("yookassa не установлен")
        import uuid
        payment = YooPayment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": f"MystVPN подписка — {plan_key}",
            "metadata": {"user_id": user_id, "plan": plan_key},
        }, uuid.uuid4())
        return {"id": payment.id, "url": payment.confirmation.confirmation_url}

    @staticmethod
    async def create_yookassa_sbp(amount: float, plan_key: str, user_id: int, return_url: str) -> dict:
        """Создаёт платёж через СБП (Система Быстрых Платежей) в YooKassa."""
        if not YOOKASSA_AVAILABLE:
            raise RuntimeError("yookassa не установлен")
        import uuid
        payment = YooPayment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": f"MystVPN подписка — {plan_key}",
            "metadata": {"user_id": user_id, "plan": plan_key},
        }, uuid.uuid4())
        return {"id": payment.id, "url": payment.confirmation.confirmation_url}

    @staticmethod
    async def create_yookassa_donation(amount: float, user_id: int, return_url: str) -> dict:
        if not YOOKASSA_AVAILABLE:
            raise RuntimeError("yookassa не установлен")
        import uuid
        payment = YooPayment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_data": {"type": "bank_card"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": "MystVPN — поддержка проекта",
            "metadata": {"user_id": user_id, "type": "donation"},
        }, uuid.uuid4())
        return {"id": payment.id, "url": payment.confirmation.confirmation_url}

    @staticmethod
    async def create_yookassa_sbp_donation(amount: float, user_id: int, return_url: str) -> dict:
        if not YOOKASSA_AVAILABLE:
            raise RuntimeError("yookassa не установлен")
        import uuid
        payment = YooPayment.create({
            "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
            "capture": True,
            "payment_method_data": {"type": "sbp"},
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": "MystVPN — поддержка проекта",
            "metadata": {"user_id": user_id, "type": "donation"},
        }, uuid.uuid4())
        return {"id": payment.id, "url": payment.confirmation.confirmation_url}

    @staticmethod
    async def check_yookassa(payment_ext_id: str) -> str:
        if not YOOKASSA_AVAILABLE:
            raise RuntimeError("yookassa не установлен")
        import uuid as _uuid
        payment = YooPayment.find_one(payment_ext_id)
        if payment.status == "waiting_for_capture":
            payment = YooPayment.capture(
                payment_ext_id,
                {"amount": {"value": payment.amount.value, "currency": payment.amount.currency}},
                _uuid.uuid4(),
            )
        return payment.status
