//! Split tunneling and routing

use std::collections::HashSet;
use std::net::SocketAddr;
use std::sync::Arc;
use tokio::sync::RwLock;
use serde::{Deserialize, Serialize};

/// Split tunneling rule
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplitTunnelRule {
    pub id: String,
    pub rule_type: RuleType,
    pub value: String,
    pub action: RuleAction,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum RuleType {
    Domain,
    Subnet,
    Ip,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub enum RuleAction {
    Bypass,
    Tunnel,
}

/// Split tunneling manager
pub struct SplitTunnel {
    rules: Arc<RwLock<Vec<SplitTunnelRule>>>,
    ru_domains: HashSet<String>,
    ru_subnets: Vec<String>,
    last_update: u64,
}

impl SplitTunnel {
    pub fn new() -> Self {
        Self {
            rules: Arc::new(RwLock::new(Vec::new())),
            ru_domains: HashSet::new(),
            ru_subnets: Vec::new(),
            last_update: 0,
        }
    }

    pub fn should_bypass(&self, dest: &SocketAddr) -> bool {
        let dest_ip = dest.ip();
        for subnet in &self.ru_subnets {
            if subnet.contains(&dest_ip.to_string()) {
                return true;
            }
        }
        false
    }

    pub async fn add_bypass_rule(&self, value: String, rule_type: RuleType) {
        let rule = SplitTunnelRule {
            id: uuid::Uuid::new_v4().to_string(),
            rule_type,
            value,
            action: RuleAction::Bypass,
        };
        self.rules.write().await.push(rule);
    }

    pub async fn update_ru_domains(&mut self, domains: Vec<String>) {
        self.ru_domains = domains.into_iter().collect();
        self.last_update = chrono::Utc::now().timestamp() as u64;
    }

    pub async fn update_ru_subnets(&mut self, subnets: Vec<String>) {
        self.ru_subnets = subnets;
        self.last_update = chrono::Utc::now().timestamp() as u64;
    }
}

impl Default for SplitTunnel {
    fn default() -> Self {
        Self::new()
    }
}