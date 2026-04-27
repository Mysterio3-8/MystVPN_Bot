# CLAUDE.md — MystVPN Telegram Bot

## Быстрые команды (локально)
- **Зависимости:** `pip install -r requirements.txt`
- **Запуск:** `python main.py`
- **Проверка Telegram API:** `curl https://api.telegram.org`

## Технический стек
- **Backend:** Python 3.11, aiogram 3.x, async/await везде
- **БД:** PostgreSQL 16 (SQLAlchemy ORM), миграции через `migrate.py`
- **Кэш/FSM:** Redis 7
- **Платежи:** YooKassa (RUB) + Telegram Stars (XTR)
- **VPN панель:** 3x-ui (VLESS Reality)
- **Локализация:** JSON locales в `locales/`

## Структура проекта
- `handlers/` — логика команд (start, buy, cabinet, admin, payments)
- `models/` — схемы БД (User, Subscription, Payment, Promo)
- `services/` — бизнес-логика (xray_service, yookassa, i18n)
- `keyboards/` — inline и reply клавиатуры
- `locales/` — переводы (RU, EN и ещё 15 языков)
- `nginx/conf.d/` — nginx конфиг (монтируется в Docker)
- `.claude/commands/` — скиллы: `/deploy`, `/server`, `/ssl`

## Сервер и деплой

### Инфраструктура
| Параметр | Значение |
|---|---|
| IP сервера | `77.110.96.77` |
| Путь на сервере | `/root/MystBot` |
| SSH пользователь | `root` |
| Домен | `keybest.cc` (Dynadot) |
| Деплой | Docker Compose |

### Как деплоить (основной способ)
```bash
git add -A && git commit -m "feat: ..." && git push origin master
# GitHub Actions (.github/workflows/deploy.yml) автоматически:
# 1. SSH на сервер по ключу (SECRET: SSH_PRIVATE_KEY)
# 2. git pull origin master
# 3. docker compose up -d --build bot
# 4. python migrate.py
```

### Команды на сервере после SSH
```bash
docker compose ps                        # статус
docker compose logs -f bot               # логи live
docker compose restart bot               # перезапуск
docker compose up -d --build bot         # rebuild
docker compose exec -T bot python migrate.py  # миграции
docker compose exec nginx nginx -s reload     # reload nginx без даунтайма
```

### GitHub Actions
- Файл: `.github/workflows/deploy.yml`
- Триггер: push в `master`
- Секреты: `SERVER_HOST` = `77.110.96.77`, `SSH_PRIVATE_KEY`
- Авто-деплой fallback: `auto_deploy.sh` (cron каждые 5 мин на сервере)

## 3x-ui панель
- **URL:** `https://77.110.96.77:2215/gcOiC1hEvMgDfnZmbz`
- **Логин/пароль:** `admin` / `MystAdmin2026`
- **Inbound ID:** `1` (VLESS Reality, порт 443, dest: vk.com)
- **Subscription порт:** `2096`, путь `/fkbumQABLZHiek0B/`
- **XrayService:** `services/xray_service.py` — вся логика создания/удаления ключей

## Домен keybest.cc
- **Регистратор:** Dynadot (`dynadot.com`)
- **DNS нужен:** A-запись `keybest.cc → 77.110.96.77`
- **Настройка DNS:** My Domains → keybest.cc → DNS Settings → добавить A @ и A www
- **SSL:** Let's Encrypt, certbot контейнер в docker-compose, авто-обновление каждые 12ч
- **Для SSL активации:** см. скилл `/ssl`

## nginx маршруты (после SSL)
- `keybest.cc/webhook/yookassa` → `bot:8090`
- `keybest.cc/fkbumQABLZHiek0B/` → 3x-ui subscription (порт 2096)

## YooKassa
- **Account ID:** `1314296`
- **Webhook URL:** `https://keybest.cc/webhook/yookassa`
- **Секрет:** в `.env` → `WEBHOOK_SECRET`
- После смены домена: `yookassa.ru` → Настройки → HTTP-уведомления → обновить URL

## Платежи
- `XTR` — Telegram Stars (обработка в `handlers/payments.py`)
- `RUB` — YooKassa (webhook на `/webhook/yookassa`)
- Обработка успешной оплаты: `services/payment_service.py`

## Правила разработки
- PEP 8, async/await везде
- Никогда не хардкодить токены — только через `.env` и `config.py`
- Доступ к admin командам — только для ID из `ADMIN_IDS`
- При изменении моделей — запускать `migrate.py`
- Комментарии только если WHY неочевиден

## Скиллы (slash-команды для Claude)
- `/deploy` — инструкция по деплою
- `/server` — управление сервером и 3x-ui
- `/ssl` — активация SSL для keybest.cc
