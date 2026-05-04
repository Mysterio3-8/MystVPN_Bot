//! API типы

use serde::{Deserialize, Serialize};

// Re-export types from other modules
pub use super::client::{ClientId, ClientProfile, TransportType, JitterProfile, ConnectionStatus};

/// Сообщение об ошибке
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorMessage {
    /// Код ошибки
    pub code: u32,
    /// Сообщение
    pub message: String,
    /// Детали
    pub details: Option<String>,
}

/// Ответ API
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ApiResponse<T> {
    /// Успех
    pub success: bool,
    /// Данные
    pub data: Option<T>,
    /// Ошибка
    pub error: Option<ErrorMessage>,
}

/// Запрос аутентификации
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthRequest {
    /// Имя пользователя
    pub username: String,
    /// Пароль
    pub password: String,
}

/// Ответ аутентификации
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthResponse {
    /// Токен доступа
    pub access_token: String,
    /// Тип токена
    pub token_type: String,
    /// Время жизни (секунды)
    pub expires_in: u64,
}

/// Запрос на обновление профиля
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProfileUpdateRequest {
    /// Сдвиг паддинга
    pub padding_shift: Option<u8>,
    /// Интервал keep-alive
    pub keepalive_interval: Option<f32>,
    /// Профиль джиттера
    pub jitter_profile: Option<JitterProfile>,
}

/// Запрос на добавление правила split tunneling
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitTunnelRuleRequest {
    /// Тип правила
    pub rule_type: RuleType,
    /// Значение
    pub value: String,
    /// Действие
    pub action: RuleAction,
}

/// Статус SNI списка
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SniListStatus {
    /// Регион
    pub region: String,
    /// Список SNI
    pub sni_list: Vec<String>,
    /// Время обновления
    pub updated_at: u64,
}

/// Запрос на обновление SNI
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SniUpdateRequest {
    /// Список SNI
    pub sni_list: Vec<String>,
}

/// Сообщение для WebSocket
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSocketMessage {
    /// Тип сообщения
    pub message_type: WebSocketMessageType,
    /// Данные
    pub data: serde_json::Value,
}

/// Тип сообщения WebSocket
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum WebSocketMessageType {
    /// Статус подключения
    Status,
    /// Смена транспорта
    TransportSwitch,
    /// Новое подключение
    ClientConnect,
    /// Отключение клиента
    ClientDisconnect,
    /// Ошибка
    Error,
}

/// Запрос на регистрацию клиента
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterRequest {
    /// Имя пользователя
    pub username: String,
    /// Пароль
    pub password: String,
    /// Email
    pub email: Option<String>,
}

/// Ответ на регистрацию
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegisterResponse {
    /// Успех
    pub success: bool,
    /// ID клиента
    pub client_id: ClientId,
    /// Профиль
    pub profile: ClientProfile,
}

/// Запрос на восстановление пароля
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PasswordResetRequest {
    /// Email
    pub email: String,
}

/// Запрос на изменение пароля
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PasswordChangeRequest {
    /// Старый пароль
    pub old_password: String,
    /// Новый пароль
    pub new_password: String,
}

/// Статус лицензии
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LicenseStatus {
    /// Тип лицензии
    pub license_type: String,
    /// Действительна до
    pub valid_until: u64,
    /// Максимум клиентов
    pub max_clients: u32,
    /// Текущее количество клиентов
    pub current_clients: u32,
    /// Функции
    pub features: Vec<String>,
}

/// Метрики производительности
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceMetrics {
    /// Использование CPU (%)
    pub cpu_usage: f32,
    /// Использование памяти (МБ)
    pub memory_usage_mb: f32,
    /// Скорость обработки (пакетов/сек)
    pub processing_rate: f64,
    /// Среднее время обработки (мкс)
    pub average_processing_time_us: f64,
    /// Очередь входящих пакетов
    pub incoming_queue_size: usize,
    /// Очередь исходящих пакетов
    pub outgoing_queue_size: usize,
}

/// Системная информация
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    /// ОС
    pub os: String,
    /// Архитектура
    pub arch: String,
    /// Версия Rust
    pub rust_version: String,
    /// Версия протокола
    pub protocol_version: String,
    /// Время запуска (UNIX timestamp)
    pub start_time: u64,
    /// Текущее время (UNIX timestamp)
    pub current_time: u64,
}

/// Конфигурация сети
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkSettings {
    /// DNS серверы
    pub dns_servers: Vec<String>,
    /// Маршруты
    pub routes: Vec<Route>,
    /// MTU
    pub mtu: u16,
    /// TTL
    pub ttl: u8,
}

/// Маршрут
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Route {
    /// Сеть назначения
    pub destination: String,
    /// Шлюз
    pub gateway: String,
    /// Интерфейс
    pub interface: String,
    /// Метрика
    pub metric: u32,
}

/// Конфигурация безопасности
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SecurityConfig {
    /// Минимальная длина пароля
    pub min_password_length: usize,
    /// Требовать спецсимволы
    pub require_special_chars: bool,
    /// Требовать цифры
    pub require_numbers: bool,
    /// Требовать заглавные буквы
    pub require_uppercase: bool,
    /// Максимальное количество попыток входа
    pub max_login_attempts: u32,
    /// Блокировка после (секунды)
    pub lockout_duration: u64,
    /// Время жизни сессии (секунды)
    pub session_lifetime: u64,
}

/// Статус работы
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct HealthStatus {
    /// Статус
    pub status: String,
    /// Время работы (секунды)
    pub uptime: u64,
    /// Версия
    pub version: String,
    /// Подключенные клиенты
    pub connected_clients: u32,
}

/// Правило split tunneling
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitTunnelRule {
    /// ID правила
    pub id: String,
    /// Тип правила
    pub rule_type: RuleType,
    /// Значение (домен или подсеть)
    pub value: String,
    /// Действие
    pub action: RuleAction,
}

/// Событие CPN
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum CpnEvent {
    /// Клиент подключился
    ClientConnected {
        client_id: ClientId,
        transport: TransportType,
    },
    /// Клиент отключился
    ClientDisconnected {
        client_id: ClientId,
        reason: String,
    },
    /// Транспорт переключен
    TransportSwitched {
        client_id: ClientId,
        from: TransportType,
        to: TransportType,
    },
    /// Ошибка
    Error {
        client_id: Option<ClientId>,
        message: String,
    },
    /// Ключи сменены
    KeysRotated {
        client_id: ClientId,
    },
}

/// Запись лога
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LogEntry {
    /// Время
    pub timestamp: u64,
    /// Уровень
    pub level: LogLevel,
    /// ID клиента (опционально)
    pub client_id: Option<ClientId>,
    /// Сообщение
    pub message: String,
    /// Транспорт (опционально)
    pub transport: Option<TransportType>,
}

/// Уровень лога
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum LogLevel {
    /// Информация
    Info,
    /// Предупреждение
    Warn,
    /// Ошибка
    Error,
}

/// Тип правила
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum RuleType {
    /// Доменное имя
    Domain,
    /// IP подсеть
    Subnet,
}

/// Действие правила
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum RuleAction {
    /// Обход туннеля
    Bypass,
    /// Маршрутизация через туннель
    Tunnel,
}