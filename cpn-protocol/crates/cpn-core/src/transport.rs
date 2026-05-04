//! Transport layer for CPN

use cpn_protocol::types::TransportType;
use std::time::Duration;

/// Transport statistics
#[derive(Debug, Clone)]
pub struct TransportStats {
    pub bytes_sent: u64,
    pub bytes_recv: u64,
    pub packets_sent: u64,
    pub packets_recv: u64,
    pub timeout_count: u32,
}

/// Transport manager
pub struct TransportManager {
    pub current: TransportType,
    pub last_ping_ms: u64,
    pub consecutive_timeouts: u32,
    pub stats: TransportStats,
}

impl TransportManager {
    pub fn new() -> Self {
        Self {
            current: TransportType::Tls,
            last_ping_ms: 0,
            consecutive_timeouts: 0,
            stats: TransportStats {
                bytes_sent: 0,
                bytes_recv: 0,
                packets_sent: 0,
                packets_recv: 0,
                timeout_count: 0,
            },
        }
    }

    pub fn current(&self) -> TransportType {
        self.current
    }

    pub fn handle_timeout(&mut self) -> bool {
        self.consecutive_timeouts += 1;
        self.stats.timeout_count += 1;
        if self.consecutive_timeouts >= 3 {
            self.switch_transport();
            return true;
        }
        false
    }

    fn switch_transport(&mut self) {
        self.current = match self.current {
            TransportType::Tls => TransportType::Quic,
            TransportType::Quic => TransportType::WebSocket,
            TransportType::WebSocket => TransportType::Tls,
        };
        self.consecutive_timeouts = 0;
    }

    pub fn reset_timeouts(&mut self) {
        self.consecutive_timeouts = 0;
    }

    pub fn update_ping(&mut self, ping_ms: u64) {
        self.last_ping_ms = ping_ms;
    }

    pub fn record_sent(&mut self, bytes: usize) {
        self.stats.bytes_sent += bytes as u64;
        self.stats.packets_sent += 1;
    }

    pub fn record_recv(&mut self, bytes: usize) {
        self.stats.bytes_recv += bytes as u64;
        self.stats.packets_recv += 1;
    }
}

impl Default for TransportManager {
    fn default() -> Self {
        Self::new()
    }
}