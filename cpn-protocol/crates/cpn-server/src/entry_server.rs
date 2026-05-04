//! Entry Server implementation

use cpn_protocol::types::ServerConfig;
use cpn_core::transport::TransportManager;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// Entry Server
pub struct EntryServer {
    config: ServerConfig,
    transport: TransportManager,
    clients: Arc<RwLock<HashMap<[u8; 32], ClientSession>>>,
}

struct ClientSession {
    bytes_sent: u64,
    bytes_received: u64,
}

impl EntryServer {
    /// Создает новый Entry Server
    pub fn new(config: ServerConfig) -> Self {
        Self {
            config,
            transport: TransportManager::new(),
            clients: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    /// Запускает сервер
    pub async fn run(self) -> Result<(), Box<dyn std::error::Error>> {
        // TODO: реализовать сервер
        loop {
            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;
        }
    }
}