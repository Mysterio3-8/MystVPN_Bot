//! Команда генерации конфигурации

use cpn_protocol::types::{ClientConfig, TransportType, JitterProfile, TunConfig, LogConfig};
use std::path::PathBuf;

pub async fn generate_config(output: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let config = ClientConfig {
        entry_servers: vec!["1.2.3.4:443".parse().unwrap()],
        profile: cpn_protocol::types::ClientProfile {
            client_id: {
                let mut id = [0u8; 32];
                for byte in &mut id {
                    *byte = rand::random();
                }
                id
            },
            padding_shift: 12,
            sni_list: vec!["cloudflare.com".to_string(), "google.com".to_string()],
            keepalive_interval: 2.5,
            keepalive_jitter: 0.5,
            jitter_profile: JitterProfile::Normal,
            transport_priority: vec![TransportType::Tls, TransportType::Quic, TransportType::WebSocket],
            expires_at: 0,
        },
        tun_config: TunConfig {
            name: "cpn0".to_string(),
            address: "10.10.0.2".to_string(),
            netmask: "255.255.255.0".to_string(),
            mtu: 1500,
        },
        log_config: LogConfig {
            level: "info".to_string(),
            file: None,
        },
    };

    let json = serde_json::to_string_pretty(&config)?;
    tokio::fs::write(&output, json).await?;
    println!("Config written to {:?}", output);
    Ok(())
}