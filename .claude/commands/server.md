# /server — Управление сервером и панелью 3x-ui

## Сервер

| Параметр | Значение |
|---|---|
| IP | `77.110.96.77` |
| SSH user | `root` |
| SSH порт | `22` |
| Путь проекта | `/root/MystBot` |
| 3x-ui пароль | `MystAdmin2026` (только для панели, не SSH) |

## 3x-ui панель

- **URL**: `https://77.110.96.77:2215/gcOiC1hEvMgDfnZmbz`
- **Логин**: `admin` / **Пароль**: `MystAdmin2026`
- **Inbound ID**: `1` (VLESS Reality, порт 443)
- **Subscription сервер**: порт `2096`, путь `/fkbumQABLZHiek0B/`

### API 3x-ui (через XrayService в коде)

```
POST /login                          — авторизация
GET  /panel/api/inbounds/list        — список inbound'ов
GET  /panel/api/inbounds/get/{id}    — получить inbound
POST /panel/api/inbounds/addClient   — добавить клиента
POST /panel/api/inbounds/{id}/delClient/{uuid} — удалить клиента
POST /panel/api/inbounds/add         — создать inbound
```

## Домен keybest.cc

- **Регистратор**: Dynadot (`dynadot.com`)
- **DNS**: нужна A-запись `keybest.cc → 77.110.96.77`
- **SSL**: Let's Encrypt через certbot (docker контейнер в compose)

### Как настроить DNS на Dynadot

1. Войти на `dynadot.com` → My Domains → `keybest.cc` → DNS Settings
2. Добавить записи:
   - Type: `A`, Host: `@`, Points to: `77.110.96.77`, TTL: 300
   - Type: `A`, Host: `www`, Points to: `77.110.96.77`, TTL: 300
3. Сохранить. DNS обновляется ~5–15 минут.

### Как активировать SSL после DNS

```bash
ssh root@77.110.96.77
cd /root/MystBot
bash scripts/init-ssl.sh
```

Или вручную:
```bash
# На сервере:
docker compose run --rm certbot certonly --webroot \
  -w /var/www/certbot \
  -d keybest.cc -d www.keybest.cc \
  --email iliyaestas@gmail.com --agree-tos --non-interactive
```

## nginx конфиг (Docker)

Файл: `nginx/conf.d/mystvpn.conf` (монтируется в контейнер)

Маршруты после настройки SSL:
- `keybest.cc/webhook/yookassa` → `bot:8090/webhook/yookassa`
- `keybest.cc/fkbumQABLZHiek0B/` → подписки 3x-ui (порт 2096)

После изменения конфига:
```bash
docker compose exec nginx nginx -s reload
# или
docker compose restart nginx
```

## Docker Compose сервисы

| Сервис | Роль | Порты |
|---|---|---|
| `bot` | Telegram бот | 8090 (webhook) |
| `postgres` | БД | 127.0.0.1:5432 |
| `redis` | Кэш/FSM | 127.0.0.1:6379 |
| `nginx` | Reverse proxy | 80, 443 |
| `certbot` | SSL авто-обновление | — |

## YooKassa webhook

После смены домена обновить URL в кабинете YooKassa:
- URL: `https://keybest.cc/webhook/yookassa`
- Секрет: из `.env` → `WEBHOOK_SECRET`
- Кабинет: `yookassa.ru` → Настройки → HTTP-уведомления
