# CLAUDE.md — MystVPN / Full_Bot (КОРНЕВОЙ)

## Проект одной строкой
VPN-сервис для обхода блокировок РФ. Цель — топ-1 в России, 200к/мес.

## Модули
| Папка | Что | Статус |
|---|---|---|
| `VPN-Bot/` | Telegram-бот @MystVPN_bot — продажи, ключи, кабинет | 🟢 Прод |
| `Support_Bot/` | Бот поддержки — тикеты юзер↔саппорт + FAQ | 🟡 Новый |
| `VPN-Site/` | Лендинг keybest.cc | 🟢 Прод |
| `Bot-Traffic/` | Маркетинг-бот для закупа рекламы в TG | 🟠 Dev |
| `cpn-app/` | iOS/Android клиент (Tauri/Rust) | ⚪ Заготовка |
| `cpn-protocol/` | Протокол / обфускация | ⚪ Заготовка |

Каждая папка имеет **свой `CLAUDE.md`** с деталями модуля.

## Сервер
- IP: `77.110.96.77`, user: `root`, путь: `/root/Full_Bot`
- Домен: `keybest.cc`
- Всё в Docker Compose: `docker-compose.yml` в корне репо

## Деплой (автоматический)
```bash
git add -A && git commit -m "feat: ..." && git push origin master
# → GitHub Actions → SSH → git reset --hard → docker compose up -d --build bot
```
Workflow: `.github/workflows/deploy.yml`
GitHub Secrets: `SERVER_HOST`, `SSH_PRIVATE_KEY`

## Законы разработки (ОБЯЗАТЕЛЬНО)

### Никогда не ломать прод
- Деплои zero-downtime
- Изменения схемы БД — только обратно совместимо (nullable → backfill → required)
- Если что-то сломалось — фиксить немедленно, это приоритет #1

### Структура кода
- Один файл = одна ответственность, max ~150 строк
- handlers/ — только роутинг входящих событий
- services/ — бизнес-логика
- models/ — схемы данных
- keyboards/ — разметка UI
- Нет god-файлов. Нет дублирования. Нет преждевременных абстракций

### Комментарии
- Только если WHY неочевиден из кода
- Никогда не объяснять ЧТО делает код — для этого есть имена функций

### Автономность
- git add / commit / push делать самому после завершения задачи
- Не спрашивать подтверждения на чтение файлов, git, docker logs

## OPSEC — публичная коммуникация
**Нельзя:** VLESS, Reality, xray, прокси, протокол, обфускация, SNI
**Можно:** «обход блокировок», «работает когда другие падают», «без логов», «гарантия возврата»

## Полезные команды на сервере
```bash
docker compose ps                           # статус всех сервисов
docker compose logs -f bot                  # логи VPN-бота live
docker compose logs -f support-bot          # логи саппорт-бота
docker compose up -d --build bot            # пересборка VPN-бота
docker compose up -d --build support-bot    # пересборка саппорт-бота
docker compose exec -T bot python migrate.py  # миграции БД
```
