# Криптографическое ядро CPN

## Обзор

Криптографическое ядро CPN реализует гибридный подход к защите данных, комбинируя классическую эллиптическую криптографию с пост-квантовыми алгоритмами для обеспечения стойкости к будущим угрозам.

## Гибридный обмен ключами

### Алгоритмы

- **X25519**: Эллиптическая кривая для эфемерного обмена ключами
- **Kyber-768**: Пост-квантовый алгоритм инкапсуляции ключей (KEM)

### Процесс обмена

#### 1. Генерация ключевых пар

```rust
use ring::agreement;
use pqcrypto_kyber::kyber768;

// Генерация X25519 ключей
let x25519_secret = agreement::EphemeralPrivateKey::generate(
    &agreement::X25519,
    rand::SystemRandom::new()
)?;
let x25519_public = x25519_secret.compute_public_key()?;

// Генерация Kyber-768 ключей
let (kyber_public, kyber_secret) = kyber768::keypair();
```

#### 2. Инкапсуляция (Клиент → Сервер)

```rust
// Клиент генерирует ciphertext и shared secret
let (ciphertext, client_shared_kyber) = kyber768::encapsulate(&server_kyber_public);

// Клиент вычисляет X25519 shared secret
let client_shared_x25519 = x25519_secret.agree(&server_x25519_public)?;

// Комбинирование
let combined_secret = [
    client_shared_x25519.as_ref(),
    client_shared_kyber.as_ref()
].concat();
```

#### 3. Декапсуляция (Сервер)

```rust
// Сервер извлекает shared secret из ciphertext
let server_shared_kyber = kyber768::decapsulate(&ciphertext, &server_kyber_secret);

// Сервер вычисляет X25519 shared secret
let server_shared_x25519 = server_x25519_secret.agree(&client_x25519_public)?;

// Комбинирование
let combined_secret = [
    server_shared_x25519.as_ref(),
    server_shared_kyber.as_ref()
].concat();
```

#### 4. Производная ключа (HKDF)

```rust
use ring::hkdf;

// Используем HKDF-SHA512 для получения мастер-ключа
let salt = hkdf::Salt::new(hkdf::HKDF_SHA512, &[]);
let prk = salt.extract(&combined_secret);

let master_key = prk.expand(
    &["CPN master key".as_bytes()],
    hkdf::KeyType::HmacSha512
)?;
```

## Сессионное шифрование

### AES-256-GCM

**Параметры:**
- Алгоритм: AES-256 в режиме GCM
- Размер тега: 128 бит (16 байт)
- Размер nonce: 96 бит (12 байт)

### Производная ключа сессии

```rust
// Каждая сессия имеет уникальный session_id (8 случайных байт)
let session_id: [u8; 8] = rand::random();

// Производим ключ сессии из мастер-ключа
let salt = hkdf::Salt::new(hkdf::HKDF_SHA512, &session_id);
let prk = salt.extract(&master_key);

let session_key = prk.expand(
    &["CPN session key".as_bytes()],
    hkdf::KeyType::Aes256Gcm
)?;
```

### Шифрование пакета

```rust
use aes_gcm::{Aes256Gcm, Key, Nonce};
use aes_gcm::aead::{Aead, NewAead, Payload};

struct CpnPacket {
    nonce: [u8; 12],
    sequence: u64,
    payload: Vec<u8>,
}

impl CpnPacket {
    fn encrypt(&self, key: &Key<Aes256Gcm>) -> Vec<u8> {
        let cipher = Aes256Gcm::new(key);
        let nonce = Nonce::from_slice(&self.nonce);
        
        // Формируем payload: [длина данных (1 байт)] + [данные] + [паддинг]
        let mut plaintext = Vec::new();
        plaintext.push(self.payload.len() as u8);
        plaintext.extend_from_slice(&self.payload);
        
        // Добавляем случайный паддинг (0-255 байт)
        let padding_len = rand::random::<u8>();
        plaintext.resize(plaintext.len() + padding_len as usize, 0);
        
        // Шифруем
        let payload = Payload {
            msg: &plaintext,
            aad: &self.sequence.to_le_bytes(),
        };
        
        let mut ciphertext = cipher.encrypt(nonce, payload).unwrap();
        
        // Формируем финальный пакет: [nonce (12)] + [sequence (8)] + [ciphertext]
        let mut packet = Vec::new();
        packet.extend_from_slice(&self.nonce);
        packet.extend_from_slice(&self.sequence.to_le_bytes());
        packet.extend_from_slice(&ciphertext);
        
        packet
    }
}
```

### Дешифрование пакета

