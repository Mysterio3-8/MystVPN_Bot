"""
Сброс всех VPN ключей у активных пользователей.
Запускать на сервере: python /tmp/reset_all_keys.py
"""
import asyncio
import sys
sys.path.insert(0, "/app")

from dotenv import load_dotenv
load_dotenv("/app/.env")

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone
import aiohttp
import os

from models.subscription import Subscription
from models.user import User
from services.xray_service import XrayService

DATABASE_URL = os.getenv("DATABASE_URL", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")


async def send_message(session: aiohttp.ClientSession, chat_id: int, text: str):
    try:
        await session.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
            timeout=aiohttp.ClientTimeout(total=10),
        )
    except Exception as e:
        print(f"  Telegram error for {chat_id}: {e}")


async def main():
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        result = await db.execute(
            select(Subscription, User)
            .join(User, Subscription.user_id == User.user_id)
            .where(Subscription.status == "active")
            .where(Subscription.end_date > datetime.utcnow())
            .where(Subscription.vpn_key.isnot(None))
        )
        rows = result.all()

    print(f"Активных подписок с ключами: {len(rows)}")
    if not rows:
        print("Нечего обновлять.")
        return

    ok, fail = 0, 0
    async with aiohttp.ClientSession() as http:
        for sub, user in rows:
            days_left = max(1, (sub.end_date - datetime.utcnow()).days)
            print(f"\n[user {user.user_id}] sub#{sub.id} — осталось {days_left} дней")
            print(f"  Старый ключ: {(sub.vpn_key or '')[:60]}...")

            new_key, new_sub_url = await XrayService.reset_client(
                user.user_id, days_left, sub.vpn_key
            )

            if not new_key:
                print(f"  FAIL: ключ не создан")
                fail += 1
                continue

            print(f"  Новый ключ:  {new_key[:60]}...")
            print(f"  Sub URL: {new_sub_url}")

            async with async_session() as db:
                await db.execute(
                    update(Subscription)
                    .where(Subscription.id == sub.id)
                    .values(vpn_key=new_key, sub_url=new_sub_url)
                )
                await db.commit()

            # Уведомление пользователю
            lang = user.language or "ru"
            if lang == "ru":
                msg = (
                    "🔐 <b>Ваш VPN обновлён</b>\n\n"
                    "Мы улучшили инфраструктуру — старая ссылка больше не работает.\n\n"
                    f"<b>Твоя новая ссылка-подписка:</b>\n<code>{new_sub_url}</code>\n\n"
                    "Открой Hiddify / v2rayTUN → «Добавить подписку» → вставь ссылку.\n\n"
                    "По вопросам: @Myst_support"
                )
            else:
                msg = (
                    "🔐 <b>Your VPN has been updated</b>\n\n"
                    "We upgraded our infrastructure — your old link no longer works.\n\n"
                    f"<b>Your new subscription link:</b>\n<code>{new_sub_url}</code>\n\n"
                    "Open Hiddify / v2rayTUN → \"Add subscription\" → paste the link.\n\n"
                    "Support: @Myst_support"
                )

            await send_message(http, user.user_id, msg)
            print(f"  Уведомление отправлено → @{user.username or user.user_id}")
            ok += 1
            await asyncio.sleep(0.3)

    print(f"\n=== Готово: обновлено {ok}, ошибок {fail} ===")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
