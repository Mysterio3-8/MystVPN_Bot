#!/bin/bash
set -e

echo ""
echo "=============================="
echo "  MystVPN Bot — Setup Server  "
echo "=============================="
echo ""

# 1. Docker
if ! command -v docker &>/dev/null; then
    echo ">>> Устанавливаю Docker..."
    curl -fsSL https://get.docker.com | sh
    echo ">>> Docker установлен"
else
    echo ">>> Docker уже есть: $(docker --version)"
fi

# 2. Клонируем репо
if [ ! -d /root/MystBot ]; then
    echo ">>> Скачиваю бота..."
    git clone https://github.com/Mysterio3-8/MystVPN_Bot.git /root/MystBot
else
    echo ">>> Обновляю бота..."
    cd /root/MystBot && git pull origin master 2>/dev/null || git pull origin main
fi

cd /root/MystBot

# 3. Создаём .env (только если его ещё нет)
if [ ! -f .env ]; then
    echo ">>> Создаю .env..."
    cat > .env << 'ENVEOF'
BOT_TOKEN=PASTE_BOT_TOKEN_HERE
BOT_USERNAME=MystVPN_bot
DATABASE_URL=postgresql+asyncpg://mystvpn:mystvpn_secret@postgres:5432/mystvpn_bot
REDIS_HOST=redis
REDIS_PORT=6379
YOOKASSA_ACCOUNT_ID=PASTE_YOOKASSA_ID_HERE
YOOKASSA_SECRET_KEY=PASTE_YOOKASSA_KEY_HERE
ADMIN_IDS=PASTE_YOUR_TELEGRAM_ID_HERE
WEBHOOK_URL=https://keybest.cc/webhook/yookassa
WEBHOOK_SECRET=PASTE_WEBHOOK_SECRET_HERE
WEBHOOK_PORT=8090
XRAY_HOST=77.110.96.77
XRAY_PORT=8080
XRAY_USERNAME=PASTE_XRAY_USER_HERE
XRAY_PASSWORD=PASTE_XRAY_PASS_HERE
XRAY_INBOUND_ID=1
XRAY_ADDRES=http://77.110.96.77:8080/PASTE_PATH_HERE
SUB_DOMAIN=https://keybest.cc
SUB_PATH=/sub/
ENVEOF
    echo ""
    echo "⚠️  Заполни .env перед запуском:"
    echo "   nano /root/MystBot/.env"
    echo ""
    echo "Замени все PASTE_*_HERE на реальные значения, затем запусти снова."
    exit 0
fi

# 4. Запускаем
echo ">>> Запускаю контейнеры..."
docker compose up -d --build bot postgres redis

echo ">>> Жду запуска базы данных..."
sleep 12

echo ">>> Применяю миграции..."
docker compose exec -T bot python migrate.py || true

echo ""
echo ">>> Логи бота:"
docker compose logs bot --tail=20

echo ""
echo "=============================="
echo "  ✅ Бот запущен!"
echo "  Логи: docker compose -f /root/MystBot/docker-compose.yml logs -f bot"
echo "=============================="
