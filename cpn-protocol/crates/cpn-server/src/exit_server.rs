//! Exit Server implementation

use cpn_protocol::types::ServerConfig;

/// Exit Server
pub struct ExitServer {
    config: ServerConfig,
}

impl ExitServer {
    /// Создает новый Exit Server
    pub fn new(config: ServerConfig) -> Self {
        Self { config }
    }

    /// Запускает сервер
    pub async fn run(self) -> Result<(), Box<dyn std::error::Error>> {
        // TODO: реализовать сервер
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        }
    }
}