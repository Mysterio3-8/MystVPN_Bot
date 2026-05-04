//! Cryptographic core for CPN protocol

use chacha20poly1305::{ChaCha20Poly1305, Key, Nonce as ChaChaNonce};
use aes_gcm::aead::{AeadInPlace, KeyInit};
use x25519_dalek::{PublicKey, StaticSecret};
use std::sync::atomic::{AtomicU64, Ordering};
use hkdf::Hkdf;
use sha2::Sha256;

/// Key pair for X25519
pub type KeyPair = (StaticSecret, PublicKey);

/// Generate a new X25519 key pair
pub fn generate_keypair() -> KeyPair {
    let secret = StaticSecret::random_from_rng(rand::rngs::OsRng);
    let public = PublicKey::from(&secret);
    (secret, public)
}

/// Derive shared secret from key exchange
pub fn derive_shared(secret: &StaticSecret, public: &PublicKey) -> [u8; 32] {
    let shared = secret.diffie_hellman(public);
    shared.to_bytes()
}

/// Nonce generator for AES-GCM
pub struct NonceGenerator {
    counter: AtomicU64,
}

impl NonceGenerator {
    pub fn new() -> Self {
        Self {
            counter: AtomicU64::new(0),
        }
    }

    pub fn generate(&self) -> [u8; 12] {
        let mut nonce = [0u8; 12];
        let counter = self.counter.fetch_add(1, Ordering::SeqCst);
        nonce[4..12].copy_from_slice(&counter.to_le_bytes());
        let mut bytes = [0u8; 4];
        getrandom::getrandom(&mut bytes).unwrap();
        nonce[0..4].copy_from_slice(&bytes);
        nonce
    }

    pub fn reset(&self) {
        self.counter.store(0, Ordering::SeqCst);
    }
}

impl Default for NonceGenerator {
    fn default() -> Self {
        Self::new()
    }
}

/// HKDF key derivation
pub fn hkdf_derive(input: &[u8], salt: &[u8], info: &[&[u8]]) -> [u8; 64] {
    let hkdf = Hkdf::<Sha256>::new(Some(salt), input);
    let mut output = [0u8; 64];
    let info_flat: Vec<u8> = info.iter().flat_map(|s| s.iter().copied()).collect();
    hkdf.expand(&info_flat, &mut output).unwrap();
    output
}

/// Session key derivation
pub fn derive_session_key(master_key: &[u8; 64], session_id: &[u8; 8]) -> [u8; 32] {
    let hkdf = Hkdf::<Sha256>::new(Some(session_id), master_key);
    let mut key = [0u8; 32];
    hkdf.expand(b"CPN session key", &mut key).unwrap();
    key
}

/// Key manager
pub struct KeyManager {
    nonce_generator: NonceGenerator,
}

impl KeyManager {
    pub fn new() -> Self {
        Self {
            nonce_generator: NonceGenerator::new(),
        }
    }

    pub fn generate_nonce(&self) -> [u8; 12] {
        self.nonce_generator.generate()
    }

    pub fn reset_nonce(&self) {
        self.nonce_generator.reset();
    }
}

impl Default for KeyManager {
    fn default() -> Self {
        Self::new()
    }
}

/// AEAD cipher using ChaCha20-Poly1305
pub struct AeadCipher {
    cipher: ChaCha20Poly1305,
}

impl AeadCipher {
    pub fn new(key: &[u8; 32]) -> Self {
        Self {
            cipher: ChaCha20Poly1305::new(Key::from_slice(key)),
        }
    }

    pub fn encrypt(&self, nonce: &[u8; 12], plaintext: &[u8], ad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let mut buffer = plaintext.to_vec();
        let chacha_nonce = ChaChaNonce::from_slice(nonce);
        self.cipher.encrypt_in_place(chacha_nonce, ad, &mut buffer)
            .map_err(|e| CryptoError::EncryptionFailed(e.to_string()))?;
        Ok(buffer)
    }

    pub fn decrypt(&self, nonce: &[u8; 12], ciphertext: &[u8], ad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let mut buffer = ciphertext.to_vec();
        let chacha_nonce = ChaChaNonce::from_slice(nonce);
        self.cipher.decrypt_in_place(chacha_nonce, ad, &mut buffer)
            .map_err(|e| CryptoError::DecryptionFailed(e.to_string()))?;
        Ok(buffer)
    }
}

/// AES-256-GCM cipher
pub struct AesCipher {
    cipher: aes_gcm::Aes256Gcm,
}

impl AesCipher {
    pub fn new(key: &[u8; 32]) -> Self {
        Self {
            cipher: aes_gcm::Aes256Gcm::new(aes_gcm::Key::<aes_gcm::Aes256Gcm>::from_slice(key)),
        }
    }

    pub fn encrypt(&self, nonce: &[u8; 12], plaintext: &[u8], ad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let mut buffer = plaintext.to_vec();
        let aes_nonce = aes_gcm::Nonce::from_slice(nonce);
        self.cipher.encrypt_in_place(aes_nonce, ad, &mut buffer)
            .map_err(|e| CryptoError::EncryptionFailed(e.to_string()))?;
        Ok(buffer)
    }

    pub fn decrypt(&self, nonce: &[u8; 12], ciphertext: &[u8], ad: &[u8]) -> Result<Vec<u8>, CryptoError> {
        let mut buffer = ciphertext.to_vec();
        let aes_nonce = aes_gcm::Nonce::from_slice(nonce);
        self.cipher.decrypt_in_place(aes_nonce, ad, &mut buffer)
            .map_err(|e| CryptoError::DecryptionFailed(e.to_string()))?;
        Ok(buffer)
    }
}

/// Crypto errors
#[derive(Debug, thiserror::Error)]
pub enum CryptoError {
    #[error("Encryption failed: {0}")]
    EncryptionFailed(String),
    #[error("Decryption failed: {0}")]
    DecryptionFailed(String),
    #[error("Invalid key")]
    InvalidKey,
}