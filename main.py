import asyncio
import logging
from logging.handlers import RotatingFileHandler
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from config import config
from database.db import init_db
from handlers import (
    start_router,
    cabinet_router,
    subscriptions_router,
    payments_router,
    admin_router,
    languages_router,
    gift_router,
    donate_router,
    referral_router,
)
from services import run_notification_loop
from services.notification_service import run_inbound_watchdog
from webhook_server import create_webhook_app


def setup_logging() -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    handlers: list[logging.Handler] = [
        RotatingFileHandler("bot.log", maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"),
        logging.StreamHandler(),
    ]
    logging.basicConfig(level=logging.INFO, format=fmt, handlers=handlers)


logger = logging.getLogger(__name__)


def create_bot() -> Bot:
    default = DefaultBotProperties(parse_mode=ParseMode.HTML)
    if config.has_proxy:
        proxy_url = config.proxy_url
        logger.info(f"🔒 Using proxy: {proxy_url.split('@')[-1]}")
        try:
            from aiogram.client.session.aiohttp import AiohttpSession
            session = AiohttpSession(proxy=proxy_url)
            return Bot(token=config.bot_token, session=session, default=default)
        except Exception as e:
            logger.warning(f"⚠️ Proxy setup failed: {e} — fallback без прокси")
    logger.info("🔓 Creating bot without proxy")
    return Bot(token=config.bot_token, default=default)


async def test_connection(bot: Bot, timeout: int = 10) -> bool:
    try:
        me = await asyncio.wait_for(bot.get_me(), timeout=timeout)
        logger.info(f"✅ Connected to Telegram as @{me.username}")
        return True
    except Exception as e:
        logger.error(f"❌ Connection to Telegram failed: {e}")
        return False


async def run_webhook_server(app: web.Application, port: int) -> None:
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Webhook server listening on port {port}")
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def main() -> None:
    setup_logging()
    logger.info("🚀 Initializing MystVPN Bot...")

    await init_db()
    logger.info("✅ База данных инициализирована")

    try:
        import redis.asyncio as aioredis
        test_redis = aioredis.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        await asyncio.wait_for(test_redis.ping(), timeout=3)
        await test_redis.aclose()
        storage = RedisStorage.from_url(f"redis://{config.redis_host}:{config.redis_port}")
        logger.info("✅ Redis подключён")
    except Exception:
        from aiogram.fsm.storage.memory import MemoryStorage
        storage = MemoryStorage()
        logger.warning("⚠️ Redis недоступен — используется MemoryStorage")

    bot = create_bot()

    if not await test_connection(bot):
        logger.error("❌ Не удалось подключиться к Telegram. Проверьте прокси/токен.")
        await bot.session.close()
        return

    dp = Dispatcher(storage=storage)
    dp.include_router(start_router)
    dp.include_router(languages_router)
    dp.include_router(cabinet_router)
    dp.include_router(subscriptions_router)
    dp.include_router(gift_router)
    dp.include_router(donate_router)
    dp.include_router(payments_router)
    dp.include_router(admin_router)
    dp.include_router(referral_router)

    webhook_app = create_webhook_app(bot=bot)

    logger.info("🚀 Бот запускается (polling + webhook server + notifications)...")
    try:
        await asyncio.gather(
            dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
            run_webhook_server(webhook_app, config.webhook_port),
            run_notification_loop(bot),
            run_inbound_watchdog(bot),
        )
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("🛑 Остановка по сигналу пользователя")
    finally:
        await bot.session.close()
        logger.info("👋 Бот остановлен")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("👋 Выход")
