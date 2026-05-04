# Транспортный уровень CPN

## Обзор

Транспортный уровень отвечает за маскировку трафика под легитимные протоколы. Реализованы три уровня транспорта с автоматическим переключением при детекте помех.

## Первичный транспорт: TCP с эмуляцией TLS 1.3

### Структура ClientHello

```rust
struct TlsClientHello {
    record_layer: RecordLayer,
    handshake: HandshakeProtocol,
}

struct RecordLayer {
    content_type: u8,      // 0x16 (Handshake)
    version: [u8; 2],      // 0x03, 0x03 (TLS 1.2)
    length: [u8; 2],       // Длина сообщения
}

struct HandshakeProtocol {
    msg_type: u8,          // 0x01 (ClientHello)
    length: [u8; 3],       // Длина (24 байта)
    version: [u8; 2],      // 0x03, 0x03 (TLS 1.2)
    random: [u8; 32],      // Случайные байты
    session_id: [u8; 32],  // ID сессии (пустой для новой)
    cipher_suites: Vec<u8>,// Набор шифров
    compression: u8,       // Метод сжатия (0 - нет)
    extensions: Vec<Extension>,
}
```

### Набор шифров (Cipher Suites)

```rust
const TLS_CIPHER_SUITES: &[u16] = &[
    0x1302, // TLS_AES_256_GCM_SHA384
    0x1303, // TLS_CHACHA20_POLY1305_SHA256
    0x1301, // TLS_AES_128_GCM_SHA256
    0xCCA8, // TLS_CHACHA20_POLY1305_SHA256 (RFC8446)
    0xCCA9, // TLS_AES_128_GCM_SHA256 (RFC8446)
];
```

### Расширения TLS

#### 1. Server Name Indication (SNI)

```rust
struct SniExtension {
    extension_type: u16,  // 0x0000
    extension_data: Vec<u8>,
}

impl SniExtension {
    fn encode(server_name: &str) -> Vec<u8> {
        let mut data = Vec::new();
        
        // Длина списка серверов (2 байта)
        data.extend_from_slice(&(server_name.len() as u16 + 3).to_be_bytes());
        
        // Тип имени (0 - hostname)
        data.push(0x00);
        
        // Длина имени
        data.extend_from_slice(&(server_name.len() as u16).to_be_bytes());
        
        // Имя сервера
        data.extend_from_slice(server_name.as_bytes());
        
        data
    }
}
```

#### 2. Supported Groups

```rust
const SUPPORTED_GROUPS: &[u8] = &[
    0x00, 0x17, // x25519
    0x00, 0x1d, // x448
    0x00, 0x18, // secp256r1
    0x00, 0x19, // secp384r1
    0x00, 0x1a, // secp521r1
];
```

#### 3. Key Share

```rust
struct KeyShareExtension {
    extension_type: u16,  // 0x0033
    client_shares: Vec<KeyShareEntry>,
}

struct KeyShareEntry {
    group: u16,           // Группа (x25519 = 0x0017)
    key_exchange: Vec<u8>, // Публичный ключ (32 байта для x25519)
}
```

#### 4. Supported Versions

```rust
const SUPPORTED_VERSIONS: &[u8] = &[
    0x0a,                   // Длина (10 байт)
    0x03, 0x04,             // TLS 1.3 (0x0304)
    0x03, 0x03,             // TLS 1.2 (0x0303)
    0x03, 0x02,             // TLS 1.1 (0x0302)
    0x03, 0x01,             // TLS 1.0 (0x0301)
];
```

#### 5. Padding

```rust
fn generate_padding() -> Vec<u8> {
    // Заполняем до 512 байт
    let mut padding = vec![0u8; 512];
    rand::fill(&mut padding);
    padding
}
```

### Полный ClientHello

