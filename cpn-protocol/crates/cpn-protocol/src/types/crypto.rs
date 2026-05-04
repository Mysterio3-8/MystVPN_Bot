//! Криптографические типы

/// Ключи сессии
#[derive(Debug, Clone)]
pub struct SessionKeys {
    /// Ключ шифрования
    pub encryption_key: super::AesKey,
    /// Ключ расшифрования
    pub decryption_key: super::AesKey,
    /// Nonce генератор
    pub nonce_counter: u64,
}

/// Результат обмена ключами
#[derive(Debug, Clone)]
pub struct KeyExchangeResult {
    /// Общий секрет X25519
    pub x25519_secret: super::SharedSecret,
    /// Общий секрет Kyber
    pub kyber_secret: super::KyberSharedSecret,
    /// Ciphertext Kyber
    pub kyber_ciphertext: super::KyberCiphertext,
    /// Мастер ключ
    pub master_key: [u8; 64],
}

/// Состояние рукопожатия
#[derive(Debug, Clone)]
pub enum HandshakeState {
    /// Начальное состояние
    Initial,
    /// Отправлен ClientHello
    ClientHelloSent,
    /// Получен ServerHello
    ServerHelloReceived,
    /// Завершено
    Completed,
}

/// Статус рукопожатия
#[derive(Debug, Clone)]
pub struct HandshakeStatus {
    /// Состояние
    pub state: HandshakeState,
    /// Версия протокола
    pub version: String,
    /// Cipher suite
    pub cipher_suite: String,
    /// Алгоритмы обмена ключами
    pub key_exchange: Vec<String>,
}