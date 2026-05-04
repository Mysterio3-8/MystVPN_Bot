//! API server implementation

use axum::{
    extract::State,
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

use crate::subscription::{KeyBundle, SubscriptionManager};

/// API state
#[derive(Clone)]
pub struct ApiState {
    pub subscription_manager: Arc<SubscriptionManager>,
}

/// Health check response
#[derive(Serialize)]
pub struct HealthResponse {
    pub status: String,
    pub version: String,
    pub timestamp: u64,
}

/// Login request
#[derive(Deserialize)]
pub struct LoginRequest {
    pub telegram_id: Option<i64>,
    pub email: Option<String>,
    pub password: Option<String>,
}

/// Login response
#[derive(Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub expires_in: u64,
}

/// Create API router
pub fn create_api_router(state: ApiState) -> Router {
    Router::new()
        .route("/health", get(health_check))
        .route("/api/v1/auth/login", post(login))
        .route("/api/v1/config/current", get(get_config))
        .with_state(state)
}

async fn health_check() -> Json<HealthResponse> {
    Json(HealthResponse {
        status: "ok".to_string(),
        version: env!("CARGO_PKG_VERSION").to_string(),
        timestamp: chrono::Utc::now().timestamp() as u64,
    })
}

async fn login(
    State(state): State<ApiState>,
    Json(req): Json<LoginRequest>,
) -> Result<Json<LoginResponse>, StatusCode> {
    // TODO: Implement proper auth
    // For now, create test user
    let user = state.subscription_manager
        .create_user(req.telegram_id, req.email)
        .await;
    
    // Generate test key bundle
    let bundle = state.subscription_manager
        .generate_key_bundle(user.id)
        .await
        .unwrap();
    
    Ok(Json(LoginResponse {
        token: bundle.access_token,
        expires_in: bundle.expires_at,
    }))
}

async fn get_config(
    State(state): State<ApiState>,
) -> Result<Json<KeyBundle>, StatusCode> {
    // TODO: Use actual user ID from auth token
    let user_id = 12345i64;
    
    let bundle = state.subscription_manager
        .generate_key_bundle(user_id)
        .await
        .ok_or(StatusCode::UNAUTHORIZED)?;
    
    Ok(Json(bundle))
}

/// Run API server
pub async fn run_api_server(addr: &str, state: ApiState) -> anyhow::Result<()> {
    let app = create_api_router(state);
    
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}