//! Subscription Service

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

/// User account
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: i64,
    pub telegram_id: Option<i64>,
    pub email: Option<String>,
    pub password_hash: String,
    pub subscription: Option<Subscription>,
    pub created_at: u64,
}

/// Subscription status
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Subscription {
    pub active: bool,
    pub expires_at: u64,
    pub plan: String,
    pub started_at: u64,
}

/// JWT token claims
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenClaims {
    pub sub: i64,
    pub email: Option<String>,
    pub telegram_id: Option<i64>,
    pub exp: u64,
    pub iat: u64,
}

/// Key Bundle for CPN
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KeyBundle {
    pub client_id: String,
    pub access_token: String,
    pub refresh_token: Option<String>,
    pub expires_at: u64,
    pub sni_list: Vec<String>,
    pub keepalive_interval: f32,
    pub jitter_profile: String,
    pub transport_priority: Vec<String>,
    pub padding_shift: u8,
    pub fallback_config: Option<FallbackConfig>,
}

/// Fallback configuration for other protocols
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FallbackConfig {
    pub protocol: String,
    pub server: String,
    pub port: u16,
    pub uuid: Option<String>,
    pub password: Option<String>,
    pub method: Option<String>,
}

/// Subscription Service
pub struct SubscriptionManager {
    users: Arc<RwLock<HashMap<i64, User>>>,
    tokens: Arc<RwLock<HashMap<String, i64>>>,
    jwt_secret: String,
}

impl SubscriptionManager {
    pub fn new(jwt_secret: String) -> Self {
        Self {
            users: Arc::new(RwLock::new(HashMap::new())),
            tokens: Arc::new(RwLock::new(HashMap::new())),
            jwt_secret,
        }
    }

    /// Create new user
    pub async fn create_user(&self, telegram_id: Option<i64>, email: Option<String>) -> User {
        let id = chrono::Utc::now().timestamp_millis() as i64;
        let user = User {
            id,
            telegram_id,
            email,
            password_hash: String::new(),
            subscription: None,
            created_at: chrono::Utc::now().timestamp(),
        };
        
        self.users.write().await.insert(id, user.clone());
        user
    }

    /// Check subscription status
    pub async fn get_subscription_status(&self, user_id: i64) -> Option<Subscription> {
        let users = self.users.read().await;
        users.get(&user_id).and_then(|u| u.subscription.clone())
    }

    /// Generate key bundle for user
    pub async fn generate_key_bundle(&self, user_id: i64) -> Option<KeyBundle> {
        let users = self.users.read().await;
        let user = users.get(&user_id)?;
        let sub = user.subscription.as_ref()?;

        if !sub.active || sub.expires_at < chrono::Utc::now().timestamp() as u64 {
            return None;
        }

        Some(KeyBundle {
            client_id: format!("client_{}", user_id),
            access_token: format!("token_{}", user_id),
            refresh_token: None,
            expires_at: sub.expires_at,
            sni_list: vec!["cloudflare.com".to_string(), "microsoft.com".to_string()],
            keepalive_interval: 2.5,
            jitter_profile: "normal".to_string(),
            transport_priority: vec!["tls".to_string(), "quic".to_string(), "websocket".to_string()],
            padding_shift: 12,
            fallback_config: None,
        })
    }

    /// Activate subscription
    pub async fn activate_subscription(&self, user_id: i64, days: i64) -> bool {
        let now = chrono::Utc::now().timestamp() as u64;
        let expires = now + (days * 24 * 60 * 60) as u64;

        let mut users = self.users.write().await;
        if let Some(user) = users.get_mut(&user_id) {
            user.subscription = Some(Subscription {
                active: true,
                expires_at: expires,
                plan: "premium".to_string(),
                started_at: now,
            });
            return true;
        }
        false
    }
}