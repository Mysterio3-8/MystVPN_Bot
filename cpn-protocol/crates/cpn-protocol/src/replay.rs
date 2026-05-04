//! Защита от replay-атак

use std::sync::atomic::{AtomicU64, Ordering};

/// Окно для защиты от replay-атак
pub struct ReplayWindow {
    bits: [AtomicU64; 16],
    lower: AtomicU64,
}

impl ReplayWindow {
    /// Создает новое окно
    pub fn new() -> Self {
        Self {
            bits: Default::default(),
            lower: AtomicU64::new(0),
        }
    }

    /// Проверяет, является ли пакет новым
    /// Возвращает false, если это повторная передача
    pub fn check(&self, sequence: u64) -> bool {
        let lower = self.lower.load(Ordering::Acquire);

        if sequence < lower {
            return false;
        }

        if sequence >= lower + 1024 {
            self.expand_window(sequence);
        }

        let idx = (sequence / 64) % 16;
        let bit = sequence % 64;
        let mask = 1u64 << bit;

        let bits = self.bits[idx as usize].load(Ordering::Acquire);
        if (bits & mask) != 0 {
            return false;
        }

        self.bits[idx as usize].fetch_or(mask, Ordering::Release);
        true
    }

    fn expand_window(&self, new_sequence: u64) {
        let mut lower = self.lower.load(Ordering::Acquire);

        loop {
            if new_sequence < lower + 1024 {
                break;
            }

            let new_lower = lower + 64;

            match self.lower.compare_exchange_weak(
                lower,
                new_lower,
                Ordering::SeqCst,
                Ordering::Acquire,
            ) {
                Ok(_) => {
                    let old_idx = (lower / 64) % 16;
                    self.bits[old_idx as usize].store(0, Ordering::Release);
                    lower = new_lower;
                }
                Err(l) => lower = l,
            }
        }
    }
}

impl Default for ReplayWindow {
    fn default() -> Self {
        Self::new()
    }
}