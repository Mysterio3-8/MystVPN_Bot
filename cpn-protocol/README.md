# CPN Protocol (Cerberus)

Защищенный транспортный протокол с многослойной маскировкой трафика и гибридной пост-квантовой криптографией.

## Особенности

- **Гибридная пост-квантовая криптография**: X25519 ECDH + Kyber-768 KEM
- **Многослойная маскировка**: TLS 1.3 → WebSocket → QUIC
- **Защита от анализа**: паддинг, джиттер, уникальные профили
- **Forward Secrecy**: гарантирована для каждой сессии

## Структура проекта

```
cpn/
├── crates/
│   ├── cpn-protocol/     # Ядро протокола (crypto, packet, types)
│   ├── cpn-core/         # Основная функциональность
│   ├── cpn-client/       # Клиентская библиотека
│   └── cpn-server/       # Серверные компоненты
├── flutter/              # Мобильное приложение
└── docs/                 # Документация
```

## Быстрый старт

```bash
# Сборка
cargo build --release

# Запуск клиента
cargo run --release -- connect --config config.toml

# Генерация конфигурации
cargo run --release -- gen-config --output config.toml
```

## Документация

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) — архитектура протокола
- [CRYPTOGRAPHY.md](docs/CRYPTOGRAPHY.md) — криптографическое ядро
- [TRANSPORT.md](docs/TRANSPORT.md) — транспортные уровни
- [API.md](docs/API.md) — REST API

## Лицензия

MIT