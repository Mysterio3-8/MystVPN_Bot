import asyncio
import json
import uuid
import base64
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_DELAY = 2.0

# Динамический ID inbound — обновляется watchdog'ом если inbound был пересоздан
_active_inbound_id: int | None = None


class XrayService:

    @staticmethod
    def _base_url() -> str:
        from config import config
        if config.xray_address:
            return config.xray_address.rstrip("/")
        return f"http://{config.xray_host}:{config.xray_port}"

    @staticmethod
    def get_inbound_id() -> int:
        from config import config
        return _active_inbound_id if _active_inbound_id is not None else config.xray_inbound_id

    @staticmethod
    def _session() -> aiohttp.ClientSession:
        import ssl as _ssl
        ctx = _ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ctx)
        # unsafe=True позволяет хранить куки для IP-адресов (не только доменов)
        jar = aiohttp.CookieJar(unsafe=True)
        return aiohttp.ClientSession(connector=connector, cookie_jar=jar)

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
        base = cls._base_url()

        # Пробуем все известные пути 3x-ui (разные версии)
        list_urls = [
            f"{base}/panel/api/inbounds/list",
            f"{base}/xui/API/inbounds",
            f"{base}/api/inbounds",
        ]
        get_urls = [
            f"{base}/panel/api/inbounds/get/{inbound_id}",
            f"{base}/xui/API/inbounds/{inbound_id}",
        ]

        # Сначала пробуем /get/:id
        for url in get_urls:
            try:
                resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    continue
                data = await resp.json(content_type=None)
                if data.get("success") and data.get("obj"):
                    logger.info(f"XRay: нашли inbound через {url}")
                    return data.get("obj")
            except Exception as e:
                logger.warning(f"XRay GET {url} failed: {e}")

        # Потом пробуем /list и ищем нужный ID
        for url in list_urls:
            try:
                resp = await session.get(url, timeout=aiohttp.ClientTimeout(total=10))
                ct = resp.headers.get("Content-Type", "")
                if "text/html" in ct:
                    continue
                data = await resp.json(content_type=None)
                if data.get("success"):
                    inbounds = data.get("obj", [])
                    logger.info(f"XRay: получили {len(inbounds)} inbound(s) через {url}")
                    found = next((i for i in inbounds if str(i.get("id")) == str(inbound_id)), None)
                    if found:
                        return found
                    # Если ID не найден — логируем все доступные
                    ids = [i.get("id") for i in inbounds]
                    logger.warning(f"XRay: inbound {inbound_id} не найден. Доступные ID: {ids}")
            except Exception as e:
                logger.warning(f"XRay LIST {url} failed: {e}")

        return None

    @staticmethod
    def _client_expiry_ms(end_date: datetime) -> int:
        return int(end_date.timestamp() * 1000)

    @staticmethod
    def _find_client(inbound: dict, client_uuid: str) -> dict | None:
        try:
            settings = json.loads(inbound.get("settings", "{}"))
            for client in settings.get("clients", []):
                if client.get("id") == client_uuid:
                    return client
        except Exception as e:
            logger.warning(f"XRay client parse error: {e}")
        return None

    @classmethod
    async def _update_client_expiry_on_inbound(
        cls,
        session: aiohttp.ClientSession,
        inbound_id: int,
        client_uuid: str,
        user_id: int,
        end_date: datetime,
    ) -> bool:
        inbound = await cls._get_inbound(session, inbound_id)
        if not inbound:
            return False

        client = cls._find_client(inbound, client_uuid)
        if not client:
            return False

        client["expiryTime"] = cls._client_expiry_ms(end_date)
        client["enable"] = end_date > datetime.utcnow()
        client.setdefault("tgId", str(user_id))
        client.setdefault("limitIp", 0)
        client.setdefault("totalGB", 0)
        client.setdefault("reset", 0)

        payload = {
            "id": int(inbound_id),
            "settings": json.dumps({"clients": [client]}),
        }
        urls = [
            f"{cls._base_url()}/panel/api/inbounds/updateClient/{client_uuid}",
            f"{cls._base_url()}/xui/API/inbounds/updateClient/{client_uuid}",
        ]
        for url in urls:
            try:
                resp = await session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15))
                data = await resp.json(content_type=None)
                if data.get("success"):
                    return True
                logger.warning(f"XRay updateClient failed via {url}: {data.get('msg', data)}")
            except Exception as e:
                logger.warning(f"XRay updateClient {url} failed: {e}")
        return False

    @classmethod
    async def test_connection(cls) -> str:
        from config import config
        base = cls._base_url()
        if not base.replace("http://", "").replace("https://", "").strip("/"):
            return "❌ XRAY_HOST / XRAY_ADDRESS не настроены в .env"
        if not config.xray_password:
            return "❌ XRAY_PASSWORD не задан в .env"
        async with cls._session() as session:
            ok = await cls._login(session)
            if not ok:
                return (
                    f"❌ Ошибка авторизации в 3x-ui\n"
                    f"URL: {base}\n"
                    f"Логин: {config.xray_username}\n"
                    f"Проверь XRAY_USERNAME и XRAY_PASSWORD в .env"
                )
            inbound = await cls._get_inbound(session, cls.get_inbound_id())
            if not inbound:
                # Пробуем получить список всех inbound'ов для подсказки
                hint = ""
                try:
                    for url in [f"{base}/panel/api/inbounds/list", f"{base}/xui/API/inbounds"]:
                        r = await session.get(url, timeout=aiohttp.ClientTimeout(total=5))
                        d = await r.json(content_type=None)
                        if d.get("success") and d.get("obj"):
                            ids = [f"#{i.get('id')} {i.get('remark','')}" for i in d["obj"]]
                            hint = f"\nДоступные inbound'ы: {', '.join(ids)}"
                            break
                except Exception:
                    pass
                return (
                    f"✅ Авторизация OK\n"
                    f"❌ Inbound ID={cls.get_inbound_id()} не найден{hint}\n"
                    f"Обнови XRAY_INBOUND_ID в .env\n"
                    f"URL панели: {base}"
                )
            protocol = inbound.get("protocol", "?")
            port = inbound.get("port", "?")
            remark = inbound.get("remark", "")
            return (
                f"✅ 3x-ui подключён!\n"
                f"URL панели: {base}\n"
                f"Inbound #{cls.get_inbound_id()}: {protocol} :{port}"
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
    async def _create_client_once(cls, user_id: int, days: int) -> tuple[str | None, str | None]:
        """Одна попытка создать клиента в 3x-ui."""
        from config import config

        client_uuid = str(uuid.uuid4())
        sub_id = uuid.uuid4().hex[:16]
        email = ""  # пустой — 3x-ui не добавляет суффикс к имени сервера
        expiry_ms = int((datetime.utcnow().timestamp() + days * 86400) * 1000)

        async with cls._session() as session:
            if not await cls._login(session):
                raise RuntimeError("XRay login failed")

            add_url = f"{cls._base_url()}/panel/api/inbounds/addClient"

            # Основной инбаунд (VLESS Reality)
            reality_settings = {
                "id": int(cls.get_inbound_id()),
                "settings": json.dumps({"clients": [{
                    "id": client_uuid, "email": email,
                    "flow": "xtls-rprx-vision",
                    "limitIp": 0, "totalGB": 0,
                    "expiryTime": expiry_ms, "enable": True,
                    "tgId": str(user_id), "subId": sub_id,
                    "comment": f"MystVPN user {user_id}", "reset": 0,
                }]}),
            }
            resp = await session.post(add_url, json=reality_settings, timeout=aiohttp.ClientTimeout(total=15))
            add_data = await resp.json(content_type=None)
            if not add_data.get("success"):
                raise RuntimeError(f"addClient failed: {add_data.get('msg', add_data)}")

            # Резервный инбаунд XHTTP (тот же subId → оба протокола в одной подписке)
            xhttp_id = config.xray_xhttp_inbound_id
            if xhttp_id:
                try:
                    xhttp_settings = {
                        "id": int(xhttp_id),
                        "settings": json.dumps({"clients": [{
                            "id": client_uuid, "email": email,
                            "flow": "",
                            "limitIp": 0, "totalGB": 0,
                            "expiryTime": expiry_ms, "enable": True,
                            "tgId": str(user_id), "subId": sub_id,
                            "comment": f"MystVPN user {user_id}", "reset": 0,
                        }]}),
                    }
                    await session.post(add_url, json=xhttp_settings, timeout=aiohttp.ClientTimeout(total=10))
                except Exception as e:
                    logger.warning(f"XRay: XHTTP client add failed (non-critical): {e}")

            inbound = await cls._get_inbound(session, cls.get_inbound_id())
            if not inbound:
                raise RuntimeError("inbound not found after addClient")

            vpn_key = cls._build_key(inbound, client_uuid, user_id)
            sub_url = cls._build_sub_url(sub_id)
            return vpn_key, sub_url

    @classmethod
    async def create_client(cls, user_id: int, days: int) -> tuple[str | None, str | None]:
        """
        Создаёт клиента в 3x-ui с автоматическим retry.
        Возвращает (vpn_key, sub_url) — гарантированно после 3 попыток.
        """
        from config import config
        if not (config.xray_address or config.xray_host) or not config.xray_password:
            logger.warning("XRay not configured — skipping key issuance")
            return None, None

        last_error: Exception | None = None
        for attempt in range(1, _RETRY_ATTEMPTS + 1):
            try:
                vpn_key, sub_url = await cls._create_client_once(user_id, days)
                if vpn_key:
                    if attempt > 1:
                        logger.info(f"XRay: ключ создан с попытки {attempt} для user {user_id}")
                    return vpn_key, sub_url
            except Exception as e:
                last_error = e
                logger.warning(f"XRay create_client attempt {attempt}/{_RETRY_ATTEMPTS} failed: {e}")
                if attempt < _RETRY_ATTEMPTS:
                    await asyncio.sleep(_RETRY_DELAY)

        logger.error(f"XRay: все {_RETRY_ATTEMPTS} попытки создать ключ провалились для user {user_id}. Последняя ошибка: {last_error}")
        return None, None

    @classmethod
    async def sync_client_expiry(cls, user_id: int, vpn_key: str | None, end_date: datetime) -> bool:
        """Обновляет срок существующего клиента в 3x-ui без перевыдачи ключа."""
        from config import config

        client_uuid = cls._extract_uuid(vpn_key or "")
        if not client_uuid:
            return False
        if not (config.xray_address or config.xray_host) or not config.xray_password:
            return False

        async with cls._session() as session:
            if not await cls._login(session):
                return False

            ok = await cls._update_client_expiry_on_inbound(
                session, cls.get_inbound_id(), client_uuid, user_id, end_date
            )
            if config.xray_xhttp_inbound_id:
                xhttp_ok = await cls._update_client_expiry_on_inbound(
                    session, int(config.xray_xhttp_inbound_id), client_uuid, user_id, end_date
                )
                ok = ok or xhttp_ok
            return ok

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
                fp = reality.get("settings", {}).get("fingerprint", "chrome")
                spx = reality.get("settings", {}).get("spiderX", "/")
            else:
                tls_settings = stream.get("tlsSettings", {})
                sni = tls_settings.get("serverName", ws_host)
                pbk = ""
                short_id = ""
                fp = "chrome"
        except Exception as e:
            logger.error(f"XRay stream parse error: {e}")
            return None

        tag = f"MystVPN"
        if protocol == "vless":
            if security == "reality":
                import urllib.parse
                params = (
                    f"type={network}&security=reality"
                    f"&pbk={pbk}&fp={fp}&sni={sni}&sid={short_id}"
                    f"&flow=xtls-rprx-vision&spx={urllib.parse.quote(spx, safe='')}"
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
        async with cls._session() as session:
            if not await cls._login(session):
                return False
            if not client_uuid:
                logger.warning(f"XRay: no UUID for user {user_id}, cannot delete")
                return False
            removed = False
            inbound_ids = [cls.get_inbound_id()]
            if config.xray_xhttp_inbound_id:
                inbound_ids.append(int(config.xray_xhttp_inbound_id))
            for inbound_id in inbound_ids:
                for url in [
                    f"{cls._base_url()}/panel/api/inbounds/{inbound_id}/delClient/{client_uuid}",
                    f"{cls._base_url()}/xui/API/inbounds/{inbound_id}/delClient/{client_uuid}",
                ]:
                    try:
                        resp = await session.post(url, timeout=aiohttp.ClientTimeout(total=10))
                        data = await resp.json(content_type=None)
                        removed = removed or data.get("success", False)
                        if data.get("success"):
                            break
                    except Exception as e:
                        logger.warning(f"XRay removeClient {url} error: {e}")
            return removed

    @classmethod
    async def disable_client(cls, user_id: int, vpn_key: str) -> bool:
        """
        Дисейблит клиента в 3x-ui (enable=False, expiryTime=1ms).
        Используется при grace period — ключ отключён, но ещё не удалён.
        """
        from config import config
        client_uuid = cls._extract_uuid(vpn_key or "")
        if not client_uuid:
            return False
        if not (config.xray_address or config.xray_host) or not config.xray_password:
            return False

        async with cls._session() as session:
            if not await cls._login(session):
                return False

            inbound = await cls._get_inbound(session, cls.get_inbound_id())
            if not inbound:
                return False
            client = cls._find_client(inbound, client_uuid)
            if not client:
                return False

            client["enable"] = False
            client["expiryTime"] = 1  # 1ms — гарантированно в прошлом
            client.setdefault("tgId", str(user_id))
            client.setdefault("limitIp", 0)
            client.setdefault("totalGB", 0)
            client.setdefault("reset", 0)

            payload = {
                "id": int(cls.get_inbound_id()),
                "settings": json.dumps({"clients": [client]}),
            }
            for url in [
                f"{cls._base_url()}/panel/api/inbounds/updateClient/{client_uuid}",
                f"{cls._base_url()}/xui/API/inbounds/updateClient/{client_uuid}",
            ]:
                try:
                    resp = await session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=15))
                    data = await resp.json(content_type=None)
                    if data.get("success"):
                        logger.info(f"XRay: disabled client {client_uuid} for user {user_id}")
                        return True
                except Exception as e:
                    logger.warning(f"XRay disable_client {url}: {e}")
        return False

    @classmethod
    async def reset_client(cls, user_id: int, days: int, old_key: str | None = None) -> tuple[str | None, str | None]:
        """Удаляет старый ключ и создаёт новый. Возвращает (vpn_key, sub_url)."""
        client_uuid = cls._extract_uuid(old_key) if old_key else None
        await cls.remove_client(user_id, client_uuid)
        return await cls.create_client(user_id, days)

    @classmethod
    async def recreate_inbound(cls) -> tuple[bool, int]:
        """
        Пересоздаёт Reality inbound с актуальными российскими настройками (sber.ru).
        Возвращает (success, new_inbound_id).
        Вызывается watchdog'ом автоматически при обнаружении отсутствия inbound.
        """
        global _active_inbound_id
        from config import config
        import secrets

        private_key = config.reality_private_key
        public_key = config.reality_public_key
        short_id = config.reality_short_id or secrets.token_hex(8)
        dest = config.reality_dest or "vk.com:443"
        sni = config.reality_sni or dest.split(":")[0]

        if not private_key or not public_key:
            logger.error("XRay recreate_inbound: REALITY_PRIVATE_KEY / REALITY_PUBLIC_KEY не заданы в .env")
            return False, 0

        inbound = {
            "enable": True,
            "remark": "MystVPN-Main",
            "listen": "",
            "port": 443,
            "protocol": "vless",
            "settings": json.dumps({"clients": [], "decryption": "none", "fallbacks": []}),
            "streamSettings": json.dumps({
                "network": "tcp",
                "security": "reality",
                "realitySettings": {
                    "show": False,
                    # ВАЖНО: оба поля нужны — старые версии xray-core читают `dest`,
                    # новые (26.x+) читают `target`. Если не задать оба, xray
                    # упадёт с "please fill in a valid value for target".
                    "dest": dest,
                    "target": dest,
                    "xver": 0,
                    "serverNames": [sni],
                    "privateKey": private_key,
                    "shortIds": [short_id],
                    "settings": {
                        "publicKey": public_key,
                        "fingerprint": "chrome",
                        "serverName": "",
                        "spiderX": "/",
                    },
                },
                "tcpSettings": {"acceptProxyProtocol": False, "header": {"type": "none"}},
            }),
            "sniffing": json.dumps({
                "enabled": True,
                "destOverride": ["http", "tls", "quic"],
                "metadataOnly": False,
            }),
        }

        async with cls._session() as session:
            if not await cls._login(session):
                logger.error("XRay recreate_inbound: login failed")
                return False, 0
            try:
                resp = await session.post(
                    f"{cls._base_url()}/panel/api/inbounds/add",
                    json=inbound,
                    timeout=aiohttp.ClientTimeout(total=15),
                )
                data = await resp.json(content_type=None)
                if data.get("success") and data.get("obj"):
                    new_id = data["obj"].get("id", 0)
                    _active_inbound_id = new_id
                    logger.info(f"XRay: inbound пересоздан, новый ID={new_id}, dest={dest}, sni={sni}")
                    return True, new_id
                logger.error(f"XRay recreate_inbound API error: {data.get('msg', data)}")
                return False, 0
            except Exception as e:
                logger.error(f"XRay recreate_inbound exception: {e}")
                return False, 0
