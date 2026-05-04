//! # Протокол CPN (Cerberus)
//!
//! Защищенный транспортный протокол с многослойной маскировкой трафика
//! и гибридной пост-квантовой криптографией.

#![warn(missing_docs)]
#![warn(rustdoc::missing_crate_level_docs)]
#![forbid(unsafe_code)]
#![deny(clippy::all)]

pub mod crypto;
pub mod error;
pub mod packet;
pub mod replay;
pub mod types;

pub use crypto::*;
pub use error::*;
pub use packet::*;
pub use replay::*;
pub use types::*;

/// Версия протокола
pub const PROTOCOL_VERSION: &str = "1.0.0";

/// Максимальный размер пакета
pub const MAX_PACKET_SIZE: usize = 65536;

/// Размер nonce для AES-GCM
pub const NONCE_SIZE: usize = 12;

/// Размер тега аутентификации
pub const TAG_SIZE: usize = 16;

/// Размер сессионного ID
pub const SESSION_ID_SIZE: usize = 8;

/// Максимальный размер паддинга
pub const MAX_PADDING_SIZE: usize = 255;

/// Размер заголовка пакета (nonce + sequence)
pub const PACKET_HEADER_SIZE: usize = NONCE_SIZE + std::mem::size_of::<u64>();