```rust
impl CpnPacket {
    fn decrypt(packet: &[u8], key: &Key<Aes256Gcm>) -> Result<Self, DecryptError> {
        let cipher = Aes256Gcm::new(key);
        
        // Извлекаем nonce и sequence
        let nonce = <[u8; 12]>::try_from(&packet[0..12])?;
        let sequence = u64::from_le_bytes(<[u8; 8]>::try_from(&packet[12..20])?);
        let ciphertext = &packet[20..];
        
        let nonce = Nonce::from_slice(&nonce);
        
        // Дешифруем
        let payload = Payload {
            msg: ciphertext,
            aad: &sequence.to_le_bytes(),
        };
        
        let plaintext = cipher.decrypt(nonce, payload)
            .map_err(|_| DecryptError::AuthenticationFailed)?;
        
        // Извлекаем длину данных
        let data_len = plaintext[0] as usize;
        
        // Проверяем, что длина корректна
        if data_len > plaintext.len() - 1 {
            return Err(DecryptError::InvalidLength);
        }
        
        // Извлекаем данные (без паддинга)
        let payload = plaintext[1..1 + data_len].to_vec();
        
        Ok(CpnPacket {
            nonce,
            sequence,
            payload,
        })
    }
}
```

## Генерация Nonce

### Структура Nonce

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+---------------+---------------+---------------+---------------+
|   Random (4)  |                                               |
+---------------+         Monotonic Counter (8)                 +
|                                                               |
+---------------------------------------------------------------+
```

**Реализация:**

```rust
use ring::rand::{SecureRandom, SystemRandom};
use std::sync::atomic::{AtomicU64, Ordering};

struct NonceGenerator {
    counter: AtomicU64,
    rng: SystemRandom,
}

impl NonceGenerator {
    fn new() -> Self {
        Self {
            counter: AtomicU64::new(0),
            rng: SystemRandom::new(),
        }
    }
    
    fn generate(&self) -> [u8; 12] {
        let mut nonce = [0u8; 12];
        
        // Генерируем 4 случайных байта
        self.rng.fill(&mut nonce[0..4]).unwrap();
        
        // Увеличиваем и записываем счетчик
        let counter = self.counter.fetch_add(1, Ordering::SeqCst);
        nonce[4..12].copy_from_slice(&counter.to_le_bytes());
        
        nonce
    }
    
    fn reset(&self) {
        self.counter.store(0, Ordering::SeqCst);
    }
}
```

### Сброс Nonce при смене ключа

```rust
impl Session {
    fn rotate_key(&mut self) -> Result<(), Error> {
        // Выполняем новый обмен ключами
        let new_master_key = self.perform_key_exchange()?;
        
        // Генерируем новый ключ сессии
        self.session_key = derive_session_key(&new_master_key, &self.session_id);
        
        // Сбрасываем счетчик nonce
        self.nonce_generator.reset();
        
        // Генерируем новую случайную часть для первого nonce
        self.rng.fill(&mut self.nonce[0..4])?;
        
        Ok(())
    }
}
```

## Защита от replay-атак

### Кольцевой битовый буфер

```rust
use std::sync::atomic::{AtomicU64, Ordering};

struct ReplayWindow {
    // 16 элементов по 64 бита = 1024 бита
    bits: [AtomicU64; 16],
    // Нижняя граница окна
    lower: AtomicU64,
}

impl ReplayWindow {
    fn new() -> Self {
        Self {
            bits: Default::default(),
            lower: AtomicU64::new(0),
        }
    }
    
    /// Проверяет, является ли пакет новым
    /// Возвращает false, если это повторная передача
    fn check(&self, sequence: u64) -> bool {
        let lower = self.lower.load(Ordering::Acquire);
        
        // Если sequence слишком старый (за пределами окна)
        if sequence < lower {
            return false;
        }
        
        // Если sequence слишком новый (за пределами текущего окна)
        // Расширяем окно
        if sequence >= lower + 1024 {
            self.expand_window(sequence);
        }
        
        let idx = (sequence / 64) % 16;
        let bit = sequence % 64;
        let mask = 1u64 << bit;
        
        // Проверяем, установлен ли бит
        let bits = self.bits[idx as usize].load(Ordering::Acquire);
        if (bits & mask) != 0 {
            return false; // Повторная передача
        }
        
        // Устанавливаем бит
        self.bits[idx as usize].fetch_or(mask, Ordering::Release);
        true
    }
    
    fn expand_window(&self, new_sequence: u64) {
        let mut lower = self.lower.load(Ordering::Acquire);
        
        loop {
            if new_sequence < lower + 1024 {
                break;
            }
            
            // Сдвигаем окно на 64 пакета
            let new_lower = lower + 64;
            
            match self.lower.compare_exchange_weak(
                lower,
                new_lower,
                Ordering::SeqCst,
                Ordering::Acquire,
            ) {
                Ok(_) => {
                    // Очищаем бит, который вышел за пределы окна
                    let old_idx = (lower / 64) % 16;
                    self.bits[old_idx as usize].store(0, Ordering::Release);
                    lower = new_lower;
                }
                Err(l) => lower = l,
            }
        }
    }
}
```

### Интеграция в обработку пакетов

```rust
impl Session {
    fn process_packet(&self, packet: CpnPacket) -> Result<(), ProcessError> {
        // Проверяем replay
        if !self.replay_window.check(packet.sequence) {
            return Err(ProcessError::ReplayAttack);
        }
        
        // Дешифруем
        let plaintext = packet.decrypt(&self.session_key)?;
        
        // Обрабатываем данные
        self.handle_data(plaintext)?;
        
        Ok(())
    }
}
```

## Смена ключей (Key Rotation)

### Условия смены ключа

Смена ключа происходит при выполнении любого из условий:
1. Прошло 80 секунд с момента последней смены
2. Передано 120 МБ данных
3. Запрос от партнера по соединению

### Процесс смены ключа

```rust
impl Session {
    async fn check_key_rotation(&mut self) -> Result<(), Error> {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_key_rotation);
        let bytes_transferred = self.bytes_sent + self.bytes_received;
        
