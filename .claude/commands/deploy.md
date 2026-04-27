# /deploy — Деплой MystVPN на сервер

## Что делает этот скилл

Деплоит текущую ветку `master` на сервер `77.110.96.77:/root/MystBot`.

## Инфраструктура

- **Сервер**: `77.110.96.77` (root), путь `/root/MystBot`
- **Деплой**: GitHub Actions → SSH → `git pull` → `docker compose up -d --build bot`
- **Авто-деплой**: cron `/root/MystBot/auto_deploy.sh` каждые 5 минут (fallback)
- **Стек**: Docker Compose (bot + postgres + redis + nginx + certbot)

## Как деплоить

### Основной способ (GitHub Actions — автоматически при push)
```bash
git add -A
git commit -m "feat: описание"
git push origin master
# → GitHub Actions запустит deploy.yml автоматически
```

### Ручной деплой через SSH (нужен SSH ключ или root пароль)
```bash
# Скопировать файлы через rsync (если SSH ключ настроен)
rsync -avz --exclude='.git' --exclude='__pycache__' \
  /c/Users/Professional/Desktop/MystBot/ root@77.110.96.77:/root/MystBot/

# Перезапустить бот
ssh root@77.110.96.77 "cd /root/MystBot && docker compose up -d --build bot"
```

### Через Python (paramiko — если известен root пароль)
```python
# server/remote_setup.py — шаблон SSH-скрипта уже есть в проекте
python server/remote_setup.py
```

## Команды на сервере (после SSH)

```bash
cd /root/MystBot

# Статус контейнеров
docker compose ps

# Логи бота (live)
docker compose logs -f bot

# Перезапуск бота
docker compose restart bot

# Полный rebuild
docker compose up -d --build bot

# Миграции БД
docker compose exec -T bot python migrate.py

# Логи nginx
docker compose logs -f nginx
```

## Что проверить после деплоя

1. `docker compose ps` — все контейнеры `running`
2. `docker compose logs bot --tail=20` — нет ошибок
3. Telegram: отправить `/start` боту `@MysterioVPN_bot`
4. `curl https://keybest.cc/webhook/yookassa` — nginx отвечает

## SSH доступ

- **Способ 1**: SSH ключ в GitHub Secrets (`SSH_PRIVATE_KEY`) — для GitHub Actions
- **Способ 2**: root пароль сервера (отличается от пароля 3x-ui `MystAdmin2026`)
- **Способ 3**: `server/remote_setup.py` через paramiko с паролем

## GitHub Secrets (для Actions)
- `SERVER_HOST` = `77.110.96.77`
- `SSH_PRIVATE_KEY` = приватный SSH ключ

Если Actions не работают, проверить: Settings → Secrets → Actions в репо GitHub.
