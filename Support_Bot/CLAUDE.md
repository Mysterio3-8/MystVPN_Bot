# CLAUDE.md — Support_Bot

## Назначение
Telegram-бот поддержки для MystVPN. Пользователь пишет боту → сообщение попадает
в группу саппорта → саппорт отвечает через Reply → ответ идёт обратно пользователю.

## Стек
- Python 3.11 + aiogram 3.13
- SQLite (aiosqlite) — `support.db`, без внешней БД
- MemoryStorage FSM (нет Redis)
- Docker: `Support_Bot/` → сервис `support-bot` в корневом docker-compose.yml

## Структура
```
Support_Bot/
├── main.py                  # точка входа, polling
├── config.py                # Config.from_env()
├── requirements.txt
├── Dockerfile
├── .env.example             # шаблон переменных
├── database/db.py           # init_db, CRUD тикетов, маршрутизация
├── handlers/
│   ├── user_handler.py      # /start, FAQ, чат с поддержкой
│   └── support_handler.py   # Reply в группе → роутинг к юзеру
├── keyboards/keyboards.py   # main_menu, faq, support_active
├── content/faq.py           # 10 разделов FAQ о MystVPN
└── services/ai_stub.py      # ИИ-заглушка (готова к интеграции Claude)
```

## Как работает маршрутизация
1. Юзер пишет → `user_handler.relay_to_support()` → сообщение в группу → `msg_routing` запись
2. Саппорт нажимает Reply в группе → `support_handler.handle_support_reply()` → lookup в `msg_routing` → отправить юзеру
3. Ответ саппорта тоже регистрируется в `msg_routing` → цепочка продолжается

## Таблицы БД
- `tickets` — id, user_id, username, status (open/closed), created_at
- `messages` — id, ticket_id, from_support, text, created_at
- `msg_routing` — support_msg_id → ticket_id + user_id

## Команды саппорта в группе
- `/tickets` — список открытых тикетов
- `/close <id>` — закрыть тикет командой
- Кнопка «✅ Закрыть тикет» на первом сообщении нового тикета

## Переменные .env
```
SUPPORT_BOT_TOKEN=    # токен бота (отдельный от VPN-бота!)
SUPPORT_GROUP_ID=     # ID группы поддержки (отрицательное число)
SUPPORT_ADMIN_IDS=    # ID саппортов через запятую
DB_PATH=support.db
```

## Запуск
```bash
cp .env.example .env && nano .env
docker compose up -d support-bot
docker compose logs -f support-bot
```

## ИИ-интеграция (будущее)
`services/ai_stub.py` — содержит полный закомментированный код для Claude.
Активация: раскомментировать, добавить `ANTHROPIC_API_KEY` в `.env`.
Модель: `claude-sonnet-4-6`. Логика: ответить если знает → None если нет → саппорт.