```rust
fn build_client_hello(sni: &str, x25519_public: &[u8; 32]) -> Vec<u8> {
    let mut extensions = Vec::new();
    
    // SNI
    extensions.extend_from_slice(&[0x00, 0x00]); // Extension type: SNI
    let sni_data = SniExtension::encode(sni);
    extensions.extend_from_slice(&(sni_data.len() as u16).to_be_bytes());
    extensions.extend_from_slice(&sni_data);
    
    // Supported Groups
    extensions.extend_from_slice(&[0x00, 0x0a]); // Extension type: supported_groups
    extensions.extend_from_slice(&[0x00, 0x08]); // Длина
    extensions.extend_from_slice(&[0x00, 0x06]); // Длина списка
    extensions.extend_from_slice(SUPPORTED_GROUPS);
    
    // Key Share
    extensions.extend_from_slice(&[0x00, 0x33]); // Extension type: key_share
    let key_share_data = build_key_share(x25519_public);
    extensions.extend_from_slice(&(key_share_data.len() as u16).to_be_bytes());
    extensions.extend_from_slice(&key_share_data);
    
    // Supported Versions
    extensions.extend_from_slice(&[0x00, 0x2b]); // Extension type: supported_versions
    extensions.extend_from_slice(&[0x00, 0x0b]); // Длина
    extensions.extend_from_slice(SUPPORTED_VERSIONS);
    
    // Padding
    extensions.extend_from_slice(&[0x00, 0x15]); // Extension type: padding
    let padding = generate_padding();
    extensions.extend_from_slice(&(padding.len() as u16).to_be_bytes());
    extensions.extend_from_slice(&padding);
    
    // Собираем ClientHello
    let mut client_hello = Vec::new();
    
    // Record Layer
    client_hello.push(0x16); // Handshake
    client_hello.extend_from_slice(&[0x03, 0x03]); // TLS 1.2
    
    // Handshake Protocol
    client_hello.push(0x01); // ClientHello
    
    // Длина всего сообщения (будет заполнена позже)
    let hello_start = client_hello.len();
    client_hello.extend_from_slice(&[0x00, 0x00, 0x00]);
    
    // Версия
    client_hello.extend_from_slice(&[0x03, 0x03]);
    
    // Random
    let mut random = [0u8; 32];
    rand::fill(&mut random);
    client_hello.extend_from_slice(&random);
    
    // Session ID (пустой)
    client_hello.push(0x00);
    
    // Cipher Suites
    client_hello.extend_from_slice(&[0x00, 0x0a]); // Длина
    for &suite in TLS_CIPHER_SUITES {
        client_hello.extend_from_slice(&suite.to_be_bytes());
    }
    
    // Compression
    client_hello.push(0x01); // Длина
    client_hello.push(0x00); // Нет сжатия
    
    // Extensions
    client_hello.extend_from_slice(&(extensions.len() as u16).to_be_bytes());
    client_hello.extend_from_slice(&extensions);
    
    // Заполняем длину
    let total_len = client_hello.len() - hello_start - 3;
    client_hello[hello_start..hello_start + 3].copy_from_slice(
        &(total_len as u32).to_be_bytes()[1..]
    );
    
    // Record Layer length
    let record_len = client_hello.len() - 5;
    client_hello[3..5].copy_from_slice(&(record_len as u16).to_be_bytes());
    
    client_hello
}
```

### ServerHello

```rust
fn parse_server_hello(data: &[u8]) -> Result<TlsServerHello, TlsError> {
    let mut offset = 0;
    
    // Проверяем тип сообщения
    if data[offset] != 0x16 { // Handshake
        return Err(TlsError::InvalidMessageType);
    }
    offset += 1;
    
    // Проверяем версию
    if data[offset..offset + 2] != [0x03, 0x03] {
        return Err(TlsError::InvalidVersion);
    }
    offset += 2;
    
    // Длина
    let length = u16::from_be_bytes([data[offset], data[offset + 1]]) as usize;
    offset += 2;
    
    // Проверяем тип рукопожатия
    if data[offset] != 0x02 { // ServerHello
        return Err(TlsError::InvalidHandshakeType);
    }
    offset += 1;
    
    // Длина рукопожатия
    let handshake_len = u24::from_be_bytes([data[offset], data[offset + 1], data[offset + 2]]);
    offset += 3;
    
    // Версия
    if data[offset..offset + 2] != [0x03, 0x03] {
        return Err(TlsError::InvalidVersion);
    }
    offset += 2;
    
    // Random
    let mut random = [0u8; 32];
    random.copy_from_slice(&data[offset..offset + 32]);
    offset += 32;
    
    // Session ID
    let session_id_len = data[offset] as usize;
    offset += 1;
    let session_id = &data[offset..offset + session_id_len];
    offset += session_id_len;
    
    // Cipher Suite
    let cipher_suite = u16::from_be_bytes([data[offset], data[offset + 1]]);
    offset += 2;
    
    // Compression
    let compression = data[offset];
    offset += 1;
    
    // Extensions
    let extensions_len = u16::from_be_bytes([data[offset], data[offset + 1]]) as usize;
    offset += 2;
    
    let extensions = parse_extensions(&data[offset..offset + extensions_len])?;
    
    Ok(TlsServerHello {
        random,
        session_id: session_id.to_vec(),
        cipher_suite,
        compression,
        extensions,
    })
}
```

## Вторичный транспорт: WebSocket через CDN

### Установка соединения

