//! Пакетные типы

/// Размер nonce
pub const NONCE_SIZE: usize = 12;
/// Размер тега
pub const TAG_SIZE: usize = 16;
/// Размер ID сессии
pub const SESSION_ID_SIZE: usize = 32;

/// Структура CPN пакета
#[derive(Debug, Clone)]
pub struct CpnPacket {
    /// Nonce
    pub nonce: super::Nonce,
    /// Номер пакета
    pub sequence: super::SequenceNumber,
    /// Payload
    pub payload: Vec<u8>,
}

/// Структура зашифрованного CPN пакета
#[derive(Debug, Clone)]
pub struct EncryptedCpnPacket {
    /// Nonce
    pub nonce: super::Nonce,
    /// Номер пакета
    pub sequence: super::SequenceNumber,
    /// Зашифрованный payload
    pub ciphertext: Vec<u8>,
    /// Тег аутентификации
    pub tag: [u8; TAG_SIZE],
}

/// Структура TLS ClientHello
#[derive(Debug, Clone)]
pub struct TlsClientHello {
    /// Версия
    pub version: [u8; 2],
    /// Random
    pub random: [u8; 32],
    /// Session ID
    pub session_id: Vec<u8>,
    /// Набор шифров
    pub cipher_suites: Vec<u16>,
    /// Расширения
    pub extensions: Vec<TlsExtension>,
}

/// Расширение TLS
#[derive(Debug, Clone)]
pub enum TlsExtension {
    /// Server Name Indication
    Sni(String),
    /// Supported Groups
    SupportedGroups(Vec<u16>),
    /// Key Share
    KeyShare(Vec<u8>),
    /// Supported Versions
    SupportedVersions(Vec<u16>),
    /// Padding
    Padding(Vec<u8>),
    /// Неизвестное расширение
    Unknown(u16, Vec<u8>),
}

/// Структура TLS ServerHello
#[derive(Debug, Clone)]
pub struct TlsServerHello {
    /// Версия
    pub version: [u8; 2],
    /// Random
    pub random: [u8; 32],
    /// Session ID
    pub session_id: Vec<u8>,
    /// Cipher Suite
    pub cipher_suite: u16,
    /// Compression
    pub compression: u8,
    /// Extensions
    pub extensions: Vec<TlsExtension>,
}

/// Структура QUIC заголовка
#[derive(Debug, Clone)]
pub struct QuicHeader {
    /// Флаги
    pub flags: u8,
    /// Версия
    pub version: u32,
    /// Destination Connection ID
    pub dcid: [u8; 8],
    /// Source Connection ID
    pub scid: [u8; 8],
    /// Длина токена
    pub token_length: u16,
    /// Токен
    pub token: Vec<u8>,
}