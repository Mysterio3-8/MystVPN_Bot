# Сборка CPN Protocol

## Требования

- Rust 1.78+
- OpenSSL (для TLS)
- CMake (для некоторых зависимостей)

## Сборка

### Windows (PowerShell)

```powershell
# Установить переменные окружения
$env:OPENSSL_DIR = "C:\OpenSSL-Win64"
$env:OPENSSL_LIB_DIR = "$env:OPENSSL_DIR\lib"
$env:OPENSSL_INCLUDE_DIR = "$env:OPENSSL_DIR\include"

# Сборка
cargo build --release
```

### Linux/macOS

```bash
# Сборка
cargo build --release

# Для полной оптимизации
cargo build --release --locked
```

## Запуск тестов

```bash
cargo test --all
```

## Структура бинарных файлов

После сборки в `target/release/`:
- `cpn-client` — клиентское приложение
- `cpn-entry-server` — entry сервер
- `cpn-exit-server` — exit сервер
- `cpn-control-server` — control сервер

## Docker

```bash
docker build -t cpn-protocol .