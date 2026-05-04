# Архитектура протокола CPN (Cerberus)

## Общая структура

Протокол CPN реализует многослойную архитектуру, где каждый уровень отвечает за конкретную функцию:

```
┌─────────────────────────────────────────────────────────┐
│                    Приложение (Клиент)                   │
├─────────────────────────────────────────────────────────┤
│              Уровень обфускации трафика                  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ - Паддинг пакетов (0-255 байт)                    │  │
│  │ - Таиминг-обфускация (джиттер 3-18 мс)            │  │
│  │ - Keep-alive (1-4 секунды)                         │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│              Криптографическое ядро                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ - Обмен ключами: X25519 + Kyber-768                │  │
│  │ - Шифрование: AES-256-GCM                          │  │
│  │ - Nonce: 12 байт (4 случайных + 8 счетчика)        │  │
│  │ - Защита от replay: кольцевой буфер 1024 пакета   │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│              Транспортный уровень                       │
│  ┌───────────────────────────────────────────────────┐  │
│  │ 1. TCP + эмуляция TLS 1.3 (Chrome 132)            │  │
│  │ 2. WebSocket через CDN (Cloudflare)                │  │
│  │ 3. UDP + эмуляция QUIC                             │  │
│  └───────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│              Сетевой уровень                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │ - TUN-интерфейс                                    │  │
│  │ - Маршрутизация (Split Tunneling)                  │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Транспортный уровень

### 1. Первичный транспорт: TCP с эмуляцией TLS 1.3

**Цель:** Имитация обычного HTTPS-трафика для обхода базовой фильтрации.

**Процесс установки соединения:**

1. **ClientHello** (от клиента к серверу):
   - Версия: TLS 1.2 (0x0303) для совместимости
   - Случайный 32-байтный client_random
   - Session ID: 32 байта (пустые для новой сессии)
   - Набор шифров: [TLS_AES_256_GCM_SHA384, TLS_CHACHA20_POLY1305_SHA256]
   - Расширения:
     - SNI (Server Name Indication): один из доменов (microsoft.com, cloudflare.com, yandex.ru)
     - supported_groups: x25519, secp256r1
     - key_share: публичный ключ X25519 клиента
     - psk_key_exchange_modes: psk_dhe_ke
     - signature_algorithms: rsa_pss_rsae_sha256, ed25519
     - supported_versions: TLS 1.3 (0x0304)
     - padding: заполнение до 512 байт

2. **ServerHello** (от сервера к клиенту):
   - Версия: TLS 1.2 (0x0303)
   - server_random: 32 байта
   - Session ID: 32 байта
   - Шифр: TLS_AES_256_GCM_SHA384
   - key_share: публичный ключ X25519 сервера
   - selected_version: TLS 1.3 (0x0304)

3. **ChangeCipherSpec** (фиктивный):
   - Тип: 1 (change_cipher_spec)
   - Версия: TLS 1.2
   - Длина: 1 байт

4. **EncryptedExtensions**:
   - Серверные расширения (пустые для маскировки)

5. **Certificate**:
   - Фейковый сертификат для SNI-домена
   - Подписан фиктивным CA

6. **CertificateVerify**:
   - Подпись сертификата (фиктивная)

7. **Finished**:
   - Проверка целостности рукопожатия

8. **CPN Handshake** (скрытый обмен):
   - В поле session_ticket вшивается публичный ключ Kyber-768 сервера
   - Клиент подтверждает получение своим ключом Kyber-768

**После рукопожатия:**
- Все последующие пакеты шифруются AES-256-GCM
- Используется сессионный ключ, полученный из X25519 + Kyber-768
- Пакеты имеют структуру TLS Application Data

### 2. Вторичный транспорт: WebSocket через CDN

**Активация:** При 3 последовательных таймаутах TCP-транспорта.

**Процесс:**

1. Установка HTTPS-соединения к домену за Cloudflare:
   ```
   GET /chat HTTP/1.1
   Host: example.cloudflare.com
   Upgrade: websocket
   Connection: Upgrade
   Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
   Sec-WebSocket-Version: 13
   Sec-WebSocket-Extensions: permessage-deflate
   User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
   ```

2. После успешного upgrade:
   - Опкод фреймов: 0x2 (BINARY)
   - Payload: [4 байта фейкового JSON-префикса] + [зашифрованный CPN-пакет]
   - Размер: 64-4096 байт (случайный)

3. Фейковый JSON-префикс: `{"t":"message","d":`
   - Имитирует чат-сообщение или стрим

### 3. Третичный транспорт: UDP с эмуляцией QUIC

**Активация:** Параллельно с TCP, используется для низкой задержки.

**Процесс:**

1. Первый пакет (QUIC Initial):
   ```
   +------------------+---------------------+---------------------+
   | Header Form (1)  | Fixed Bit (1)       | Long Packet Type (0)|
   +------------------+---------------------+---------------------+
   | Version (0x00000001)                          | DCID Len (8)     |
   +---------------------------------------------------------------+
   | Destination Connection ID (8 случайных байт)                  |
   +---------------------------------------------------------------+
   | SCID Len (8)     | Source Connection ID (8 случайных байт)   |
   +---------------------------------------------------------------+
   | Token Length (2) | Token (зашифрованный ключ CPN)             |
   +---------------------------------------------------------------+
   | Length (2)       | Packet Number (4)    | Payload             |
   +---------------------------------------------------------------+
   ```

2. Ответ сервера: QUIC Initial Response
   - Подтверждение соединения
   - Шифрованный ответный ключ

3. После обмена:
   - Переход на чистый CPN поверх UDP
   - Больше QUIC-заголовков не используется

## Криптографическое ядро

### Обмен ключами (Handshake)

```rust
// Генерация эфемерных ключей
let client_x25519_secret = X25519Secret::generate();
let client_x25519_public = client_x25519_secret.public_key();

let client_kyber_secret = Kyber768Secret::generate();
let client_kyber_public = client_kyber_secret.public_key();

// Отправка клиентом: client_x25519_public || client_kyber_public

// Сервер генерирует свои ключи
let server_x25519_secret = X25519Secret::generate();
let server_kyber_secret = Kyber768Secret::generate();

// Вычисление shared secrets
let shared_x25519 = server_x25519_secret.diffie_hellman(&client_x25519_public);
let (shared_kyber, ciphertext) = server_kyber_secret.encapsulate(&client_kyber_public);

// Комбинирование
let combined_secret = concat(shared_x25519, shared_kyber);
let master_key = hkdf_sha512(combined_secret, salt, info);
```

### Сессионное шифрование

**Структура пакета CPN:**
```
+------------------+---------------------+---------------------+---------------------+
| Nonce (12 bytes) | Sequence (8 bytes)  | Payload (variable)  | Tag (16 bytes)      |
+------------------+---------------------+---------------------+---------------------+
```

**Nonce:**
- Байты 0-3: Случайные (getrandom)
- Байты 4-11: Монотонный счетчик (little-endian)

**Sequence:**
- 64-битный номер пакета
- Увеличивается на 1 для каждого пакета

**Payload:**
- [1 байт: длина полезных данных]
- [данные]
- [паддинг: 0-255 байт]

**Смена ключа:**
- Каждые 80 секунд ИЛИ каждые 120 МБ
- Новый обмен X25519 + Kyber-768 внутри зашифрованного канала
- Старые ключи затираются нулями

### Защита от replay-атак

```rust
struct ReplayWindow {
    bits: [AtomicU64; 16],  // 1024 бита
    lower: AtomicU64,       // Нижняя граница окна
}

impl ReplayWindow {
    fn check(&self, sequence: u64) -> bool {
        if sequence < self.lower.load(Ordering::SeqCst) {
            return false;  // Слишком старый
        }
        
        let idx = (sequence / 64) % 16;
        let bit = sequence % 64;
        let mask = 1u64 << bit;
        
        let bits = self.bits[idx as usize].load(Ordering::SeqCst);
        if (bits & mask) != 0 {
            return false;  // Уже получен
        }
        
        // Установить бит
        self.bits[idx as usize].fetch_or(mask, Ordering::SeqCst);
        true
    }
}
```

## Управление соединениями

### Entry Server

**Роли:**
- Прием входящих соединений (TCP:443, UDP:443)
- Аутентификация клиентов
- Туннелирование к Exit Server
- Replay-защита

**Архитектура:**
```rust
struct EntryServer {
    tcp_listener: TcpListener,
    udp_socket: UdpSocket,
    exit_connections: HashMap<ClientId, ExitConnection>,
    replay_windows: HashMap<ClientId, ReplayWindow>,
}
```

### Exit Server

**Роли:**
- Прием соединений только от Entry Server
- Проксирование во внешний интернет
- NAT traversal

**Особенности:**
- Не хранит ключи клиентов
- Не видит реальные IP клиентов
- Только маршрутизация трафика

### Control Server

**API Endpoints:**
- `GET /profile/{client_id}` — получить профиль маскировки
- `GET /sni/{region}` — список SNI для региона
- `GET /split-tunnel` — правила split tunneling
- `POST /stats` — статистика использования

## Split Tunneling

**Реализация:**

```rust
struct SplitTunnel {
    // Российские домены
    ru_domains: HashSet<String>,
    // IP-диапазоны
    ru_subnets: Vec<IpNetwork>,
}

impl SplitTunnel {
    fn should_bypass(&self, dest: &SocketAddr) -> bool {
        // Проверка по IP
        for subnet in &self.ru_subnets {
            if subnet.contains(dest.ip()) {
                return true;
            }
        }
        
        // Проверка по домену (если доступно)
        false
    }
}
```

**Правила маршрутизации:**
- Трафик к RU-доменам → системный роутинг
- Остальной трафик → CPN-туннель
- Обновление списков: каждые 12 часов

## Профили маскировки

**Структура профиля:**
```json
{
  "client_id": "uuid",
  "padding_shift": 12,
  "sni_list": ["microsoft.com", "cloudflare.com"],
  "keepalive_interval": 2.5,
  "keepalive_jitter": 1.2,
  "jitter_profile": "normal",
  "transport_priority": ["tls", "quic", "websocket"]
}
```

**Генерация:**
- Сервер выдает уникальный профиль при первой аутентификации
- Хранится в зашифрованном виде на клиенте
- Обновляется раз в 24 часа

## Сетевая архитектура

```
         
  Client       Entry Server       Exit Server    Internet  
         
                                                         
  TUN      TLS 1.3              Internal VPN              
  +--+   +---------+          +---------+          +---------+
  |IP|-->| CPN TLS |--------->| CPN TLS |--------->|  NAT    |--> Target
  +--+   +---------+          +---------+          +---------+
  |IP|-->| QUIC    |          |         |          |         |
  +--+   +---------+          +---------+          +---------+
  |IP|-->| WS      |          |         |          |         |
  +--+   +---------+          +---------+          +---------+
```

## Обработка пакетов

### Исходящий трафик (Client → Internet):

1. Приложение отправляет пакет в TUN-интерфейс
2. Split Tunneling проверка:
   - Если RU-трафик → отправить напрямую
   - Иначе → продолжить
3. Добавить паддинг (случайная длина 0-255)
4. Зашифровать AES-256-GCM
5. Добавить nonce и sequence
6. Выбрать транспорт (по приоритету)
7. Отправить на Entry Server
8. Entry Server пересылает на Exit Server
9. Exit Server отправляет в Internet

### Входящий трафик (Internet → Client):

1. Internet → Exit Server
2. Exit Server → Entry Server
3. Entry Server → выбранный транспорт
4. Клиент получает пакет
5. Дешифровать AES-256-GCM
6. Проверить sequence (replay защита)
7. Убрать паддинг
8. Отправить в TUN-интерфейс
9. Приложение получает данные

## Обработка ошибок

### Таймауты транспорта

```rust
enum TransportError {
    Timeout,
    ConnectionReset,
    TlsError,
    QuicError,
    WebSocketError,
}

impl TransportManager {
    fn handle_error(&mut self, error: TransportError) {
        self.consecutive_timeouts += 1;
        
        if self.consecutive_timeouts >= 3 {
            self.switch_to_next_transport();
            self.consecutive_timeouts = 0;
        }
    }
    
    fn switch_to_next_transport(&mut self) {
        match self.current_transport {
            Transport::Tls => self.current_transport = Transport::Quic,
            Transport::Quic => self.current_transport = Transport::WebSocket,
            Transport::WebSocket => self.current_transport = Transport::Tls,
        }
    }
}
```

### Переподключение

- Экспоненциальный бэкофф (1s, 2s, 4s, 8s...)
- Максимум 5 попыток
- После 5 неудачи → ожидание 60 секунд
- Сброс состояния при успешном подключении

## Метрики и мониторинг

**Собираемые метрики:**
- Скорость передачи (входящая/исходящая)
- Текущий транспорт
- Количество переключений транспорта
- Задержка (latency)
- Количество dropped пакетов
- Использование CPU/памяти

**Экспорт:**
- Локальная панель: http://127.0.0.1:8080
- Prometheus endpoint: http://127.0.0.1:9090/metrics