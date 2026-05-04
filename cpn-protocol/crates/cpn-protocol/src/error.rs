//! Ошибки протокола CPN

use thiserror::Error;

/// Ошибки протокола
#[derive(Debug, Error)]
pub enum ProtocolError {
    /// Ошибка криптографии
    #[error("Cryptographic error: {0}")]
    Crypto(String),

    /// Ошибка аутентификации
    #[error("Authentication failed")]
    AuthenticationFailed,

    /// Ошибка при обмене ключами
    #[error("Key exchange failed")]
    KeyExchangeFailed,

    /// Неверный формат пакета
    #[error("Invalid packet format")]
    InvalidPacketFormat,

    /// Повторная передача (replay attack)
    #[error("Replay attack detected")]
    ReplayAttack,

    /// Истек срок действия ключа
    #[error("Key expired")]
    KeyExpired,

    /// Ошибка транспорта
    #[error("Transport error: {0}")]
    Transport(String),

    /// Таймаут соединения
    #[error("Connection timeout")]
    Timeout,

    /// Ошибка IO
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    /// Ошибка сериализации
    #[error("Serialization error: {0}")]
    Serialization(String),

    /// Неизвестная ошибка
    #[error("Unknown error: {0}")]
    Unknown(String),
}