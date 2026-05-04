#!/bin/bash
# Автобэкап PostgreSQL. Добавить в cron:
# 0 3 * * * /root/MystBot/scripts/backup.sh >> /root/MystBot/backup.log 2>&1

set -e

PROJECT_DIR="/root/MystBot"
BACKUP_DIR="/root/backups/postgres"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/mystvpn_${DATE}.sql.gz"
KEEP_DAYS=7

mkdir -p "$BACKUP_DIR"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Начинаю бэкап..."

docker compose -f "$PROJECT_DIR/docker-compose.yml" exec -T postgres \
    pg_dump -U mystvpn mystvpn_bot | gzip > "$BACKUP_FILE"

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Бэкап готов: $BACKUP_FILE ($SIZE)"

# Удаляем старые бэкапы
DELETED=$(find "$BACKUP_DIR" -name "*.sql.gz" -mtime +$KEEP_DAYS -print -delete | wc -l)
[ "$DELETED" -gt 0 ] && echo "[$(date '+%Y-%m-%d %H:%M:%S')] Удалено старых бэкапов: $DELETED"
