//! Команда сервиса

use cpn_core::{
    transport::TransportManager,
    session::Session,
};
use cpn_protocol::types::TransportType;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;

static CONNECTED: AtomicBool = AtomicBool::new(false);
static PING_MS: AtomicU64 = AtomicU64::new(0);

pub async fn run_service() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt::init();
    
    println!("CPN HUB Service starting...");
    
    let mut transport = TransportManager::new();
    let mut session = Session::default();
    
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(5)).await;
        
        if CONNECTED.load(Ordering::SeqCst) {
            let ping = rand::random::<u64>() % 50;
            PING_MS.store(ping, Ordering::SeqCst);
            
            if ping > 100 {
                transport.handle_timeout();
                println!("High latency detected, transport: {:?}", transport.current());
            }
        }
    }
}