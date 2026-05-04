import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import init_db
from handlers import user_router, support_router


def setup_logging() -> None:
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=fmt,
        handlers=[
            RotatingFileHandler("support.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


async def main() -> None:
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Initializing Support Bot...")

    await init_db()
    logger.info("DB ready: %s", config.db_path)

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    try:
        me = await bot.get_me()
        logger.info("Connected as @%s", me.username)
    except Exception as e:
        logger.error("Cannot connect to Telegram: %s", e)
        await bot.session.close()
        return

    dp = Dispatcher(storage=MemoryStorage())

    # support_router первым — фильтрует групповые сообщения раньше user_router
    dp.include_router(support_router)
    dp.include_router(user_router)

    logger.info("Support Bot is running. Group ID: %s", config.support_group_id)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except (KeyboardInterrupt, SystemExit, asyncio.CancelledError):
        logger.info("Stopped by user")
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
