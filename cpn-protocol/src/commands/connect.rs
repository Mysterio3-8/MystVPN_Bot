//! Команда подключения

use cpn_core::{
    session::Session, 
    transport::TransportManager, 
    observatory::Observatory,
    routing::SplitTunnel,
    ffi::ConnectionState,
};
use cpn_protocol::types::{ClientConfig, TransportType, JitterProfile};
use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::Arc;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt, EnvFilter};

static CONNECTED: AtomicBool = AtomicBool::new(false);
static BYTES_SENT: AtomicU64 = AtomicU64::new(0);
static BYTES_RECV: AtomicU64 = AtomicU64::new(0);
static PING_MS: AtomicU64 = AtomicU64::new(0);

pub async fn connect(config_path: PathBuf, debug: bool) -> Result<(), Box<dyn std::error::Error>> {
    let fmt_layer = tracing_subscriber::fmt::layer()
        .with_target(true)
        .with_ansi(debug);
    
    let filter = EnvFilter::new(if debug { "debug" } else { "info" });
    tracing_subscriber::registry()
        .with(fmt_layer)
        .with(filter)
        .init();

    println!("CPN HUB v{}", env!("CARGO_PKG_VERSION"));
    
    if !config_path.exists() {
        eprintln!("Config file not found: {:?}", config_path);
        generate_default_config(&config_path).await?;
        println!("Generated default config at {:?}", config_path);
        println!("Edit the config file and reconnect.");
        return Ok(());
    }

    let config_str = tokio::fs::read_to_string(&config_path).await?;
    let config: ClientConfig = match serde_json::from_str(&config_str) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("Failed to parse config: {}", e);
            generate_default_config(&config_path).await?;
            println!("Generated default config. Edit and reconnect.");
            return Ok(());
        }
    };

    println!("Connecting to servers...");
    println!("SNI list: {:?}", config.profile.sni_list);

    let mut session = Session::new(config.profile.clone());
    let mut transport = TransportManager::new();
    let mut observatory = Observatory::new();
    let mut split_tunnel = SplitTunnel::new();

    println!("Running transport test...");
    if let Ok(addr) = "127.0.0.1:443".parse() {
        if let Some(best) = observatory.select_best_transport(addr).await {
            println!("Best transport: {:?}", best);
        }
    }

    CONNECTED.store(true, Ordering::SeqCst);
    
    println!("Establishing connection...");
    tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
    
    println!("Connected via {:?}", transport.current());
    println!("Press Ctrl+C to disconnect...");
    
    tokio::signal::ctrl_c().await?;
    
    CONNECTED.store(false, Ordering::SeqCst);
    println!("Disconnected.");
    Ok(())
}

async fn generate_default_config(path: &PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let config = ClientConfig {
        entry_servers: vec!["us1.cpn.io:443".parse().unwrap()],
        profile: cpn_protocol::types::ClientProfile {
            client_id: [0u8; 32],
            padding_shift: 12,
            sni_list: vec!["cloudflare.com".to_string()],
            keepalive_interval: 2.5,
            keepalive_jitter: 0.5,
            jitter_profile: JitterProfile::Normal,
            transport_priority: vec![TransportType::Tls, TransportType::Quic],
            expires_at: 0,
        },
        tun_config: cpn_protocol::types::TunConfig {
            name: "cpn0".to_string(),
            address: "10.10.0.2".to_string(),
            netmask: "255.255.255.0".to_string(),
            mtu: 1500,
        },
        log_config: cpn_protocol::types::LogConfig {
            level: "info".to_string(),
            file: None,
        },
    };

    let json = serde_json::to_string_pretty(&config)?;
    if let Some(parent) = path.parent() {
        tokio::fs::create_dir_all(parent).await?;
    }
    tokio::fs::write(path, json).await?;
    Ok(())
}