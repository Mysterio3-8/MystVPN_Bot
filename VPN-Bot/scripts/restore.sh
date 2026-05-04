#!/bin/bash
# Восстановление БД из бэкапа
# Использование: bash scripts/restore.sh /root/backups/postgres/mystvpn_20260425_030000.sql.gz

set -e

BACKUP_FILE=${1:-""}
PROJECT_DIR="/root/MystBot"

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
    echo "Использование: bash scripts/restore.sh <путь_к_бэкапу.sql.gz>"
    echo ""
    echo "Доступные бэкапы:"
    ls -lh /root/backups/postgres/*.sql.gz 2>/dev/null || echo "  Бэкапы не найдены"
    exit 1
fi

echo "⚠️  ВНИМАНИЕ: Текущая БД будет ПЕРЕЗАПИСАНА данными из $BACKUP_FILE"
read -r -p "Продолжить? (yes/no): " CONFIRM
[ "$CONFIRM" != "yes" ] && echo "Отменено." && exit 0

cd "$PROJECT_DIR"

echo "=== Останавливаем бота ==="
docker compose stop bot

echo "=== Восстанавливаем БД ==="
gunzip -c "$BACKUP_FILE" | docker compose exec -T postgres \
    psql -U mystvpn -d mystvpn_bot

echo "=== Запускаем бота ==="
docker compose start bot

echo "✅ БД восстановлена из $BACKUP_FILE"
