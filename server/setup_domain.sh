#!/bin/bash
# Запускать от root на сервере 77.110.96.77
# chmod +x setup_domain.sh && ./setup_domain.sh

set -e

DOMAIN="keybest.cc"
EMAIL="iliyaestas@gmail.com"

echo "=== Установка nginx и certbot ==="
apt-get update -q
apt-get install -y nginx certbot python3-certbot-nginx

echo "=== Копирование nginx конфига ==="
cp nginx_keybest.conf /etc/nginx/sites-available/$DOMAIN
ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/$DOMAIN
rm -f /etc/nginx/sites-enabled/default

nginx -t && systemctl reload nginx

echo "=== Получение SSL сертификата (Let's Encrypt) ==="
certbot certonly --nginx -d $DOMAIN -d www.$DOMAIN \
    --non-interactive --agree-tos --email $EMAIL

echo "=== Перезапуск nginx с SSL ==="
nginx -t && systemctl reload nginx

echo "=== Включение автообновления сертификата ==="
systemctl enable certbot.timer
systemctl start certbot.timer

echo ""
echo "✅ Готово! Проверь:"
echo "   https://$DOMAIN/webhook/yookassa  → должен ответить бот"
echo "   https://$DOMAIN/fkbumQABLZHiek0B/ → подписки 3x-ui"
