//! CPN Client implementation

use cpn_protocol::types::{ClientConfig, ClientProfile, TransportType};
use cpn_core::session::Session;
use cpn_core::transport::TransportManager;

/// CPN Client
pub struct Client {
    config: ClientConfig,
    session: Session,
    transport: TransportManager,
}

impl Client {
    /// Создает новый клиент
    pub fn new(config: ClientConfig) -> Self {
        let session = Session::new(config.profile.clone());
        let transport = TransportManager::new();
        
        Self {
            config,
            session,
            transport,
        }
    }

    /// Запускает клиент
    pub async fn run(&mut self) -> Result<(), Box<dyn std::error::Error>> {
        loop {
            // TODO: реализовать соединение
            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        }
    }
}