```rust
struct WebSocketTransport {
    stream: TcpStream,
    tls_stream: TlsStream<TcpStream>,
    websocket: WebSocket<MaybeTlsStream<TcpStream>>,
    frame_size: usize,
}

impl WebSocketTransport {
    async fn connect(url: &str) -> Result<Self, TransportError> {
        // Парсим URL
        let url = Url::parse(url)?;
        let host = url.host_str().ok_or(TransportError::InvalidUrl)?;
        let port = url.port().unwrap_or(443);
        
        // Подключаемся
        let stream = TcpStream::connect((host, port)).await?;
        
        // Настраиваем TLS
        let connector = TlsConnector::from(Arc::new(
            native_tls::TlsConnector::builder().build()?
        ));
        
        let tls_stream = connector.connect(host, stream).await?;
        
        // WebSocket handshake
        let request = Request::builder()
            .method("GET")
            .uri(url.path())
            .header("Host", host)
            .header("Upgrade", "websocket")
            .header("Connection", "Upgrade")
            .header("Sec-WebSocket-Key", generate_websocket_key())
            .header("Sec-WebSocket-Version", "13")
            .header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)...")
            .body(())?;
        
        let (websocket, _) = tokio_tungstenite::client_async(request, tls_stream).await?;
        
        Ok(Self {
            stream,
            tls_stream,
            websocket,
            frame_size: 1024, // Начальный размер
        })
    }
}
```

### Отправка фрейма

```rust
impl WebSocketTransport {
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        // Добавляем фейковый JSON-префикс
        let prefix = b"{\"t\":\"message\",\"d\":";
        let mut frame_data = Vec::with_capacity(prefix.len() + data.len());
        frame_data.extend_from_slice(prefix);
        frame_data.extend_from_slice(data);
        
        // Случайный размер фрейма (64-4096 байт)
        let target_size = rand::random::<usize>() % (4096 - 64) + 64;
        
        // Если данных меньше целевого размера, добавляем паддинг
        if frame_data.len() < target_size {
            let padding = target_size - frame_data.len();
            frame_data.resize(frame_data.len() + padding, 0);
        }
        
        // Отправляем бинарный фрейм
        let message = Message::Binary(frame_data);
        self.websocket.send(message).await?;
        
        Ok(())
    }
    
    async fn recv(&mut self) -> Result<Vec<u8>, TransportError> {
        let message = self.websocket.next().await
            .ok_or(TransportError::ConnectionClosed)??;
        
        match message {
            Message::Binary(data) => {
                // Убираем фейковый префикс
                if data.len() > 15 && &data[0..15] == b"{\"t\":\"message\",\"d\":" {
                    // Ищем конец JSON (на самом деле это просто префикс)
                    // Возвращаем остаток данных
                    Ok(data[15..].to_vec())
                } else {
                    Err(TransportError::InvalidFrame)
                }
            }
            Message::Close(_) => Err(TransportError::ConnectionClosed),
            _ => Err(TransportError::InvalidFrame),
        }
    }
}
```

## Третичный транспорт: UDP с эмуляцией QUIC

### QUIC Initial Packet

```rust
struct QuicInitialPacket {
    header: QuicHeader,
    token: Vec<u8>,
    payload: Vec<u8>,
}

struct QuicHeader {
    flags: u8,              // Флаги
    version: u32,           // Версия (0x00000001)
    dcid: [u8; 8],          // Destination Connection ID
    scid: [u8; 8],          // Source Connection ID
    token_length: u16,      // Длина токена
}

impl QuicHeader {
    fn encode(&self) -> Vec<u8> {
        let mut data = Vec::new();
        
        // Флаги: Long Header (1), Fixed Bit (1), Packet Type (0 - Initial)
        data.push(0xc0 | 0x00);
        
        // Версия
        data.extend_from_slice(&self.version.to_be_bytes());
        
        // DCID Length
        data.push(self.dcid.len() as u8);
        
        // DCID
        data.extend_from_slice(&self.dcid);
        
        // SCID Length
        data.push(self.scid.len() as u8);
        
        // SCID
        data.extend_from_slice(&self.scid);
        
        // Token Length
        data.extend_from_slice(&self.token_length.to_be_bytes());
        
        // Token
        data.extend_from_slice(&self.token);
        
        data
    }
}
```

### Формирование Initial Packet

