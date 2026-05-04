//! Конфигурационные типы

use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

// Re-export types
pub use super::client::{ClientProfile, TransportType, JitterProfile};
pub use super::transport::TransportConfig;

/// Конфигурация клиента
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ClientConfig {
    /// Серверы входа
    pub entry_servers: Vec<SocketAddr>,
    /// Профиль маскировки
    pub profile: ClientProfile,
    /// Настройки TUN
    pub tun_config: TunConfig,
    /// Настройки логирования
    pub log_config: LogConfig,
}

/// Конфигурация TUN интерфейса
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TunConfig {
    /// Имя интерфейса
    pub name: String,
    /// IP адрес
    pub address: String,
    /// Маска подсети
    pub netmask: String,
    /// MTU
    pub mtu: u16,
}

/// Конфигурация логирования
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogConfig {
    /// Уровень логирования
    pub level: String,
    /// Файл логов
    pub file: Option<String>,
}

/// Конфигурация сервера
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ServerConfig {
    /// Тип сервера
    pub server_type: ServerType,
    /// Сетевые настройки
    pub network: NetworkConfig,
    /// Настройки логирования
    pub log_config: LogConfig,
}

/// Тип сервера
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum ServerType {
    /// Entry сервер
    Entry,
    /// Exit сервер
    Exit,
    /// Control сервер
    Control,
}

/// Сетевые настройки
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkConfig {
    /// TCP порт
    pub tcp_port: u16,
    /// UDP порт
    pub udp_port: u16,
    /// API порт
    pub api_port: u16,
    /// Интерфейс
    pub bind_address: String,
}

/// Конфигурация криптографии
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoConfig {
    /// Использовать X25519
    pub use_x25519: bool,
    /// Использовать Kyber-768
    pub use_kyber: bool,
    /// Размер ключа AES
    pub aes_key_size: usize,
    /// Размер nonce
    pub nonce_size: usize,
    /// Интервал смены ключа (секунды)
    pub key_rotation_interval: u64,
    /// Максимальный объем данных до смены ключа (байты)
    pub max_data_before_rotation: u64,
}

/// Стандартная конфигурация криптографии
impl Default for CryptoConfig {
    fn default() -> Self {
        Self {
            use_x25519: true,
            use_kyber: true,
            aes_key_size: 32,
            nonce_size: 12,
            key_rotation_interval: 80,
            max_data_before_rotation: 120 * 1024 * 1024, // 120 MB
        }
    }
}

/// Конфигурация обфускации
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ObfuscationConfig {
    /// Минимальный размер паддинга
    pub min_padding_size: usize,
    /// Максимальный размер паддинга
    pub max_padding_size: usize,
    /// Минимальный джиттер (мс)
    pub min_jitter_ms: u64,
    /// Максимальный джиттер (мс)
    pub max_jitter_ms: u64,
    /// Минимальный интервал keep-alive (секунды)
    pub min_keepalive_interval: u64,
    /// Максимальный интервал keep-alive (секунды)
    pub max_keepalive_interval: u64,
    /// Размер окна replay-защиты
    pub replay_window_size: usize,
}

/// Стандартная конфигурация обфускации
impl Default for ObfuscationConfig {
    fn default() -> Self {
        Self {
            min_padding_size: 0,
            max_padding_size: 255,
            min_jitter_ms: 3,
            max_jitter_ms: 18,
            min_keepalive_interval: 1,
            max_keepalive_interval: 4,
            replay_window_size: 1024,
        }
    }
}

/// Полная конфигурация CPN
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CpnConfig {
    /// Конфигурация клиента
    pub client: Option<ClientConfig>,
    /// Конфигурация сервера
    pub server: Option<ServerConfig>,
    /// Конфигурация криптографии
    pub crypto: CryptoConfig,
    /// Конфигурация обфускации
    pub obfuscation: ObfuscationConfig,
    /// Конфигурация транспорта
    pub transport: Vec<TransportConfig>,
}

/// Стандартная конфигурация CPN
impl Default for CpnConfig {
    fn default() -> Self {
        Self {
            client: None,
            server: None,
            crypto: CryptoConfig::default(),
            obfuscation: ObfuscationConfig::default(),
            transport: Vec::new(),
        }
    }
}