"""
Миграция БД — добавляет новые колонки для:
  - Пробного периода (trial)
  - Реферальной программы
  - Subscription URL (ссылка-подписка)
  - Уведомлений об истечении

Запуск: python migrate.py
"""
import asyncio
import logging
from sqlalchemy import text
from database.db import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MIGRATIONS = [
    # ── Таблица users ───────────────────────────────────────────────────────
    (
        "users.referred_by",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS referred_by BIGINT DEFAULT NULL",
    ),
    (
        "users.trial_used",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_used BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "users.extra_days",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS extra_days INTEGER NOT NULL DEFAULT 0",
    ),
    # ── Таблица subscriptions ───────────────────────────────────────────────
    (
        "subscriptions.sub_url",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS sub_url VARCHAR(512) DEFAULT NULL",
    ),
    (
        "subscriptions.is_trial",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_trial BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "subscriptions.notified_5d",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS notified_5d BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "subscriptions.notified_1d",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS notified_1d BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "subscriptions.notified_0d",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS notified_0d BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    # ── Ротация ключей ──────────────────────────────────────────────────────
    (
        "subscriptions.new_vpn_key",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS new_vpn_key VARCHAR(2048) DEFAULT NULL",
    ),
    (
        "subscriptions.new_sub_url",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS new_sub_url VARCHAR(512) DEFAULT NULL",
    ),
    (
        "subscriptions.key_rotation_deadline",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS key_rotation_deadline TIMESTAMP DEFAULT NULL",
    ),
    # ── WireGuard ───────────────────────────────────────────────────────────
    (
        "subscriptions.wg_peer_id",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS wg_peer_id VARCHAR(100) DEFAULT NULL",
    ),
    # ── Gift security ───────────────────────────────────────────────────────
    (
        "gift_codes.is_paid",
        "ALTER TABLE gift_codes ADD COLUMN IF NOT EXISTS is_paid BOOLEAN NOT NULL DEFAULT FALSE",
    ),
    (
        "gift_codes.payment_ext_id",
        "ALTER TABLE gift_codes ADD COLUMN IF NOT EXISTS payment_ext_id VARCHAR(128) DEFAULT NULL",
    ),
    # ── Key lifecycle ───────────────────────────────────────────────────────
    (
        "subscriptions.key_disabled_at",
        "ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS key_disabled_at TIMESTAMP DEFAULT NULL",
    ),
]


async def run_migrations() -> None:
    async with engine.begin() as conn:
        for name, sql in MIGRATIONS:
            try:
                await conn.execute(text(sql))
                logger.info(f"✅ {name}")
            except Exception as e:
                logger.error(f"❌ {name}: {e}")
    logger.info("🎉 Миграция завершена!")


if __name__ == "__main__":
    asyncio.run(run_migrations())
