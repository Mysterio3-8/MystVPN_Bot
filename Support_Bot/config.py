import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str
    support_group_id: int
    admin_ids: list[int]
    db_path: str

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("SUPPORT_BOT_TOKEN", "").strip()
        if not token:
            raise RuntimeError("SUPPORT_BOT_TOKEN not set in .env")

        group_id = os.getenv("SUPPORT_GROUP_ID", "").strip()
        if not group_id:
            raise RuntimeError("SUPPORT_GROUP_ID not set in .env")

        raw_ids = os.getenv("SUPPORT_ADMIN_IDS", "")
        admin_ids = [int(x.strip()) for x in raw_ids.split(",") if x.strip().lstrip("-").isdigit()]

        return cls(
            bot_token=token,
            support_group_id=int(group_id),
            admin_ids=admin_ids,
            db_path=os.getenv("DB_PATH", "support.db"),
        )


config = Config.from_env()
