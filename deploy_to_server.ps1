# MystVPN — Автоматический деплой на сервер
# Просто запусти этот файл в PowerShell

$SERVER_IP = "77.110.96.77"
$SERVER_USER = "root"
$SERVER_PASS = "XfFPiCsY4mtl"
$LOCAL_PATH = Split-Path -Parent $MyInvocation.MyCommand.Path
$REMOTE_PATH = "/root/MystBot"

Write-Host "🚀 MystVPN Deploy" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Устанавливаем plink/pscp если нет (через winget или chocolatey)
$scpExists = Get-Command scp -ErrorAction SilentlyContinue
$sshExists = Get-Command ssh -ErrorAction SilentlyContinue

if (-not $scpExists -or -not $sshExists) {
    Write-Host "❌ SSH/SCP не найдены. Обновите Windows или установите OpenSSH." -ForegroundColor Red
    exit 1
}

Write-Host "📦 Шаг 1/3: Загружаем файлы на сервер..." -ForegroundColor Yellow
Write-Host "   (введи пароль: $SERVER_PASS)" -ForegroundColor Gray

# Загружаем папку на сервер
$env:SSHPASS = $SERVER_PASS
scp -o StrictHostKeyChecking=no -r "$LOCAL_PATH" "${SERVER_USER}@${SERVER_IP}:/root/"

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка загрузки файлов. Введи пароль вручную когда попросит." -ForegroundColor Red
}

Write-Host ""
Write-Host "✅ Файлы загружены!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Шаг 2/3: Подключаемся к серверу и запускаем бота..." -ForegroundColor Yellow
Write-Host "   (введи пароль ещё раз: $SERVER_PASS)" -ForegroundColor Gray
Write-Host ""

# SSH команда для запуска на сервере
$SSH_COMMANDS = @"
cd /root/MystBot
echo "=== Запуск docker compose ==="
docker compose pull postgres redis 2>/dev/null || true
docker compose up -d --build
sleep 8
echo "=== Миграции БД ==="
docker compose exec -T bot python migrate.py 2>/dev/null || echo "Миграции запустятся после старта"
echo "=== Статус контейнеров ==="
docker compose ps
echo ""
echo "✅ Готово! Бот запущен."
"@

ssh -o StrictHostKeyChecking=no "${SERVER_USER}@${SERVER_IP}" $SSH_COMMANDS

Write-Host ""
Write-Host "🎉 Деплой завершён!" -ForegroundColor Green
Write-Host "Логи бота: ssh root@$SERVER_IP 'cd /root/MystBot && docker compose logs -f bot'" -ForegroundColor Cyan
Write-Host ""
Read-Host "Нажми Enter для выхода"
