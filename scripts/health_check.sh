#!/usr/bin/env bash
# health_check.sh — проверка здоровья MystVPN сервера
# Запуск на сервере: bash /root/MystBot/scripts/health_check.sh
# Запуск локально (через SSH): ssh root@77.110.96.77 'bash -s' < scripts/health_check.sh

set -u

PASS="✅"
FAIL="❌"
WARN="⚠️ "

errors=0
warnings=0

print_header() {
    echo ""
    echo "════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════"
}

check() {
    local name="$1"
    local cmd="$2"
    local expect="${3:-0}"

    if eval "$cmd" >/dev/null 2>&1; then
        local rc=0
    else
        local rc=$?
    fi

    if [ "$rc" -eq "$expect" ]; then
        echo "  $PASS $name"
        return 0
    else
        echo "  $FAIL $name (rc=$rc)"
        errors=$((errors + 1))
        return 1
    fi
}

warn_check() {
    local name="$1"
    local cmd="$2"

    if eval "$cmd" >/dev/null 2>&1; then
        echo "  $PASS $name"
        return 0
    else
        echo "  $WARN $name"
        warnings=$((warnings + 1))
        return 1
    fi
}

print_header "1. Docker контейнеры"

cd /root/MystBot 2>/dev/null || { echo "  $FAIL Не найдена директория /root/MystBot"; exit 2; }

check "docker compose ps возвращает результат" "docker compose ps -q"
check "контейнер bot запущен" "docker compose ps bot --format json | grep -q '\"State\":\"running\"'"
check "контейнер postgres запущен" "docker compose ps postgres --format json | grep -q '\"State\":\"running\"'"
check "контейнер redis запущен" "docker compose ps redis --format json | grep -q '\"State\":\"running\"'"
check "контейнер nginx запущен" "docker compose ps nginx --format json | grep -q '\"State\":\"running\"'"

print_header "2. Сервисы внутри контейнеров"

check "PostgreSQL принимает подключения" "docker compose exec -T postgres pg_isready -U mystvpn"
check "Redis отвечает PING" "docker compose exec -T redis redis-cli ping | grep -q PONG"
check "bot не сыпет critical в логах (последние 100 строк)" "! docker compose logs --tail=100 bot 2>&1 | grep -iE 'critical|fatal|traceback' | grep -v 'INFO'"

print_header "3. Сеть и порты"

check "порт 443 слушается (HTTPS)" "ss -tlnp | grep -q ':443 '"
check "порт 80 слушается (HTTP)" "ss -tlnp | grep -q ':80 '"
warn_check "порт 44300 слушается (xray Reality)" "ss -tlnp | grep -q ':44300 '"
warn_check "порт 2052 слушается (xray XHTTP)" "ss -tlnp | grep -q ':2052 '"
warn_check "порт 2096 слушается (xray subscription)" "ss -tlnp | grep -q ':2096 '"
warn_check "порт 8090 слушается (bot webhook)" "ss -tlnp | grep -q ':8090 '"

print_header "4. SSL сертификат keybest.cc"

if command -v openssl >/dev/null 2>&1; then
    cert_info=$(echo | openssl s_client -servername keybest.cc -connect keybest.cc:443 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)

    if [ -n "$cert_info" ]; then
        echo "  $PASS Сертификат доступен"
        echo "$cert_info" | sed 's/^/    /'

        not_after=$(echo "$cert_info" | grep notAfter | cut -d= -f2)
        if [ -n "$not_after" ]; then
            expire_ts=$(date -d "$not_after" +%s 2>/dev/null || echo 0)
            now_ts=$(date +%s)
            days_left=$(( (expire_ts - now_ts) / 86400 ))

            if [ "$days_left" -gt 7 ]; then
                echo "  $PASS Сертификат валиден ещё $days_left дней"
            elif [ "$days_left" -gt 0 ]; then
                echo "  $WARN Сертификат истекает через $days_left дней — пора обновлять"
                warnings=$((warnings + 1))
            else
                echo "  $FAIL Сертификат истёк или не валиден"
                errors=$((errors + 1))
            fi
        fi
    else
        echo "  $FAIL Не удалось получить сертификат с keybest.cc:443"
        errors=$((errors + 1))
    fi
fi

print_header "5. HTTP эндпоинты"

check "keybest.cc отдаёт 200/301" "curl -sk -o /dev/null -w '%{http_code}' https://keybest.cc/ | grep -qE '200|301|302'"
warn_check "keybest.cc/webhook/yookassa отвечает (любой код != 5xx)" "curl -sk -o /dev/null -w '%{http_code}' https://keybest.cc/webhook/yookassa -X POST -H 'Content-Type: application/json' -d '{}' | grep -qvE '^5'"
warn_check "keybest.cc/fkbumQABLZHiek0B/ отдаёт что-то" "curl -sk -o /dev/null -w '%{http_code}' https://keybest.cc/fkbumQABLZHiek0B/ | grep -qE '200|404|400'"

print_header "6. Disk и Memory"

disk_used=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$disk_used" -lt 80 ]; then
    echo "  $PASS Диск: ${disk_used}% использовано"
else
    echo "  $WARN Диск: ${disk_used}% — больше 80%"
    warnings=$((warnings + 1))
fi

mem_used_pct=$(free | awk '/^Mem:/ {printf "%.0f", $3/$2 * 100}')
if [ "$mem_used_pct" -lt 80 ]; then
    echo "  $PASS Memory: ${mem_used_pct}% использовано"
else
    echo "  $WARN Memory: ${mem_used_pct}% — больше 80%"
    warnings=$((warnings + 1))
fi

print_header "7. БД — sanity"

users_count=$(docker compose exec -T postgres psql -U mystvpn -d mystvpn_bot -tAc "SELECT count(*) FROM users;" 2>/dev/null | tr -d '[:space:]')
if [ -n "$users_count" ] && [ "$users_count" -ge 0 ] 2>/dev/null; then
    echo "  $PASS Юзеров в БД: $users_count"
else
    echo "  $WARN Не удалось прочитать таблицу users"
    warnings=$((warnings + 1))
fi

paying_count=$(docker compose exec -T postgres psql -U mystvpn -d mystvpn_bot -tAc "SELECT count(*) FROM subscriptions WHERE end_date > NOW();" 2>/dev/null | tr -d '[:space:]')
if [ -n "$paying_count" ] && [ "$paying_count" -ge 0 ] 2>/dev/null; then
    echo "  $PASS Активных подписок: $paying_count"
fi

print_header "ИТОГО"

echo ""
if [ "$errors" -eq 0 ] && [ "$warnings" -eq 0 ]; then
    echo "  $PASS Всё ✓ — сервер здоров"
    exit 0
elif [ "$errors" -eq 0 ]; then
    echo "  $WARN Предупреждений: $warnings (не критично)"
    exit 0
else
    echo "  $FAIL Ошибок: $errors, предупреждений: $warnings"
    exit 1
fi
