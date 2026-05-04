//! Транспортные типы

use serde::{Deserialize, Serialize};
use std::net::SocketAddr;

/// Тип транспорта
#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
pub enum TransportType {
    /// TCP с эмуляцией TLS 1.3
    Tls,
    /// WebSocket через CDN
    WebSocket,
    /// UDP с эмуляцией QUIC
    Quic,
}

/// Статус транспорта
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum TransportStatus {
    /// Подключен и работает
    Connected,
    /// Отключен
    Disconnected,
    /// Ошибка соединения
    Error,
    /// В процессе переподключения
    Reconnecting,
}

/// Тип профиля джиттера
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum JitterProfile {
    /// Равномерный распределение
    Uniform,
    /// Нормальное распределение
    Normal,
    /// Экспоненциальное распределение
    Exponential,
}

/// Метрики транспорта
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportMetrics {
    /// Отправлено байт
    pub bytes_sent: u64,
    /// Получено байт
    pub bytes_received: u64,
    /// Отправлено пакетов
    pub packets_sent: u64,
    /// Получено пакетов
    pub packets_received: u64,
    /// Таймауты
    pub timeouts: u64,
    /// Переключения транспорта
    pub switches: u64,
    /// Текущий транспорт
    pub current_transport: TransportType,
    /// Задержка (мкс)
    pub latency: u64,
}

/// Конфигурация транспорта
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportConfig {
    /// Тип транспорта
    pub transport_type: TransportType,
    /// Адрес сервера
    pub server_address: SocketAddr,
    /// Таймаут соединения (секунды)
    pub connect_timeout: u64,
    /// Таймаут чтения (секунды)
    pub read_timeout: u64,
    /// Таймаут записи (секунды)
    pub write_timeout: u64,
    /// Максимальное количество таймаутов перед переключением
    pub max_timeouts: u32,
    /// Интервал пингования (секунды)
    pub ping_interval: u64,
}

/// Статус соединения транспорта
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportConnectionStatus {
    /// Тип транспорта
    pub transport_type: TransportType,
    /// Статус
    pub status: TransportStatus,
    /// Задержка (мс)
    pub latency_ms: Option<f64>,
}

/// Статус всех транспортов
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AllTransportStatus {
    /// Текущий транспорт
    pub current: TransportType,
    /// Доступные транспорты
    pub available: Vec<TransportType>,
    /// Статус каждого транспорта
    pub status: Vec<TransportConnectionStatus>,
}

/// Запрос на смену транспорта
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportSwitchRequest {
    /// Новый транспорт
    pub transport: TransportType,
}