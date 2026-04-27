"""
Настройка nginx stream SNI-роутинга на хосте сервера.
Запускать: python3 /tmp/setup_stream.py
"""
import os, subprocess, json, urllib.request, http.cookiejar, ssl, urllib.parse, re

# Содержимое stream.d файла — БЕЗ обёртки stream{}, она будет в nginx.conf
STREAM_MAP_CONF = """\
    map $ssl_preread_server_name $backend {
        keybest.cc    127.0.0.1:8444;
        default       127.0.0.1:44300;
    }

    server {
        listen 443;
        proxy_pass $backend;
        ssl_preread on;
        proxy_connect_timeout 5s;
    }
"""

HTTPS_SITE_CONF = """\
server {
    listen 80;
    server_name keybest.cc;
    location /.well-known/acme-challenge/ { root /var/www/html; }
    location / { return 301 https://keybest.cc$request_uri; }
}

server {
    listen 8444 ssl http2;
    server_name keybest.cc;

    ssl_certificate /etc/letsencrypt/live/keybest.cc/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/keybest.cc/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    add_header Strict-Transport-Security "max-age=63072000" always;

    location /webhook/yookassa {
        proxy_pass http://127.0.0.1:8090/webhook/yookassa;
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
        proxy_pass http://127.0.0.1:8090/health;
        access_log off;
    }

    location / { return 444; }
}
"""


def sh(cmd, timeout=30):
    print(f"$ {cmd}")
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
    if r.stdout.strip(): print(r.stdout.strip())
    if r.stderr.strip(): print("[err]", r.stderr.strip())
    return r.stdout.strip()


def write(path, content):
    with open(path, "w") as f:
        f.write(content)
    print(f"Written: {path}")


def main():
    nginx_conf = "/etc/nginx/nginx.conf"

    with open(nginx_conf) as f:
        conf = f.read()

    # 1. Добавляем load_module если нет
    load_line = "load_module /usr/lib/nginx/modules/ngx_stream_module.so;"
    if load_line not in conf:
        conf = load_line + "\n" + conf
        print("Added load_module directive")

    # 2. Удаляем старый include stream.d (если добавили раньше)
    conf = re.sub(r'\ninclude /etc/nginx/stream.d/\*\.conf;\n?', '', conf)

    # 3. Добавляем stream блок в конец (вне http{})
    stream_block = "\nstream {\n    include /etc/nginx/stream.d/*.conf;\n}\n"
    if "stream {" not in conf:
        conf = conf + stream_block
        print("Added stream block to nginx.conf")

    write(nginx_conf, conf)

    # 4. Пишем содержимое stream.d
    os.makedirs("/etc/nginx/stream.d", exist_ok=True)
    write("/etc/nginx/stream.d/sni_router.conf", STREAM_MAP_CONF)

    # 5. Обновляем sites-available: порт 8444
    write("/etc/nginx/sites-available/keybest.cc", HTTPS_SITE_CONF)

    # 6. Проверяем и перезапускаем nginx
    result = sh("nginx -t 2>&1")
    if "successful" in result:
        sh("systemctl reload nginx")
        print("\nnginx reloaded OK")
    else:
        print("\nnginx config ERROR - aborting")
        return

    print("\n--- Ports ---")
    sh("ss -tlnp | grep -E ':80 |:443 |:8444 |:44300 '")

    print("\n--- Changing 3x-ui inbound port 443 → 44300 ---")
    change_inbound_port()

    print("\nDone!")
    sh("curl -sk https://keybest.cc/health -o /dev/null -w 'HTTPS health: %{http_code}'")


def change_inbound_port():
    base = "https://127.0.0.1:2215/gcOiC1hEvMgDfnZmbz"
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar)
    )
    try:
        data = urllib.parse.urlencode({"username": "admin", "password": "MystAdmin2026"}).encode()
        resp = opener.open(urllib.request.Request(f"{base}/login", data=data), timeout=10)
        result = json.loads(resp.read())
        print("3x-ui login:", result.get("success"))
        if not result.get("success"):
            return

        resp = opener.open(urllib.request.Request(f"{base}/panel/api/inbounds/get/1"), timeout=10)
        inbound = json.loads(resp.read())
        obj = inbound.get("obj", {})
        old_port = obj.get("port")
        print(f"Current inbound port: {old_port}")

        if old_port == 44300:
            print("Already on 44300")
            return

        obj["port"] = 44300
        req = urllib.request.Request(
            f"{base}/panel/api/inbounds/update/1",
            data=json.dumps(obj).encode(),
            headers={"Content-Type": "application/json"}
        )
        resp = opener.open(req, timeout=15)
        result = json.loads(resp.read())
        print(f"Changed to 44300: success={result.get('success')} {result.get('msg','')}")
    except Exception as e:
        print(f"3x-ui error: {e}")


if __name__ == "__main__":
    main()
