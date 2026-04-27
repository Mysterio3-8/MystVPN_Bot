import json
import logging
from aiohttp import web
from database import AsyncSessionLocal
from services import PaymentService, SubscriptionService, XrayService, GiftService, fmt_key
from services.donation_service import DonationService
from config import config, PLANS

logger = logging.getLogger(__name__)


async def _handle_donation_succeeded(bot, user_id: int, amount: float, ext_id: str) -> None:
    """Обрабатывает успешный донат: записывает в donations, уведомляет пользователя."""
    bot_user = None
    if bot:
        try:
            bot_user = await bot.get_chat(user_id)
        except Exception:
            pass

    username = getattr(bot_user, "username", None)
    first_name = getattr(bot_user, "first_name", None)

    async with AsyncSessionLocal() as session:
        await DonationService.record_rub(session, user_id, username, first_name, amount)

    if bot:
        try:
            await bot.send_message(
                user_id,
                f"❤️ <b>Спасибо за поддержку!</b>\n\n"
                f"Твой донат <b>{amount:.0f} ₽</b> получен.\n"
                f"Ты помогаешь нам развивать сервис!",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Cannot notify donor {user_id}: {e}")

    logger.info(f"Webhook: donation {ext_id} recorded for user {user_id}, amount={amount:.2f}")


async def handle_yookassa(request: web.Request) -> web.Response:
    try:
        body = await request.read()
        data = json.loads(body)
    except Exception:
        return web.Response(status=400)

    event_type = data.get("event", "")
    if event_type not in ("payment.succeeded", "payment.canceled"):
        return web.Response(status=200)

    payment_obj = data.get("object", {})
    ext_id = payment_obj.get("id")
    if not ext_id:
        return web.Response(status=400)

    if event_type == "payment.canceled":
        logger.info(f"Payment {ext_id} canceled by YooKassa")
        return web.Response(status=200)

    # Verify via API (prevents spoofed webhooks)
    try:
        status = await PaymentService.check_yookassa(ext_id)
    except Exception as e:
        logger.error(f"YooKassa API verify failed for {ext_id}: {e}")
        return web.Response(status=500)

    if status != "succeeded":
        logger.info(f"Payment {ext_id} status={status}, skipping")
        return web.Response(status=200)

    sub_id = None
    user_id = None
    plan_key = None
    amount = 0.0

    async with AsyncSessionLocal() as session:
        payment = await PaymentService.get_by_ext_id(session, ext_id)
        if not payment:
            logger.warning(f"Payment {ext_id} not found in DB")
            return web.Response(status=200)
        if payment.status == "completed":
            logger.info(f"Payment {ext_id} already completed, skipping")
            return web.Response(status=200)

        await PaymentService.complete(session, payment.id)

        sub_id = payment.subscription_id
        user_id = payment.user_id
        plan_key = payment.plan
        amount = payment.amount

        # Активируем подписку только для реальных планов
        if sub_id and plan_key != "donation":
            await SubscriptionService.activate(session, sub_id)

    bot = request.app.get("bot")

    # Донат
    if plan_key == "donation":
        await _handle_donation_succeeded(bot, user_id, amount, ext_id)
        return web.Response(status=200)

    # Подарок — помечаем оплаченным и отправляем ссылку покупателю
    if plan_key and payment and getattr(payment, 'payment_method', '') == "yookassa_gift":
        async with AsyncSessionLocal() as session:
            gift = await GiftService.get_by_payment_ext_id(session, ext_id)
            if gift and not gift.is_paid:
                gift.is_paid = True
                await session.commit()
            if gift and bot:
                from config import config as _cfg
                gift_link = f"https://t.me/{_cfg.bot_username}?start=gift_{gift.code}"
                try:
                    await bot.send_message(
                        user_id,
                        f"✅ <b>Оплата подарка получена!</b>\n\n"
                        f"🎁 Вот ссылка — отправь другу:\n\n"
                        f"<code>{gift_link}</code>\n\n"
                        f"Друг перейдёт и получит VPN автоматически.",
                        parse_mode="HTML",
                    )
                except Exception as e:
                    logger.warning(f"Cannot send gift link to {user_id}: {e}")
        logger.info(f"Webhook: gift payment {ext_id} confirmed for user {user_id}")
        return web.Response(status=200)

    # Обычная подписка — создаём ключ
    days = PLANS.get(plan_key or "", {}).get("days", 30)
    vpn_key, sub_url = await XrayService.create_client(user_id, days)
    if vpn_key and sub_id:
        async with AsyncSessionLocal() as session:
            await SubscriptionService.save_key(session, sub_id, vpn_key, sub_url)

    if bot and user_id:
        try:
            await bot.send_message(
                user_id,
                f"✅ <b>Оплата получена!</b>\n"
                f"Подписка активирована."
                f"{fmt_key(vpn_key, sub_url)}",
                parse_mode="HTML",
            )
        except Exception as e:
            logger.warning(f"Cannot notify user {user_id}: {e}")

    logger.info(f"Webhook: payment {ext_id} activated for user {user_id}")
    return web.Response(status=200)


async def handle_health(request: web.Request) -> web.Response:
    return web.Response(text="ok")


def create_webhook_app(bot=None) -> web.Application:
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook/yookassa", handle_yookassa)
    app.router.add_post("/webhook", handle_yookassa)  # fallback
    app.router.add_get("/health", handle_health)
    return app
