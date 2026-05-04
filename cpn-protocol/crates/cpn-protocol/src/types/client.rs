//! Типы клиента

use serde::{Deserialize, Serialize};

// Re-export types from transport module
pub use super::transport::{TransportType, JitterProfile, TransportStatus};
pub use super::api::{RuleType, RuleAction, LogLevel};

/// Уникальный идентификатор клиента
pub type ClientId = [u8; 32];

/// Уникальный идентификатор сессии
pub type SessionId = [u8; 32];

/// Публичный ключ X25519
pub type X25519PublicKey = [u8; 32];

/// Секретный ключ X25519
pub type X25519SecretKey = [u8; 32];

/// Общий секрет (результат ECDH)
pub type SharedSecret = [u8; 32];

/// Публичный ключ Kyber-768
pub type KyberPublicKey = [u8; 1184];

/// Секретный ключ Kyber-768
pub type KyberSecretKey = [u8; 2400];

/// Ciphertext Kyber-768
pub type KyberCiphertext = [u8; 1088];

/// Общий секрет Kyber
pub type KyberSharedSecret = [u8; 32];

/// Ключ AES-256-GCM
pub type AesKey = [u8; 32];

/// Nonce для AES-GCM
pub type Nonce = [u8; 12];

/// Номер пакета
pub type SequenceNumber = u64;

/// Профиль маскировки клиента
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientProfile {
    /// ID клиента
    pub client_id: ClientId,
    /// Сдвиг паддинга (0-32 байта)
    pub padding_shift: u8,
    /// Список SNI для первичного транспорта
    pub sni_list: Vec<String>,
    /// Интервал keep-alive (секунды)
    pub keepalive_interval: f32,
    /// Джиттер для keep-alive
    pub keepalive_jitter: f32,
    /// Профиль джиттера
    pub jitter_profile: JitterProfile,
    /// Приоритет транспортов
    pub transport_priority: Vec<TransportType>,
    /// Время истечения профиля
    pub expires_at: u64,
}

/// Статус клиента
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientStatus {
    /// ID клиента
    pub client_id: ClientId,
    /// Текущий статус
    pub status: ConnectionStatus,
    /// Текущий транспорт
    pub current_transport: TransportType,
    /// Время подключения
    pub connected_since: u64,
    /// Время последней активности
    pub last_activity: u64,
    /// Отправлено байт
    pub bytes_sent: u64,
    /// Получено байт
    pub bytes_received: u64,
}

/// Статус соединения
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ConnectionStatus {
    /// Подключен
    Online,
    /// Отключен
    Offline,
    /// Ошибка
    Error,
}

/// Информация о клиенте
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientInfo {
    /// ID клиента
    pub client_id: ClientId,
    /// Имя пользователя
    pub username: String,
    /// Email
    pub email: Option<String>,
    /// Статус
    pub status: ConnectionStatus,
    /// Текущий транспорт
    pub current_transport: TransportType,
    /// Профиль
    pub profile: ClientProfile,
    /// Время подключения
    pub connected_since: u64,
    /// Время последней активности
    pub last_activity: u64,
    /// Отправлено байт
    pub bytes_sent: u64,
    /// Получено байт
    pub bytes_received: u64,
    /// Общее количество соединений
    pub total_connections: u64,
}

/// Список клиентов
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientList {
    /// Клиенты
    pub clients: Vec<ClientInfo>,
    /// Всего
    pub total: usize,
    /// Лимит
    pub limit: usize,
    /// Смещение
    pub offset: usize,
}

/// Статистика клиента
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientStatistics {
    /// ID клиента
    pub client_id: ClientId,
    /// Отправлено байт
    pub bytes_sent: u64,
    /// Получено байт
    pub bytes_received: u64,
    /// Отправлено пакетов
    pub packets_sent: u64,
    /// Получено пакетов
    pub packets_received: u64,
    /// Средняя задержка (мс)
    pub average_latency_ms: f64,
    /// Переключения транспорта
    pub transport_switches: u64,
    /// Время подключения
    pub connected_since: u64,
    /// Время последней активности
    pub last_activity: u64,
    /// Текущий транспорт
    pub current_transport: TransportType,
}