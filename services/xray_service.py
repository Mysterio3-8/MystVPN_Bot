import json
import uuid
import base64
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


class XrayService:

    @staticmethod
    def _base_url() -> str:
        from config import config
        if config.xray_address:
            return config.xray_address.rstrip("/")
        return f"http://{config.xray_host}:{config.xray_port}"

    @classmethod
    async def _login(cls, session: aiohttp.ClientSession) -> bool:
        from config import config
        try:
            resp = await session.post(
                f"{cls._base_url()}/login",
                data={"username": config.xray_username, "password": config.xray_password},
                timeout=aiohttp.ClientTimeout(total=10),
            )
            data = await resp.json(content_type=None)
            return data.get("success", False)
        except Exception as e:
            logger.error(f"XRay login failed: {e}")
            return False

    @classmethod
    async def _get_inbound(cls, session: aiohttp.ClientSession, inbound_id: int) -> dict | None:
        # Используем /get/:id — эффективнее, чем получать весь список
        url = f"{cls._base_url()}/panel/api/inbounds/get/{inbound_id}"
        try:
            resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
            ct = resp.headers.get("Content-Type", "")
            if "text/html" in ct:
                logger.error("XRay: сессия не активна (редирект на логин)")
                return None
            data = await resp.json(content_type=None)
            if data.get("success"):
                return data.get("obj")
        except Exception as e:
            logger.warning(f"XRay /get/{inbound_id} failed: {e}, trying /list")

        # Fallback: получаем весь список
        url = f"{cls._base_url()}/panel/api/inbounds/list"
        try:
            resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
            data = await resp.json(content_type=None)
            if data.get("success"):
                inbounds = data.get("obj", [])
                return next((i for i in inbounds if str(i.get("id")) == str(inbound_id)), None)
        except Exception as e:
            logger.error(f"XRay /list failed: {e}")
        return None

    @classmethod
    async def test_connection(cls) -> str:
        from config import config
        base = cls._base_url()
        if not base.replace("http://", "").replace("https://", "").strip("/"):
            return "❌ XRAY_HOST / XRAY_ADDRESS не настроены в .env"
        if not config.xray_password:
            return "❌ XRAY_PASSWORD не задан в .env"
        async with aiohttp.ClientSession() as session:
            ok = await cls._login(session)
            if not ok:
                return (
                    f"❌ Ошибка авторизации в 3x-ui\n"
                    f"URL: {base}\n"
                    f"Логин: {config.xray_username}\n"
                    f"Проверь XRAY_USERNAME и XRAY_PASSWORD в .env"
                )
            inbound = await cls._get_inbound(session, config.xray_inbound_id)
            if not inbound:
                return (
                    f"✅ Авторизация OK\n"
                    f"❌ Inbound ID={config.xray_inbound_id} не найден\n"
                    f"Проверь XRAY_INBOUND_ID в .env\n"
                    f"URL панели: {base}"
                )
            protocol = inbound.get("protocol", "?")
            port = inbound.get("port", "?")
            remark = inbound.get("remark", "")
            return (
                f"✅ 3x-ui подключён!\n"
                f"URL панели: {base}\n"
                f"Inbound #{config.xray_inbound_id}: {protocol} :{port}"
                + (f" ({remark})" if remark else "")
            )

    @staticmethod
    def _build_sub_url(sub_id: str) -> str:
        """
        Строит subscription URL для клиентов v2rayTUN / Hiddify.
        Пример: https://key.yourdomain.com/sub/SUBID
        Настраивается через SUB_DOMAIN и SUB_PATH в .env
        """
        from config import config
        base = config.sub_domain.rstrip("/") if config.sub_domain else (
            config.xray_address.rstrip("/") if config.xray_address else
            f"http://{config.xray_host}:{config.xray_port}"
        )
        path = config.sub_path.strip("/")
        return f"{base}/{path}/{sub_id}"

    @classmethod
    async def create_client(cls, user_id: int, days: int) -> tuple[str | None, str | None]:
        """
        Создаёт клиента в 3x-ui.
        Возвращает (vpn_key, sub_url) — оба могут быть None при ошибке.
        sub_url — ссылка-подписка для v2rayTUN/Hiddify (автообновление).
        """
        from config import config
        if not (config.xray_address or config.xray_host) or not config.xray_password:
            logger.warning("XRay not configured — skipping key issuance")
            return None, None

        client_uuid = str(uuid.uuid4())
        # subId — уникальный ID подписки для subscription URL
        sub_id = uuid.uuid4().hex[:16]
        # Email уникален за счёт части UUID — позволяет пользователю покупать повторно
        email = f"user_{user_id}_{client_uuid[:8]}"
        expiry_ms = int((datetime.utcnow().timestamp() + days * 86400) * 1000)

        async with aiohttp.ClientSession() as session:
            if not await cls._login(session):
                logger.error("XRay login failed during create_client")
                return None, None

            client_settings = {
                "id": int(config.xray_inbound_id),
                "settings": json.dumps({
                    "clients": [{
                        "id": client_uuid,
                        "email": email,
                        "flow": "xtls-rprx-vision",
                        "limitIp": 0,
                        "totalGB": 0,
                        "expiryTime": expiry_ms,
                        "enable": True,
                        "tgId": str(user_id),
                        "subId": sub_id,
                        "comment": f"MystVPN user {user_id}",
                        "reset": 0,
                    }]
                }),
            }

            try:
                url = f"{cls._base_url()}/panel/api/inbounds/addClient"
                resp = await session.post(
                    url,
                    json=client_settings,
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                add_data = await resp.json(content_type=None)
                if not add_data.get("success"):
                    logger.error(f"XRay addClient failed: {add_data.get('msg', add_data)}")
                    return None, None
            except Exception as e:
                logger.error(f"XRay addClient error: {e}")
                return None, None

            inbound = await cls._get_inbound(session, config.xray_inbound_id)
            if not inbound:
                logger.error("XRay: inbound not found after addClient")
                return None, None

            vpn_key = cls._build_key(inbound, client_uuid, user_id)
            sub_url = cls._build_sub_url(sub_id)
            return vpn_key, sub_url

    @classmethod
    def _build_key(cls, inbound: dict, client_uuid: str, user_id: int) -> str | None:
        from config import config
        protocol = inbound.get("protocol", "")
        port = inbound.get("port", 443)
        # xray_host — публичный IP/домен VPN-сервера для ключа
        host = config.xray_host

        try:
            stream = json.loads(inbound.get("streamSettings", "{}"))
            network = stream.get("network", "tcp")
            security = stream.get("security", "none")

            ws_settings = stream.get("wsSettings", {})
            path = ws_settings.get("path", "/")
            ws_host = ws_settings.get("headers", {}).get("Host", host)

            if security == "reality":
                reality = stream.get("realitySettings", {})
                server_names = reality.get("serverNames", [])
                sni = server_names[0] if server_names else reality.get("dest", "").split(":")[0]
                short_ids = reality.get("shortIds", [""])
                short_id = short_ids[0] if short_ids else ""
                pbk = reality.get("settings", {}).get("publicKey", "")
                fp = "chrome"
            else:
                tls_settings = stream.get("tlsSettings", {})
                sni = tls_settings.get("serverName", ws_host)
                pbk = ""
                short_id = ""
                fp = "chrome"
        except Exception as e:
            logger.error(f"XRay stream parse error: {e}")
            return None

        tag = f"MystVPN-{user_id}"
        if protocol == "vless":
            if security == "reality":
                params = (
                    f"type={network}&security=reality"
                    f"&pbk={pbk}&fp={fp}&sni={sni}&sid={short_id}&flow=xtls-rprx-vision"
                )
            else:
                params = f"type={network}&security={security}&path={path}&host={ws_host}&sni={sni}&fp={fp}"
            return f"vless://{client_uuid}@{host}:{port}?{params}#{tag}"
        elif protocol == "vmess":
            vmess = {
                "v": "2", "ps": tag, "add": host, "port": str(port),
                "id": client_uuid, "aid": "0", "net": network,
                "type": "none", "host": ws_host, "path": path, "tls": security,
            }
            encoded = base64.b64encode(json.dumps(vmess).encode()).decode()
            return f"vmess://{encoded}"
        elif protocol == "trojan":
            params = f"type={network}&security={security}&path={path}&host={ws_host}&sni={sni}"
            return f"trojan://{client_uuid}@{host}:{port}?{params}#{tag}"

        logger.error(f"XRay unsupported protocol: {protocol}")
        return None

    @staticmethod
    def _extract_uuid(vpn_key: str) -> str | None:
        try:
            if vpn_key.startswith(("vless://", "trojan://")):
                return vpn_key.split("://")[1].split("@")[0]
            if vpn_key.startswith("vmess://"):
                decoded = json.loads(base64.b64decode(vpn_key[8:]).decode())
                return decoded.get("id")
        except Exception:
            pass
        return None

    @classmethod
    async def remove_client(cls, user_id: int, client_uuid: str | None = None) -> bool:
        from config import config
        if not (config.xray_address or config.xray_host) or not config.xray_password:
            return False
        async with aiohttp.ClientSession() as session:
            if not await cls._login(session):
                return False
            if not client_uuid:
                logger.warning(f"XRay: no UUID for user {user_id}, cannot delete")
                return False
            try:
                resp = await session.post(
                    f"{cls._base_url()}/panel/api/inbounds/{config.xray_inbound_id}/delClient/{client_uuid}",
                    timeout=aiohttp.ClientTimeout(total=10),
                )
                data = await resp.json(content_type=None)
                return data.get("success", False)
            except Exception as e:
                logger.error(f"XRay removeClient error: {e}")
                return False

    @classmethod
    async def reset_client(cls, user_id: int, days: int, old_key: str | None = None) -> tuple[str | None, str | None]:
        """Удаляет старый ключ и создаёт новый. Возвращает (vpn_key, sub_url)."""
        client_uuid = cls._extract_uuid(old_key) if old_key else None
        await cls.remove_client(user_id, client_uuid)
        return await cls.create_client(user_id, days)
