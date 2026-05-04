import aiosqlite
from config import config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS tickets (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    username    TEXT,
    status      TEXT    NOT NULL DEFAULT 'open',
    created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    closed_at   TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id    INTEGER NOT NULL,
    from_support INTEGER NOT NULL DEFAULT 0,
    text         TEXT    NOT NULL,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

-- Maps a message_id in the support group → ticket + user, so replies route correctly.
CREATE TABLE IF NOT EXISTS msg_routing (
    support_msg_id INTEGER PRIMARY KEY,
    ticket_id      INTEGER NOT NULL,
    user_id        INTEGER NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);
"""


async def init_db() -> None:
    async with aiosqlite.connect(config.db_path) as db:
        await db.executescript(_SCHEMA)
        await db.commit()


async def get_open_ticket(user_id: int) -> dict | None:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE user_id = ? AND status = 'open' ORDER BY id DESC LIMIT 1",
            (user_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def create_ticket(user_id: int, username: str | None) -> int:
    async with aiosqlite.connect(config.db_path) as db:
        cur = await db.execute(
            "INSERT INTO tickets (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        await db.commit()
        return cur.lastrowid


async def close_ticket(ticket_id: int) -> None:
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            "UPDATE tickets SET status = 'closed', closed_at = datetime('now') WHERE id = ?",
            (ticket_id,),
        )
        await db.commit()


async def add_message(ticket_id: int, text: str, from_support: bool = False) -> None:
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            "INSERT INTO messages (ticket_id, from_support, text) VALUES (?, ?, ?)",
            (ticket_id, int(from_support), text),
        )
        await db.commit()


async def register_routing(support_msg_id: int, ticket_id: int, user_id: int) -> None:
    async with aiosqlite.connect(config.db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO msg_routing (support_msg_id, ticket_id, user_id) VALUES (?, ?, ?)",
            (support_msg_id, ticket_id, user_id),
        )
        await db.commit()


async def get_routing(support_msg_id: int) -> dict | None:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM msg_routing WHERE support_msg_id = ?",
            (support_msg_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_open_tickets(limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(config.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM tickets WHERE status = 'open' ORDER BY id DESC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]
