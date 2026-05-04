# API протокола CPN

## Обзор

CPN предоставляет REST API для управления серверами, получения статистики и настройки параметров. API доступно на порту 9090 для Entry Server и порту 9091 для Control Server.

## Аутентификация

Все запросы к API требуют аутентификации с использованием Bearer токена.

### Получение токена

```bash
# Для клиента
curl -X POST http://localhost:9090/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user123",
    "password": "password"
  }'

# Ответ
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Использование токена

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  http://localhost:9090/api/stats
```

## Entry Server API

### Базовый URL

```
http://localhost:9090
```

### Статус сервера

#### Получение статуса

```
GET /api/status
```

**Ответ:**
```json
{
  "status": "online",
  "version": "1.0.0",
  "uptime": 86400,
  "current_transport": "tls",
  "connected_clients": 150,
  "active_connections": {
    "tls": 120,
    "quic": 20,
    "websocket": 10
  }
}
```

### Статистика

#### Получение общей статистики

```
GET /api/stats
```

**Ответ:**
```json
{
  "total_bytes_sent": 1073741824,
  "total_bytes_received": 2147483648,
  "total_packets_sent": 1000000,
  "total_packets_received": 2000000,
  "average_latency_ms": 45.2,
  "transport_switches": 25,
  "timeouts": 100,
  "bandwidth": {
    "in_mbps": 100.5,
    "out_mbps": 50.2
  }
}
```

#### Получение статистики по клиенту

```
GET /api/stats/client/{client_id}
```

**Параметры:**
- `client_id` (path): ID клиента

**Ответ:**
```json
{
  "client_id": "abc-123-def",
  "bytes_sent": 104857600,
  "bytes_received": 209715200,
  "packets_sent": 10000,
  "packets_received": 20000,
  "average_latency_ms": 35.5,
  "transport_switches": 5,
  "connected_since": "2026-05-01T10:00:00Z",
  "last_activity": "2026-05-02T09:30:00Z",
  "current_transport": "tls"
}
```

### Управление клиентами

#### Получение списка клиентов

```
GET /api/clients
```

**Параметры запроса:**
- `limit` (query): Количество клиентов на страницу (по умолчанию: 100)
- `offset` (query): Смещение (по умолчанию: 0)
- `status` (query): Фильтр по статусу (online, offline)

**Ответ:**
```json
{
  "clients": [
    {
      "client_id": "abc-123-def",
      "username": "user123",
      "status": "online",
      "current_transport": "tls",
      "connected_since": "2026-05-01T10:00:00Z",
      "last_activity": "2026-05-02T09:30:00Z",
      "bytes_sent": 104857600,
      "bytes_received": 209715200
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

#### Получение информации о клиенте

```
GET /api/clients/{client_id}
```

**Ответ:**
```json
{
  "client_id": "abc-123-def",
  "username": "user123",
  "email": "user@example.com",
  "status": "online",
  "current_transport": "tls",
  "profile": {
    "padding_shift": 12,
    "keepalive_interval": 2.5,
    "jitter_profile": "normal"
  },
  "connected_since": "2026-05-01T10:00:00Z",
  "last_activity": "2026-05-02T09:30:00Z",
  "bytes_sent": 104857600,
  "bytes_received": 209715200,
  "total_connections": 45
}
```

#### Отключение клиента

```
POST /api/clients/{client_id}/disconnect
```

**Ответ:**
```json
{
  "success": true,
  "message": "Client disconnected"
}
```

### Управление транспортом

#### Получение текущего транспорта

```
GET /api/transport
```

**Ответ:**
```json
{
  "current": "tls",
  "available": ["tls", "quic", "websocket"],
  "status": {
    "tls": "connected",
    "quic": "disconnected",
    "websocket": "disconnected"
  }
}
```

#### Принудительное переключение транспорта

```
POST /api/transport/switch
```

**Тело запроса:**
```json
{
  "transport": "quic"
}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Transport switched to quic",
  "previous": "tls"
}
```

### Журналы

#### Получение последних событий

```
GET /api/logs
```

**Параметры запроса:**
- `limit` (query): Количество записей (по умолчанию: 100)
- `level` (query): Уровень логирования (info, warn, error)
- `client_id` (query): Фильтр по клиенту

**Ответ:**
```json
{
  "logs": [
    {
      "timestamp": "2026-05-02T09:30:00Z",
      "level": "info",
      "client_id": "abc-123-def",
      "message": "Client connected via TLS",
      "transport": "tls"
    }
  ],
  "total": 1000
}
```

## Control Server API

### Базовый URL

```
http://localhost:9091
```

### Профили маскировки

#### Получение профиля клиента

```
GET /api/profile/{client_id}
```

**Ответ:**
```json
{
  "client_id": "abc-123-def",
  "padding_shift": 12,
  "sni_list": [
    "microsoft.com",
    "cloudflare.com",
    "yandex.ru"
  ],
  "keepalive_interval": 2.5,
  "keepalive_jitter": 1.2,
  "jitter_profile": "normal",
  "transport_priority": ["tls", "quic", "websocket"],
  "expires_at": "2026-05-03T10:00:00Z"
}
```

#### Обновление профиля

```
PUT /api/profile/{client_id}
```

**Тело запроса:**
```json
{
  "padding_shift": 15,
  "keepalive_interval": 3.0,
  "jitter_profile": "uniform"
}
```

**Ответ:**
```json
{
  "success": true,
  "profile": {
    "client_id": "abc-123-def",
    "padding_shift": 15,
    "keepalive_interval": 3.0,
    "jitter_profile": "uniform"
  }
}
```

### SNI списки

#### Получение SNI для региона

```
GET /api/sni/{region}
```

**Параметры:**
- `region` (path): Регион (ru, eu, us, asia)

**Ответ:**
```json
{
  "region": "ru",
  "sni_list": [
    "microsoft.com",
    "cloudflare.com",
    "yandex.ru",
    "sberbank.ru"
  ],
  "updated_at": "2026-05-02T08:00:00Z"
}
```

#### Обновление SNI списка

```
PUT /api/sni/{region}
```

**Тело запроса:**
```json
{
  "sni_list": [
    "microsoft.com",
    "cloudflare.com",
    "yandex.ru"
  ]
}
```

**Ответ:**
```json
{
  "success": true,
  "region": "ru",
  "count": 3
}
```

### Split Tunneling

#### Получение правил

```
GET /api/split-tunnel
```

**Ответ:**
```json
{
  "enabled": true,
  "rules": [
    {
      "type": "domain",
      "value": "sberbank.ru",
      "action": "bypass"
    },
    {
      "type": "subnet",
      "value": "10.0.0.0/8",
      "action": "bypass"
    }
  ],
  "updated_at": "2026-05-02T06:00:00Z"
}
```

#### Добавление правила

```
POST /api/split-tunnel/rules
```

**Тело запроса:**
```json
{
  "type": "domain",
  "value": "ozon.ru",
  "action": "bypass"
}
```

**Ответ:**
```json
{
  "success": true,
  "rule": {
    "id": "rule-123",
    "type": "domain",
    "value": "ozon.ru",
    "action": "bypass"
  }
}
```

#### Удаление правила

```
DELETE /api/split-tunnel/rules/{rule_id}
```

**Ответ:**
```json
{
  "success": true,
  "message": "Rule deleted"
}
```

### Мониторинг нод

#### Получение статуса нод

```
GET /api/nodes
```

**Ответ:**
```json
{
  "nodes": [
    {
      "node_id": "entry-01",
      "type": "entry",
      "region": "ru-moscow",
      "status": "online",
      "last_seen": "2026-05-02T09:30:00Z",
      "clients": 150,
      "cpu_usage": 45.2,
      "memory_usage": 62.1
    },
    {
      "node_id": "exit-01",
      "type": "exit",
      "region": "eu-frankfurt",
      "status": "online",
      "last_seen": "2026-05-02T09:29:00Z",
      "clients": 0,
      "cpu_usage": 25.5,
      "memory_usage": 40.3
    }
  ]
}
```

## WebSocket API (для реального времени)

### Подключение

```javascript
const ws = new WebSocket('ws://localhost:9090/api/ws');

