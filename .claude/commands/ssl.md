# /ssl — Активация SSL для keybest.cc

## Когда запускать

Только после того, как DNS `keybest.cc → 77.110.96.77` разошёлся.

Проверка DNS:
```bash
# Из любого терминала
nslookup keybest.cc 8.8.8.8
# Должно вернуть: 77.110.96.77
```

## Шаг 1 — Обновить nginx конфиг

В файле `nginx/conf.d/mystvpn.conf` заменить всё содержимое на:

```nginx
server {
    listen 80;
    server_name keybest.cc www.keybest.cc;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://keybest.cc$request_uri; }
}

server {
    listen 443 ssl;
    server_name keybest.cc www.keybest.cc;

    ssl_certificate /etc/letsencrypt/live/keybest.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/keybest.cc/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    add_header Strict-Transport-Security "max-age=63072000" always;

    location /webhook/yookassa {
        proxy_pass http://bot:8090/webhook/yookassa;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_read_timeout 30s;
    }

    location /fkbumQABLZHiek0B/ {
        proxy_pass http://127.0.0.1:2096/fkbumQABLZHiek0B/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://bot:8090/health;
        access_log off;
    }

    location / { return 444; }
}
```

## Шаг 2 — Деплой + получение сертификата

```bash
# Push обновлённого nginx конфига
git add nginx/conf.d/mystvpn.conf
git commit -m "feat: enable SSL for keybest.cc"
git push origin master
# → GitHub Actions задеплоит автоматически

# Затем на сервере получить сертификат:
ssh root@77.110.96.77 "cd /root/MystBot && docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d keybest.cc -d www.keybest.cc \
  --email iliyaestas@gmail.com --agree-tos --non-interactive && \
  docker compose restart nginx"
```

## Шаг 3 — Проверка

```bash
curl -I https://keybest.cc/health
# Должно вернуть: HTTP/2 200
```

## Автообновление сертификата

Уже настроено в docker-compose.yml — контейнер `certbot` обновляет сертификат каждые 12 часов автоматически.
