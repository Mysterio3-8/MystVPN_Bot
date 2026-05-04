"""
/status — статус VPN серверов.
Показывает пинг до 3x-ui панели, версию, uptime бота.
Повышает доверие пользователей, снижает обращения в поддержку.
"""
import time
import asyncio
import logging
from datetime import datetime, timezone
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services import XrayService

router = Router()
logger = logging.getLogger(__name__)

# Время старта бота (для uptime)
_BOT_START = datetime.now(tz=timezone.utc)


def _uptime_str() -> str:
    delta = datetime.now(tz=timezone.utc) - _BOT_START
    hours, rem = divmod(int(delta.total_seconds()), 3600)
    minutes = rem // 60
    if hours >= 24:
        days = hours // 24
        return f"{days}д {hours % 24}ч {minutes}м"
    return f"{hours}ч {minutes}м"


async def _ping_xray() -> tuple[bool, float]:
    """Пингует 3x-ui и возвращает (ok, ms)."""
    from config import config
    import aiohttp
    base = config.xray_address.rstrip("/") if config.xray_address else (
        f"http://{config.xray_host}:{config.xray_port}" if config.xray_host else None
    )
    if not base:
        return False, 0.0
    t0 = time.monotonic()
    try:
        async with aiohttp.ClientSession() as session:
            resp = await session.get(
                f"{base}/",
                timeout=aiohttp.ClientTimeout(total=5),
                allow_redirects=False,
            )
            _ = resp.status
        ms = (time.monotonic() - t0) * 1000
        return True, round(ms, 1)
    except Exception:
        ms = (time.monotonic() - t0) * 1000
        return False, round(ms, 1)


async def _build_status_text() -> str:
    ok, ms = await _ping_xray()

    if ok:
        status_icon = "🟢"
        status_text = f"Онлайн ({ms} мс)"
    else:
        status_icon = "🔴"
        status_text = "Недоступен"

    return (
        f"📡 <b>Статус серверов MystVPN</b>\n\n"
        f"{status_icon} <b>VPN сервер (Helsinki):</b> {status_text}\n\n"
        f"🤖 <b>Бот:</b> 🟢 Работает\n"
        f"⏱ <b>Uptime бота:</b> {_uptime_str()}\n\n"
        f"<i>Обновлено: {datetime.now().strftime('%H:%M:%S')}</i>"
    )


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    msg = await message.answer("⏳ Проверяю серверы...")
    text = await _build_status_text()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="status_refresh")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])
    await msg.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "menu_status")
async def status_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text("⏳ Проверяю серверы...", parse_mode="HTML")
    text = await _build_status_text()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="status_refresh")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@router.callback_query(F.data == "status_refresh")
async def status_refresh(callback: CallbackQuery) -> None:
    await callback.answer("🔄 Обновляю...")
    text = await _build_status_text()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="status_refresh")],
        [InlineKeyboardButton(text="◀️ В меню", callback_data="back_to_menu")],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
