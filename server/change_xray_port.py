import json, urllib.request, http.cookiejar, ssl, urllib.parse, time, subprocess

base = "https://127.0.0.1:2215/gcOiC1hEvMgDfnZmbz"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(
    urllib.request.HTTPSHandler(context=ctx),
    urllib.request.HTTPCookieProcessor(jar)
)

data = urllib.parse.urlencode({"username": "admin", "password": "MystAdmin2026"}).encode()
resp = opener.open(urllib.request.Request(f"{base}/login", data=data), timeout=10)
ok = json.loads(resp.read()).get("success")
print("login:", ok)

resp = opener.open(urllib.request.Request(f"{base}/panel/api/inbounds/get/1"), timeout=10)
inbound = json.loads(resp.read())
obj = inbound["obj"]
print(f"current port: {obj['port']}")

if obj["port"] == 44300:
    print("already on 44300")
else:
    obj["port"] = 44300
    req = urllib.request.Request(
        f"{base}/panel/api/inbounds/update/1",
        data=json.dumps(obj).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = opener.open(req, timeout=15)
    r = json.loads(resp.read())
    print(f"changed: success={r.get('success')} msg={r.get('msg','')}")

# Ждём пока xray отпустит порт 443
print("waiting for xray to release port 443...")
time.sleep(3)

# Проверяем
r = subprocess.run("ss -tlnp | grep ':443 '", shell=True, capture_output=True, text=True)
if "xray" in r.stdout:
    print("xray still on 443, waiting more...")
    time.sleep(5)

# Перезапускаем nginx чтобы занял 443
r = subprocess.run("systemctl reload nginx", shell=True, capture_output=True, text=True)
print("nginx reload:", r.returncode == 0)

time.sleep(2)
r = subprocess.run("ss -tlnp | grep -E ':443 |:8444 '", shell=True, capture_output=True, text=True)
print("Ports after:")
print(r.stdout.strip())

# Тест
r = subprocess.run("curl -sk https://keybest.cc/health -o /dev/null -w '%{http_code}'", shell=True, capture_output=True, text=True)
print(f"https://keybest.cc/health -> HTTP {r.stdout}")
