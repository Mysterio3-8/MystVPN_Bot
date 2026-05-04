#!/bin/bash
# Одноразовая инициализация SSL сертификата через Let's Encrypt
# Запускать один раз: bash scripts/init-ssl.sh bot.example.com admin@example.com

set -e

DOMAIN=${1:-""}
EMAIL=${2:-""}
PROJECT_DIR="/root/MystBot"
NGINX_CONF="$PROJECT_DIR/nginx/conf.d/mystvpn.conf"

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Использование: bash scripts/init-ssl.sh <domain> <email>"
    echo "Пример:        bash scripts/init-ssl.sh bot.example.com admin@example.com"
    exit 1
fi

cd "$PROJECT_DIR"

echo "=== [1/4] Проверяем что nginx запущен ==="
docker compose up -d nginx
sleep 3

echo "=== [2/4] Получаем сертификат для $DOMAIN ==="
docker compose run --rm certbot certonly \
    --webroot \
    -w /var/www/certbot \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email

echo "=== [3/4] Переключаем nginx на HTTPS конфиг ==="
cat > "$NGINX_CONF" << NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    add_header Strict-Transport-Security "max-age=63072000" always;

    location /webhook {
        proxy_pass http://bot:8090/webhook;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 30s;
    }

    location /health {
        proxy_pass http://bot:8090/health;
        access_log off;
    }

    location / {
        return 444;
    }
}
NGINXEOF

echo "=== [4/4] Перезагружаем nginx ==="
docker compose exec nginx nginx -s reload

echo ""
echo "✅ SSL настроен для $DOMAIN"
echo "   Webhook URL для YooKassa: https://$DOMAIN/webhook/yookassa"
echo "   Добавь в .env: WEBHOOK_URL=https://$DOMAIN/webhook/yookassa"
