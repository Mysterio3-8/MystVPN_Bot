//! WireGuard mimicry for CPN

use std::net::SocketAddr;

/// WireGuard-fake transport implementation
pub struct WgFakeTransport {
    local_addr: SocketAddr,
    remote_addr: SocketAddr,
    session_key: [u8; 32],
}

impl WgFakeTransport {
    pub fn new(remote_addr: SocketAddr, session_key: [u8; 32]) -> Self {
        let local_addr: SocketAddr = "0.0.0.0:0".parse().unwrap();
        Self {
            local_addr,
            remote_addr,
            session_key,
        }
    }

    pub fn build_handshake(&self) -> Vec<u8> {
        let mut packet = Vec::new();
        
        packet.extend_from_slice(b"WG_INIT");
        
        let mut eph_pub = [0u8; 32];
        getrandom::getrandom(&mut eph_pub).unwrap();
        packet.extend_from_slice(&eph_pub);
        
        packet.extend_from_slice(&self.session_key);
        
        let encrypted = [0u8; 16];
        packet.extend_from_slice(&encrypted);
        
        packet
    }

    pub fn get_remote(&self) -> SocketAddr {
        self.remote_addr
    }
}