        if elapsed >= Duration::from_secs(80) 
            || bytes_transferred >= 120 * 1024 * 1024 
        {
            self.rotate_key().await?;
        }
        
        Ok(())
    }
    
    async fn rotate_key(&mut self) -> Result<(), Error> {
        // 1. Генерируем новые ключи
        let new_x25519_secret = X25519Secret::generate();
        let new_kyber_secret = Kyber768Secret::generate();
        
        // 2. Отправляем публичные ключи партнеру
        // (через уже установленный защищенный канал)
        self.send_key_update(
            new_x25519_secret.public_key(),
            new_kyber_secret.public_key(),
        ).await?;
        
        // 3. Получаем ключи партнера
        let (peer_x25519_public, peer_kyber_ciphertext) = 
            self.receive_key_update().await?;
        
        // 4. Вычисляем новые shared secrets
        let shared_x25519 = new_x25519_secret.diffie_hellman(&peer_x25519_public);
        let shared_kyber = new_kyber_secret.decapsulate(&peer_kyber_ciphertext);
        
        // 5. Комбинируем и производим новый мастер-ключ
        let combined = [shared_x25519.as_ref(), shared_kyber.as_ref()].concat();
        let new_master_key = hkdf_sha512(&combined, b"CPN key rotation", &[]);
        
        // 6. Производим новый ключ сессии
        self.session_key = derive_session_key(&new_master_key, &self.session_id);
        
        // 7. Сбрасываем счетчики
        self.nonce_generator.reset();
        self.bytes_sent = 0;
        self.bytes_received = 0;
        self.last_key_rotation = Instant::now();
        
        // 8. Затираем старые ключи в памяти
        secure_zero_memory(&mut self.old_session_key);
        
        Ok(())
    }
}
```

### Безопасность при смене ключа

1. **Атомарность:** Смена ключа происходит атомарно, чтобы избежать состояния гонки
2. **Подтверждение:** Оба партнера подтверждают успешную смену ключа
3. **Откат:** При ошибке откатываемся к предыдущему ключу
4. **Затирание:** Старые ключи немедленно затираются в памяти

## Криптографические примитивы

### Используемые библиотеки

- **ring**: X25519, AES-GCM, HKDF, SHA512
- **pqcrypto-kyber**: Kyber-768 KEM
- **getrandom**: Системный источник энтропии

### Константы

```rust
// Размеры ключей
const X25519_PUBLIC_KEY_LEN: usize = 32;
const X25519_SECRET_KEY_LEN: usize = 32;
const KYBER768_PUBLIC_KEY_LEN: usize = 1184;
const KYBER768_SECRET_KEY_LEN: usize = 2400;
const KYBER768_CIPHERTEXT_LEN: usize = 1088;
const KYBER768_SHARED_SECRET_LEN: usize = 32;

// AES-GCM
const AES256GCM_KEY_LEN: usize = 32;
const AES256GCM_NONCE_LEN: usize = 12;
const AES256GCM_TAG_LEN: usize = 16;

// Размеры
const SESSION_ID_LEN: usize = 8;
const SEQUENCE_LEN: usize = 8;
const MAX_PADDING: usize = 255;
```

## Анализ безопасности

### Преимущества

1. **Пост-квантовая стойкость:** Kyber-768 обеспечивает защиту от квантовых атак
2. **Forward Secrecy:** Каждая сессия использует уникальные эфемерные ключи
3. **Гибридный подход:** Комбинирование классической и пост-квантовой криптографии
4. **Защита от replay:** Кольцевой буфер с O(1) сложностью
5. **Регулярная смена ключей:** Минимизация окна уязвимости

### Потенциальные уязвимости

1. **Side-channel атаки:** Внимание к времени выполнения операций
2. **Генерация случайных чисел:** Критически важна для безопасности
3. **Утечка памяти:** Тщательное управление памятью при смене ключей
4. **Десятилогарифмическая атака на Kyber:** Теоретически возможна, но практически не применима

### Рекомендации по безопасности

1. Использовать аппаратные генераторы случайных чисел при наличии
2. Регулярно обновлять криптографические библиотеки
3. Вести аудит безопасности кода
4. Мониторинг аномалий в трафике
5. Резервное копирование ключей в защищенном хранилище