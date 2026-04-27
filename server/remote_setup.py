"""
Удалённое управление сервером MystVPN через SSH.
Запускать: python server/remote_setup.py [команда]
Команды: status, deploy, ssl, logs
"""
import sys
import os
os.environ["PYTHONIOENCODING"] = "utf-8"
import paramiko
import time

HOST = "77.110.96.77"
PORT = 22
USER = "root"
PASSWORD = "Ma9851H3pKIU"

DOMAIN = "keybest.cc"
EMAIL = "iliyaestas@gmail.com"
BOT_DIR = "/root/MystBot"

NGINX_HTTP_CONF = """server {
    listen 80;
    server_name keybest.cc www.keybest.cc;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location /webhook/yookassa {
        proxy_pass http://bot:8090/webhook/yookassa;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
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
}"""

NGINX_HTTPS_CONF = """server {
    listen 80;
    server_name keybest.cc www.keybest.cc;
    location /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://keybest.cc$request_uri; }
}

server {
    listen 443 ssl http2;
    server_name keybest.cc www.keybest.cc;

    ssl_certificate /etc/letsencrypt/live/keybest.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/keybest.cc/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
    }

    location /health {
        proxy_pass http://bot:8090/health;
        access_log off;
    }

    location / { return 444; }
}"""


def connect() -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, port=PORT, username=USER, password=PASSWORD, timeout=15)
    return client


def run(client: paramiko.SSHClient, cmd: str, timeout: int = 60) -> str:
    print(f"$ {cmd}")
    _, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode(errors="replace").strip()
    err = stderr.read().decode(errors="replace").strip()
    if out:
        print(out)
    if err and "Warning" not in err:
        print(f"[err] {err}")
    return out


def write_file(client: paramiko.SSHClient, path: str, content: str):
    sftp = client.open_sftp()
    with sftp.file(path, "w") as f:
        f.write(content)
    sftp.close()


def cmd_status(client):
    print("\n=== Docker контейнеры ===")
    run(client, f"cd {BOT_DIR} && docker compose ps")
    print("\n=== Последние логи бота ===")
    run(client, f"cd {BOT_DIR} && docker compose logs bot --tail=20")
    print("\n=== DNS keybest.cc ===")
    dns = run(client, "dig +short keybest.cc @8.8.8.8 2>/dev/null || echo 'dig not found'")
    print(f"keybest.cc → {dns or '(не настроен)'}")
    print("\n=== Свободное место ===")
    run(client, "df -h /")


def cmd_deploy(client):
    print("\n=== Деплой ===")
    run(client, f"cd {BOT_DIR} && git pull origin master", timeout=30)
    run(client, f"cd {BOT_DIR} && docker compose up -d --build bot", timeout=300)
    print("Ждём запуска БД...")
    time.sleep(10)
    run(client, f"cd {BOT_DIR} && docker compose exec -T bot python migrate.py", timeout=60)
    run(client, f"cd {BOT_DIR} && docker compose ps")


def cmd_ssl(client):
    print("\n=== Проверка DNS ===")
    dns = run(client, "dig +short keybest.cc @8.8.8.8 2>/dev/null")
    if "77.110.96.77" not in dns:
        print(f"DNS ещё не настроен: {dns or '(пусто)'}")
        print("Настрой A-запись на Dynadot и запусти снова.")
        return

    print("DNS OK. Получаем SSL сертификат...")
    # Пишем HTTP конфиг для certbot challenge
    write_file(client, f"{BOT_DIR}/nginx/conf.d/mystvpn.conf", NGINX_HTTP_CONF)
    run(client, f"cd {BOT_DIR} && docker compose exec nginx nginx -s reload 2>/dev/null || docker compose restart nginx")
    time.sleep(3)

    result = run(client,
        f"cd {BOT_DIR} && docker compose run --rm certbot certonly --webroot "
        f"-w /var/www/certbot -d {DOMAIN} -d www.{DOMAIN} "
        f"--email {EMAIL} --agree-tos --non-interactive 2>&1",
        timeout=120)

    if "Congratulations" in result or "Successfully received" in result:
        print("\nSSL получен! Включаем HTTPS...")
        write_file(client, f"{BOT_DIR}/nginx/conf.d/mystvpn.conf", NGINX_HTTPS_CONF)
        run(client, f"cd {BOT_DIR} && docker compose exec nginx nginx -s reload 2>/dev/null || docker compose restart nginx")
        print("\n✅ HTTPS работает на keybest.cc!")
        print("Обнови webhook в YooKassa: https://keybest.cc/webhook/yookassa")
    else:
        print("\n⚠️  SSL не получен. Проверь логи выше.")


def cmd_logs(client):
    run(client, f"cd {BOT_DIR} && docker compose logs bot --tail=50")


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    print(f"Подключение к {HOST}... (команда: {cmd})")
    try:
        client = connect()
        print("✅ Подключён\n")
    except Exception as e:
        print(f"❌ SSH ошибка: {e}")
        return

    try:
        if cmd == "status":
            cmd_status(client)
        elif cmd == "deploy":
            cmd_deploy(client)
        elif cmd == "ssl":
            cmd_ssl(client)
        elif cmd == "logs":
            cmd_logs(client)
        else:
            print(f"Неизвестная команда: {cmd}")
            print("Доступные: status, deploy, ssl, logs")
    finally:
        client.close()


if __name__ == "__main__":
    main()