```rust
fn build_quic_initial(
    session_key: &[u8],
    connection_id: [u8; 8],
) -> Result<Vec<u8>, TransportError> {
    // Генерируем случайные ID
    let mut rng = rand::thread_rng();
    let dcid: [u8; 8] = rng.gen();
    let scid: [u8; 8] = rng.gen();
    
    // Шифруем ключ сессии для токена
    let token = encrypt_session_key(session_key, &dcid)?;
    
    let header = QuicHeader {
        flags: 0xc0, // Long Header + Fixed Bit + Initial
        version: 0x00000001, // QUIC version 1
        dcid,
        scid,
        token_length: token.len() as u16,
    };
    
    let mut packet = header.encode();
    
    // Length (будет заполнено позже)
    packet.extend_from_slice(&[0x00, 0x00]);
    
    // Payload (Initial криптографический обмен)
    let payload = build_initial_crypto_payload()?;
    packet.extend_from_slice(&payload);
    
    // Заполняем длину
    let length = packet.len() - header.encode().len() - 2;
    let len_pos = header.encode().len();
    packet[len_pos..len_pos + 2].copy_from_slice(&(length as u16).to_be_bytes());
    
    Ok(packet)
}
```

### Обработка QUIC пакетов

```rust
struct QuicTransport {
    socket: UdpSocket,
    connection_id: [u8; 8],
    peer_addr: SocketAddr,
    state: QuicState,
}

enum QuicState {
    Initial,
    Handshaking,
    Connected,
}

impl QuicTransport {
    async fn new() -> Result<Self, TransportError> {
        let socket = UdpSocket::bind("0.0.0.0:0").await?;
        
        Ok(Self {
            socket,
            connection_id: rand::random(),
            peer_addr: "0.0.0.0:0".parse().unwrap(),
            state: QuicState::Initial,
        })
    }
    
    async fn connect(&mut self, addr: SocketAddr) -> Result<(), TransportError> {
        self.peer_addr = addr;
        
        // Отправляем Initial Packet
        let initial_packet = build_quic_initial(
            &self.session_key,
            self.connection_id,
        )?;
        
        self.socket.send_to(&initial_packet, addr).await?;
        self.state = QuicState::Handshaking;
        
        // Ждем ответ
        let mut buf = [0u8; 1500];
        let (size, _) = self.socket.recv_from(&mut buf).await?;
        
        // Парсим ответ
        self.handle_initial_response(&buf[..size])?;
        
        self.state = QuicState::Connected;
        
        Ok(())
    }
    
    fn handle_initial_response(&mut self, data: &[u8]) -> Result<(), TransportError> {
        // Проверяем флаги
        if data.is_empty() || (data[0] & 0xc0) != 0xc0 {
            return Err(TransportError::InvalidPacket);
        }
        
        // Проверяем тип пакета (должен быть Initial или Handshake)
        let packet_type = data[0] & 0x30;
        if packet_type != 0x00 && packet_type != 0x20 {
            return Err(TransportError::InvalidPacket);
        }
        
        // Извлекаем ключ сессии из токена
        self.extract_session_key(data)?;
        
        Ok(())
    }
}
```

### Переход на чистый CPN

После успешного обмена QUIC-пакетами, обе стороны переходят на чистый CPN поверх UDP:

```rust
impl QuicTransport {
    async fn upgrade_to_cpn(&mut self) -> Result<CpnUdpTransport, TransportError> {
        // Отправляем финальный пакет подтверждения
        let confirm_packet = self.build_confirmation_packet()?;
        self.socket.send_to(&confirm_packet, self.peer_addr).await?;
        
        // Создаем CPN UDP транспорт
        let cpn_transport = CpnUdpTransport::new(
            self.socket.try_clone()?,
            self.peer_addr,
            self.session_key.clone(),
        );
        
        Ok(cpn_transport)
    }
}

struct CpnUdpTransport {
    socket: UdpSocket,
    peer_addr: SocketAddr,
    cipher: Aes256Gcm,
    nonce_gen: NonceGenerator,
    sequence: AtomicU64,
}

impl CpnUdpTransport {
    async fn send(&self, data: &[u8]) -> Result<(), TransportError> {
        let sequence = self.sequence.fetch_add(1, Ordering::SeqCst);
        let nonce = self.nonce_gen.generate();
        
        // Шифруем
        let packet = self.encrypt_packet(data, &nonce, sequence)?;
        
        // Отправляем
        self.socket.send_to(&packet, self.peer_addr).await?;
        
        Ok(())
    }
}
```

## Автоматическое переключение транспорта

### Менеджер транспорта

