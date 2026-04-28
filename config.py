from dataclasses import dataclass, field
from os import getenv
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    bot_token: str = field(default_factory=lambda: getenv("BOT_TOKEN", ""))
    bot_username: str = field(default_factory=lambda: getenv("BOT_USERNAME", "MystVPN_bot"))

    database_url: str = field(default_factory=lambda: getenv("DATABASE_URL", ""))
    redis_host: str = field(default_factory=lambda: getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(getenv("REDIS_PORT", "6379")))

    yookassa_account_id: str = field(default_factory=lambda: getenv("YOOKASSA_ACCOUNT_ID", ""))
    yookassa_secret_key: str = field(default_factory=lambda: getenv("YOOKASSA_SECRET_KEY", ""))

    webhook_url: str = field(default_factory=lambda: getenv("WEBHOOK_URL", ""))
    webhook_secret: str = field(default_factory=lambda: getenv("WEBHOOK_SECRET", ""))

    proxy_host: str = field(default_factory=lambda: getenv("PROXY_HOST", ""))
    proxy_port: int = field(default_factory=lambda: int(getenv("PROXY_PORT", "0") or 0))
    proxy_login: str = field(default_factory=lambda: getenv("PROXY_LOGIN", ""))
    proxy_pass: str = field(default_factory=lambda: getenv("PROXY_PASS", ""))

    admin_ids: list[int] = field(default_factory=lambda: [
        int(i) for i in getenv("ADMIN_IDS", "").split(",") if i.strip().isdigit()
    ])

    xray_host: str = field(default_factory=lambda: getenv("XRAY_HOST", ""))
    xray_port: int = field(default_factory=lambda: int(getenv("XRAY_PORT", "54321")))
    xray_username: str = field(default_factory=lambda: getenv("XRAY_USERNAME", "admin"))
    xray_password: str = field(default_factory=lambda: getenv("XRAY_PASSWORD", ""))
    xray_inbound_id: int = field(default_factory=lambda: int(getenv("XRAY_INBOUND_ID", "1")))
    xray_address: str = field(default_factory=lambda: getenv("XRAY_ADDRESS", "") or getenv("XRAY_ADDRES", ""))
    webhook_port: int = field(default_factory=lambda: int(getenv("WEBHOOK_PORT", "8090")))
    # Reality inbound settings — for auto-recreate watchdog
    reality_private_key: str = field(default_factory=lambda: getenv("REALITY_PRIVATE_KEY", ""))
    reality_public_key: str = field(default_factory=lambda: getenv("REALITY_PUBLIC_KEY", ""))
    reality_short_id: str = field(default_factory=lambda: getenv("REALITY_SHORT_ID", ""))
    reality_dest: str = field(default_factory=lambda: getenv("REALITY_DEST", "www.microsoft.com:443"))
    reality_sni: str = field(default_factory=lambda: getenv("REALITY_SNI", "www.microsoft.com"))
    sub_domain: str = field(default_factory=lambda: getenv("SUB_DOMAIN", ""))
    # Путь к endpoint подписки. Для 3x-ui: /sub/  Для Remnawave: /rem/sub/
    sub_path: str = field(default_factory=lambda: getenv("SUB_PATH", "/sub/"))

    # ── WireGuard (wg-easy) ──────────────────────────────────────────────────
    wg_api_url: str = field(default_factory=lambda: getenv("WG_API_URL", "http://wg-easy:51821"))
    wg_api_password: str = field(default_factory=lambda: getenv("WG_API_PASSWORD", ""))

    @property
    def proxy_url(self) -> str:
        if not self.proxy_host or not self.proxy_port:
            return ""
        if self.proxy_login and self.proxy_pass:
            return f"socks5://{self.proxy_login}:{self.proxy_pass}@{self.proxy_host}:{self.proxy_port}"
        return f"socks5://{self.proxy_host}:{self.proxy_port}"

    @property
    def has_proxy(self) -> bool:
        return bool(self.proxy_host and self.proxy_port)


config = Config()

PLANS = {
    "1_month": {"period": "1 месяц", "price": 219.0, "days": 30},
    "3_months": {"period": "3 месяца", "price": 549.0, "days": 90},
    "6_months": {"period": "6 месяцев", "price": 999.0, "days": 180},
    "1_year": {"period": "1 год", "price": 1799.0, "days": 365},
}

# Цены в Telegram Stars (⭐). Курс ~1.5 RUB/Star. Можно менять.
STARS_PRICES = {
    "1_month": 150,
    "3_months": 370,
    "6_months": 670,
    "1_year": 1200,
}

SUPPORTED_LANGUAGES = ["ru", "en", "fr", "es", "pt", "tr", "ar", "fa", "uk", "id", "zh", "ja", "ko", "de", "vi", "ms", "hi"]
DEFAULT_LANGUAGE = "ru"

# ── Пробный период ──────────────────────────────────────────────────────────
TRIAL_DAYS = 3                    # длина пробного периода

# ── Реферальная программа ───────────────────────────────────────────────────
REFERRAL_BONUS_DAYS = 7           # дней за каждого приведённого друга
REFERRAL_MILESTONE = 10           # рефералов для крупного бонуса
REFERRAL_MILESTONE_DAYS = 30      # дней за достижение milestone

# ── Уведомления об истечении ─────────────────────────────────────────────────
EXPIRY_NOTIFY_DAYS = [5, 1, 0]    # за сколько дней до конца слать уведомления
EXPIRY_DISCOUNT_PERCENT = 15      # скидка в день истечения (промокод авто)

# ── Subscription URL ────────────────────────────────────────────────────────
# Путь к endpoint подписки в 3x-ui: {XRAY_BASE_URL}/sub/{subId}
# Переопределяется через SUB_DOMAIN в .env (если используешь отдельный домен)
SUB_DOMAIN: str = ""              # заполняется из .env при необходимости
