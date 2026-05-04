//! CPN packet handling

use crate::types::{EncryptedCpnPacket, Nonce, SequenceNumber};
use crate::crypto::{AesCipher, AeadCipher, CryptoError};

/// Maximum payload size
const MAX_PAYLOAD_SIZE: usize = 65535;

/// CPN Packet
#[derive(Debug, Clone)]
pub struct CpnPacket {
    pub nonce: Nonce,
    pub sequence: SequenceNumber,
    pub payload: Vec<u8>,
}

impl CpnPacket {
    pub fn new(nonce: Nonce, sequence: SequenceNumber, payload: Vec<u8>) -> Self {
        Self {
            nonce,
            sequence,
            payload,
        }
    }

    pub fn encrypt(mut self, key: &[u8; 32]) -> Result<EncryptedCpnPacket, PacketError> {
        let padding_len = rand::random::<u8>() as usize;
        let original_len = self.payload.len();
        
        self.payload.push(original_len as u8);
        self.payload.extend_from_slice(&[0u8; 0]);
        self.payload.resize(self.payload.len() + padding_len, 0);

        let cipher = AeadCipher::new(key);
        let ciphertext = cipher.encrypt(&self.nonce, &self.payload, b"CPN")
            .map_err(|e| PacketError::EncryptionFailed(e.to_string()))?;
        
        Ok(EncryptedCpnPacket {
            nonce: self.nonce,
            sequence: self.sequence,
            ciphertext,
            tag: [0u8; 16],
        })
    }

    pub fn decrypt(packet: EncryptedCpnPacket, key: &[u8; 32]) -> Result<Self, PacketError> {
        let cipher = AeadCipher::new(key);
        let plaintext = cipher.decrypt(&packet.nonce, &packet.ciphertext, b"CPN")
            .map_err(|e| PacketError::DecryptionFailed(e.to_string()))?;
        
        if plaintext.is_empty() {
            return Err(PacketError::InvalidPayload);
        }

        let len_byte = plaintext[plaintext.len() - 1];
        let payload_len = len_byte as usize;
        
        if payload_len > plaintext.len() {
            return Err(PacketError::InvalidPayload);
        }

        let payload = plaintext[..plaintext.len() - 1 - (plaintext.len() - 1 - payload_len)].to_vec();
        
        Ok(Self {
            nonce: packet.nonce,
            sequence: packet.sequence,
            payload,
        })
    }
}

/// Packet errors
#[derive(Debug, thiserror::Error)]
pub enum PacketError {
    #[error("Encryption failed: {0}")]
    EncryptionFailed(String),
    
    #[error("Decryption failed: {0}")]
    DecryptionFailed(String),
    
    #[error("Authentication failed")]
    AuthenticationFailed,
    
    #[error("Invalid packet format")]
    InvalidPacketFormat,
    
    #[error("Invalid payload")]
    InvalidPayload,
    
    #[error("Invalid tag length")]
    InvalidTagLength,
    
    #[error("Payload too large")]
    PayloadTooLarge,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_packet_roundtrip() {
        let key = [0u8; 32];
        let nonce = [0u8; 12];
        let packet = CpnPacket::new(nonce, 1, b"test data".to_vec());

        let encrypted = packet.encrypt(&key).unwrap();
        let decrypted = CpnPacket::decrypt(encrypted, &key).unwrap();
        
        assert_eq!(decrypted.payload, b"test data");
    }
}