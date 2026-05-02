# План миграции основного бота: корень → bot/

## Зачем
Сейчас основной бот (main.py, handlers/, models/, services/) лежит в корне репозитория. Это смешивается с другими модулями (site/, traffic-bot/, vpn-app/, vpn-protocol/). Нужно вынести в `bot/`.

## Почему НЕ сделано в коммите со структурой папок
Перенос требует одновременного изменения:
- `Dockerfile` (изменение `WORKDIR` или путей)
- `docker-compose.yml` (`build: .` → `build: ./bot`)
- `.github/workflows/deploy.yml` (пути на сервере)
- На сервере `/root/MystBot` — структура должна совпадать после `git pull`

Любая ошибка → бот падает. С 2 платящими юзерами риск неприемлем.

## Когда делать
В **выходной день / ночью**, когда минимум активных юзеров. Заранее предупредить юзеров через бот: «обновление в N часов, возможны кратковременные перебои».

## План пошагово (когда дойдёт время)

### Шаг 1. Локально создать ветку миграции
```bash
git checkout -b refactor/move-bot-to-subfolder
```

### Шаг 2. Перенести файлы
```bash
git mv main.py bot/
git mv config.py bot/
git mv migrate.py bot/
git mv webhook_server.py bot/
git mv handlers bot/
git mv models bot/
git mv services bot/
git mv keyboards bot/
git mv locales bot/
git mv database bot/
git mv requirements.txt bot/
git mv Dockerfile bot/
```

### Шаг 3. Обновить docker-compose.yml
```yaml
services:
  bot:
    build: ./bot           # было: .
```

### Шаг 4. Обновить deploy.yml
- `cp -r /root/MystBot/site/*` → не меняется (site остался)
- `docker compose exec -T bot python migrate.py` — внутри контейнера WORKDIR /app, путь не меняется
- Проверить что .backup и `bot_data.db` не попадут в Docker контекст

### Шаг 5. Локальный тест
```bash
docker compose build bot
docker compose up -d
docker compose logs -f bot
```

### Шаг 6. Деплой через окно обслуживания
1. Бот шлёт юзерам: «техработы 5 минут, скоро вернёмся»
2. `git push origin master`
3. Watch deploy.yml в GitHub Actions
4. Проверить: `docker compose ps`, `docker compose logs --tail=100 bot`
5. Проверить вручную: бот отвечает на /start, кабинет, ключ выдаётся

## Риски и митигация
| Риск | Митигация |
|---|---|
| Деплой падает из-за неправильного пути | Тест локально ДО пуша |
| Миграции БД ломаются | `python migrate.py` не зависит от пути |
| nginx теряет static/ | nginx раздаёт `./site:/usr/share/nginx/html` — site не двигаем |
| Юзер платит во время даунтайма | Окно обслуживания + ретрай webhook YooKassa |

## Откат
```bash
ssh root@77.110.96.77
cd /root/MystBot
git revert HEAD
git push origin master
```

## Не забыть
- Перед стартом: `git status` чистый
- После: обновить корневой CLAUDE.md
- После: обновить скилы в `.claude/commands/` если ссылаются на пути
