#!/bin/bash
# Автодеплой MystBot: запускать по cron каждые 2 минуты
# Установка: crontab -e → добавить строку:
# */2 * * * * /root/MystBot/MystBot/auto_deploy.sh >> /root/MystBot/deploy.log 2>&1

BOT_DIR="/root/MystBot/MystBot"
BRANCH="main"

cd "$BOT_DIR" || exit 1

# Получаем изменения без применения
git fetch origin "$BRANCH" --quiet

LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse "origin/$BRANCH")

if [ "$LOCAL" != "$REMOTE" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Новые изменения! Обновляю..."
    git pull origin "$BRANCH"
    docker compose up -d --build bot
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Готово. Версия: $(git rev-parse --short HEAD)"
fi
