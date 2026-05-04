//! Session management for CPN

use cpn_protocol::types::{ClientProfile, CpnConfig, TransportType, JitterProfile};
use cpn_protocol::crypto::KeyManager;
use cpn_protocol::replay::ReplayWindow;
use std::time::Instant;

/// CPN Session
pub struct Session {
    pub profile: ClientProfile,
    pub key_manager: KeyManager,
    pub replay_window: ReplayWindow,
    pub bytes_sent: u64,
    pub bytes_received: u64,
    pub last_key_rotation: Instant,
}

impl Session {
    pub fn new(profile: ClientProfile) -> Self {
        Self {
            profile,
            key_manager: KeyManager::new(),
            replay_window: ReplayWindow::new(),
            bytes_sent: 0,
            bytes_received: 0,
            last_key_rotation: Instant::now(),
        }
    }

    pub fn check_key_rotation(&self) -> bool {
        let elapsed = self.last_key_rotation.elapsed();
        let bytes_transferred = self.bytes_sent + self.bytes_received;

        elapsed.as_secs() >= 80 || bytes_transferred >= 120 * 1024 * 1024
    }

    pub fn record_sent(&mut self, bytes: usize) {
        self.bytes_sent += bytes as u64;
    }

    pub fn record_received(&mut self, bytes: usize) {
        self.bytes_received += bytes as u64;
    }

    pub fn generate_nonce(&self) -> [u8; 12] {
        self.key_manager.generate_nonce()
    }
}

impl Default for Session {
    fn default() -> Self {
        Self::new(ClientProfile {
            client_id: {
                let mut id = [0u8; 32];
                rand::RngCore::fill_bytes(&mut rand::thread_rng(), &mut id);
                id
            },
            padding_shift: 12,
            sni_list: vec!["cloudflare.com".to_string()],
            keepalive_interval: 2.5,
            keepalive_jitter: 0.5,
            jitter_profile: JitterProfile::Normal,
            transport_priority: vec![TransportType::Tls, TransportType::Quic, TransportType::WebSocket],
            expires_at: 0,
        })
    }
}