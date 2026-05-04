//! TUN interface implementation

use std::io;
use std::net::IpAddr;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::thread;

/// TUN interface configuration
#[derive(Debug, Clone)]
pub struct TunConfig {
    pub name: String,
    pub address: IpAddr,
    pub netmask: IpAddr,
    pub mtu: u16,
}

impl Default for TunConfig {
    fn default() -> Self {
        Self {
            name: "cpn0".to_string(),
            address: "10.10.0.1".parse().unwrap(),
            netmask: "255.255.255.0".parse().unwrap(),
            mtu: 1500,
        }
    }
}

/// TUN interface
pub struct TunInterface {
    config: TunConfig,
    packet_count: Arc<AtomicU64>,
    bytes_in: Arc<AtomicU64>,
    bytes_out: Arc<AtomicU64>,
}

impl TunInterface {
    pub fn new(config: TunConfig) -> io::Result<Self> {
        Ok(Self {
            config,
            packet_count: Arc::new(AtomicU64::new(0)),
            bytes_in: Arc::new(AtomicU64::new(0)),
            bytes_out: Arc::new(AtomicU64::new(0)),
        })
    }

    pub fn read_packet(&self, buf: &mut [u8]) -> io::Result<usize> {
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "TUN read not implemented - requires tun-tap crate on real system",
        ))
    }

    pub fn write_packet(&self, packet: &[u8]) -> io::Result<usize> {
        Err(io::Error::new(
            io::ErrorKind::Unsupported,
            "TUN write not implemented - requires tun-tap crate on real system",
        ))
    }

    pub fn start_routing(&self) -> io::Result<()> {
        // TUN routing not yet implemented (requires OS-level TUN device)
        let _ = &self.bytes_out;
        Ok(())
    }

    pub fn stats(&self) -> TunStats {
        TunStats {
            packets: self.packet_count.load(Ordering::Relaxed),
            bytes_in: self.bytes_in.load(Ordering::Relaxed),
            bytes_out: self.bytes_out.load(Ordering::Relaxed),
        }
    }
}

/// TUN statistics
#[derive(Debug, Clone)]
pub struct TunStats {
    pub packets: u64,
    pub bytes_in: u64,
    pub bytes_out: u64,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tun_config_default() {
        let config = TunConfig::default();
        assert_eq!(config.name, "cpn0");
        assert_eq!(config.mtu, 1500);
    }
}