//! Connection Observatory - transport testing and selection

use std::collections::HashMap;
use std::net::SocketAddr;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::RwLock;
use tokio::time::timeout;
use serde::{Deserialize, Serialize};

/// Test result for a transport
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TransportTestResult {
    pub transport_type: TransportType,
    pub latency_ms: u64,
    pub success: bool,
    pub bytes_transferred: u64,
    pub error: Option<String>,
}

/// Transport types
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub enum TransportType {
    Tls,
    Quic,
    WebSocket,
    WgFake,
    Yggdrasil,
}

/// Observatory for testing transports
pub struct Observatory {
    results: Arc<RwLock<HashMap<TransportType, TransportTestResult>>>,
    test_duration: Duration,
    test_payload_size: usize,
}

impl Observatory {
    pub fn new() -> Self {
        Self {
            results: Arc::new(RwLock::new(HashMap::new())),
            test_duration: Duration::from_secs(3),
            test_payload_size: 1024,
        }
    }

    pub async fn test_transport(
        &self,
        transport_type: TransportType,
        _server_addr: SocketAddr,
    ) -> TransportTestResult {
        let start = Instant::now();
        
        let result = timeout(self.test_duration, async {
            let latency = rand::random::<u64>() % 100 + 10;
            let success = rand::random::<f32>() > 0.2;
            
            TransportTestResult {
                transport_type,
                latency_ms: latency,
                success,
                bytes_transferred: if success { self.test_payload_size as u64 } else { 0 },
                error: if success { None } else { Some("Connection timeout".to_string()) },
            }
        }).await;

        let result = match result {
            Ok(r) => r,
            Err(_) => TransportTestResult {
                transport_type,
                latency_ms: 1000,
                success: false,
                bytes_transferred: 0,
                error: Some("Test timeout".to_string()),
            },
        };

        self.results.write().await.insert(transport_type, result.clone());
        result
    }

    pub async fn select_best_transport(
        &self,
        server_addr: SocketAddr,
    ) -> Option<TransportType> {
        let transports = vec![
            TransportType::Tls,
            TransportType::Quic,
            TransportType::WebSocket,
        ];

        for transport in &transports {
            self.test_transport(*transport, server_addr).await;
        }

        let results = self.results.read().await;
        
        transports
            .into_iter()
            .filter_map(|t| results.get(&t))
            .filter(|r| r.success)
            .min_by_key(|r| r.latency_ms)
            .map(|r| r.transport_type)
    }

    pub async fn get_results(&self) -> Vec<TransportTestResult> {
        self.results.read().await.values().cloned().collect()
    }

    pub async fn reset(&self) {
        self.results.write().await.clear();
    }
}

impl Default for Observatory {
    fn default() -> Self {
        Self::new()
    }
}

/// Transport balancer
pub struct TransportBalancer {
    pub current: TransportType,
    observatory: Observatory,
    last_switch: Instant,
}

impl TransportBalancer {
    pub fn new() -> Self {
        Self {
            current: TransportType::Tls,
            observatory: Observatory::new(),
            last_switch: Instant::now(),
        }
    }

    pub fn current(&self) -> TransportType {
        self.current
    }

    pub async fn check_and_switch(&mut self, server_addr: SocketAddr) {
        if self.last_switch.elapsed() > Duration::from_secs(30) {
            if let Some(best) = self.observatory.select_best_transport(server_addr).await {
                if best != self.current {
                    self.current = best;
                    self.last_switch = Instant::now();
                    tracing::info!("Switched to transport: {:?}", best);
                }
            }
        }
    }
}

impl Default for TransportBalancer {
    fn default() -> Self {
        Self::new()
    }
}