//! Команда статуса

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use cpn_core::ffi::ConnectionState;
use cpn_protocol::types::TransportType;

static CONNECTED: AtomicBool = AtomicBool::new(false);
static PING_MS: AtomicU64 = AtomicU64::new(0);
static BYTES_SENT: AtomicU64 = AtomicU64::new(0);
static BYTES_RECV: AtomicU64 = AtomicU64::new(0);

pub async fn show_status() -> Result<(), Box<dyn std::error::Error>> {
    let state = ConnectionState {
        connected: CONNECTED.load(Ordering::SeqCst),
        transport: TransportType::Tls as u32,
        ping_ms: PING_MS.load(Ordering::SeqCst) as u32,
        bytes_sent: BYTES_SENT.load(Ordering::SeqCst),
        bytes_received: BYTES_RECV.load(Ordering::SeqCst),
    };
    
    println!("=== CPN HUB Status ===");
    println!("Connected: {}", state.connected);
    println!("Transport: {}", match state.transport {
        0 => "TLS",
        1 => "WebSocket", 
        2 => "QUIC",
        _ => "Unknown",
    });
    println!("Ping: {}ms", state.ping_ms);
    println!("Bytes sent: {}", state.bytes_sent);
    println!("Bytes received: {}", state.bytes_received);
    Ok(())
}