```rust
struct TransportManager {
    current: TransportType,
    tls: Option<TlsTransport>,
    websocket: Option<WebSocketTransport>,
    quic: Option<QuicTransport>,
    consecutive_timeouts: u32,
    last_switch: Instant,
}

enum TransportType {
    Tls,
    WebSocket,
    Quic,
}

impl TransportManager {
    async fn send(&mut self, data: &[u8]) -> Result<(), TransportError> {
        let result = match self.current {
            TransportType::Tls => {
                if let Some(tls) = &mut self.tls {
                    tls.send(data).await
                } else {
                    Err(TransportError::NotInitialized)
                }
            }
            TransportType::WebSocket => {
                if let Some(ws) = &mut self.websocket {
                    ws.send(data).await
                } else {
                    Err(TransportError::NotInitialized)
                }
            }
            TransportType::Quic => {
                if let Some(quic) = &mut self.quic {
                    quic.send(data).await
                } else {
                    Err(TransportError::NotInitialized)
                }
            }
        };
        
        match result {
            Ok(()) => {
                self.consecutive_timeouts = 0;
                Ok(())
            }
            Err(TransportError::Timeout) => {
                self.consecutive_timeouts += 1;
                if self.consecutive_timeouts >= 3 {
                    self.switch_transport().await?;
                }
                Err(TransportError::Timeout)
            }
            Err(e) => Err(e),
        }
    }
    
    async fn switch_transport(&mut self) -> Result<(), TransportError> {
        let new_transport = match self.current {
            TransportType::Tls => {
                println!("Switching to QUIC transport");
                TransportType::Quic
            }
            TransportType::Quic => {
                println!("Switching to WebSocket transport");
                TransportType::WebSocket
            }
            TransportType::WebSocket => {
                println!("Switching to TLS transport");
                TransportType::Tls
            }
        };
        
        // Инициализируем новый транспорт
        self.initialize_transport(new_transport).await?;
        self.current = new_transport;
        self.consecutive_timeouts = 0;
        self.last_switch = Instant::now();
        
        Ok(())
    }
    
    async fn initialize_transport(
        &mut self,
        transport: TransportType,
    ) -> Result<(), TransportError> {
        match transport {
            TransportType::Tls => {
                if self.tls.is_none() {
                    let tls = TlsTransport::connect("entry-server:443").await?;
                    self.tls = Some(tls);
                }
            }
            TransportType::WebSocket => {
                if self.websocket.is_none() {
                    let ws = WebSocketTransport::connect(
                        "wss://cdn.example.com/chat"
                    ).await?;
                    self.websocket = Some(ws);
                }
            }
            TransportType::Quic => {
                if self.quic.is_none() {
                    let mut quic = QuicTransport::new().await?;
                    quic.connect("entry-server:443".parse()?).await?;
                    self.quic = Some(quic);
                }
            }
        }
        
        Ok(())
    }
}
```

### Обратное переключение

```rust
impl TransportManager {
    fn check_revert(&mut self) {
        // Если прошло более 30 секунд с последнего переключения
        // и текущий транспорт не TLS, проверяем доступность TLS
        if self.last_switch.elapsed() > Duration::from_secs(30)
            && !matches!(self.current, TransportType::Tls)
        {
            // Пробуем переключиться обратно на TLS
            if let Ok(()) = self.try_revert_to_tls() {
                println!("Reverted to TLS transport");
            }
        }
    }
    
    async fn try_revert_to_tls(&mut self) -> Result<(), TransportError> {
        // Проверяем доступность TLS
        if let Some(tls) = &mut self.tls {
            if tls.ping().await.is_ok() {
                self.current = TransportType::Tls;
                self.consecutive_timeouts = 0;
                return Ok(());
            }
        }
        
        Err(TransportError::TransportUnavailable)
    }
}
```

## Метрики транспорта

```rust
struct TransportMetrics {
    bytes_sent: AtomicU64,
    bytes_received: AtomicU64,
    packets_sent: AtomicU64,
    packets_received: AtomicU64,
    timeouts: AtomicU64,
    switches: AtomicU64,
    current_transport: TransportType,
    latency: AtomicU64, // в микросекундах
}

impl TransportMetrics {
    fn record_send(&self, bytes: usize) {
        self.bytes_sent.fetch_add(bytes as u64, Ordering::Relaxed);
        self.packets_sent.fetch_add(1, Ordering::Relaxed);
    }
    
    fn record_receive(&self, bytes: usize) {
        self.bytes_received.fetch_add(bytes as u64, Ordering::Relaxed);
        self.packets_received.fetch_add(1, Ordering::Relaxed);
    }
    
    fn record_timeout(&self) {
        self.timeouts.fetch_add(1, Ordering::Relaxed);
    }
    
    fn record_switch(&self) {
        self.switches.fetch_add(1, Ordering::Relaxed);
    }
    
    fn update_latency(&self, latency_us: u64) {
        self.latency.store(latency_us, Ordering::Relaxed);
    }
}