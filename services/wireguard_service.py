import logging
import aiohttp
from config import config

logger = logging.getLogger(__name__)


class WireGuardService:
    _session: aiohttp.ClientSession | None = None

    @classmethod
    def _get_session(cls) -> aiohttp.ClientSession:
        if cls._session is None or cls._session.closed:
            cls._session = aiohttp.ClientSession(cookie_jar=aiohttp.CookieJar())
        return cls._session

    @classmethod
    def _enabled(cls) -> bool:
        return bool(config.wg_api_url and config.wg_api_password)

    @classmethod
    async def _auth(cls) -> bool:
        if not cls._enabled():
            return False
        try:
            session = cls._get_session()
            async with session.post(
                f"{config.wg_api_url}/api/session",
                json={"password": config.wg_api_password},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return resp.status in (200, 204)
        except Exception as e:
            logger.warning(f"WireGuard auth failed: {e}")
            return False

    @classmethod
    async def create_peer(cls, user_id: int) -> str | None:
        """Create a WireGuard peer. Returns peer ID or None if WG unavailable."""
        if not await cls._auth():
            return None
        try:
            session = cls._get_session()
            async with session.post(
                f"{config.wg_api_url}/api/wireguard/client",
                json={"name": f"MystVPN-{user_id}"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 201:
                    data = await resp.json()
                    return data.get("id")
                logger.warning(f"WireGuard create_peer status={resp.status} user={user_id}")
        except Exception as e:
            logger.warning(f"WireGuard create_peer error user={user_id}: {e}")
        return None

    @classmethod
    async def get_config(cls, peer_id: str) -> str | None:
        """Get WireGuard .conf file content."""
        if not await cls._auth():
            return None
        try:
            session = cls._get_session()
            async with session.get(
                f"{config.wg_api_url}/api/wireguard/client/{peer_id}/configuration",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.text()
        except Exception as e:
            logger.warning(f"WireGuard get_config error peer={peer_id}: {e}")
        return None

    @classmethod
    async def delete_peer(cls, peer_id: str) -> None:
        """Delete a WireGuard peer. Ignores errors — best-effort cleanup."""
        if not await cls._auth():
            return
        try:
            session = cls._get_session()
            async with session.delete(
                f"{config.wg_api_url}/api/wireguard/client/{peer_id}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status not in (200, 204):
                    logger.warning(f"WireGuard delete_peer status={resp.status} peer={peer_id}")
        except Exception as e:
            logger.warning(f"WireGuard delete_peer error peer={peer_id}: {e}")
