//! MystVPN Server - Main binary

use cpn_server::{subscription::SubscriptionManager, api::{create_api_router, ApiState}};
use std::sync::Arc;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();
    
    let subscription_manager = Arc::new(SubscriptionManager::new(
        "jwt-secret-change-in-production".to_string()
    ));
    
    let state = ApiState { subscription_manager };
    
    println!("MystVPN Server v{}", env!("CARGO_PKG_VERSION"));
    
    let app = create_api_router(state);
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:9090").await?;
    println!("API server listening on http://0.0.0.0:9090");
    
    axum::serve(listener, app).await?;
    
    Ok(())
}