#!/bin/bash
set -e

echo "🚀 MystVPN Deploy Script"
echo "========================"

# 1. Логин в Docker Hub (снимает rate limit)
echo "📦 Проверка Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker не запущен!"
    exit 1
fi

# 2. Запуск контейнеров
echo "🔨 Сборка и запуск контейнеров..."
docker compose pull postgres redis 2>/dev/null || true
docker compose up -d --build

# 3. Ждём PostgreSQL
echo "⏳ Ожидание базы данных..."
sleep 5

# 4. Миграции БД
echo "🗄️  Применение миграций..."
docker compose exec -T bot python migrate.py

echo ""
echo "✅ Готово! Бот запущен."
echo ""
echo "Полезные команды:"
echo "  docker compose logs -f bot     — логи бота"
echo "  docker compose ps              — статус контейнеров"
echo "  docker compose restart bot     — перезапуск"