ws.onopen = () => {
  // Отправка токена аутентификации
  ws.send(JSON.stringify({
    type: 'auth',
    token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### Типы сообщений

#### Статус подключения

```json
{
  "type": "status",
  "data": {
    "connected_clients": 150,
    "current_transport": "tls"
  }
}
```

#### Смена транспорта

```json
{
  "type": "transport_switch",
  "data": {
    "from": "tls",
    "to": "quic",
    "client_id": "abc-123-def"
  }
}
```

#### Новое подключение

```json
{
  "type": "client_connect",
  "data": {
    "client_id": "abc-123-def",
    "transport": "tls",
    "ip": "192.168.1.100"
  }
}
```

#### Отключение клиента

```json
{
  "type": "client_disconnect",
  "data": {
    "client_id": "abc-123-def",
    "reason": "timeout"
  }
}
```

## Коды ошибок

| Код | Описание |
|-----|----------|
| 400 | Bad Request - Некорректный запрос |
| 401 | Unauthorized - Требуется аутентификация |
| 403 | Forbidden - Недостаточно прав |
| 404 | Not Found - Ресурс не найден |
| 429 | Too Many Requests - Слишком много запросов |
| 500 | Internal Server Error - Внутренняя ошибка сервера |
| 503 | Service Unavailable - Сервис недоступен |

## Примеры использования

### Получение статистики клиента

```bash
# Получение токена
TOKEN=$(curl -s -X POST http://localhost:9090/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user123","password":"password"}' \
  | jq -r '.access_token')

# Получение статистики
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:9090/api/stats/client/abc-123-def
```

### Автоматическое переключение транспорта

```bash
#!/bin/bash
# Проверка доступности TLS и переключение при необходимости

STATUS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  http://localhost:9090/api/transport)

CURRENT=$(echo $STATUS | jq -r '.current')
TLS_STATUS=$(echo $STATUS | jq -r '.status.tls')

if [ "$TLS_STATUS" = "disconnected" ] && [ "$CURRENT" != "quic" ]; then
  curl -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"transport":"quic"}' \
    http://localhost:9090/api/transport/switch
fi
```

## Rate Limiting

API использует rate limiting для предотвращения злоупотреблений:

- **Анонимные запросы**: 10 запросов в минуту
- **Аутентифицированные пользователи**: 100 запросов в минуту
- **Администраторы**: 1000 запросов в минуту

Заголовки ответа содержат информацию о лимитах:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1717234800