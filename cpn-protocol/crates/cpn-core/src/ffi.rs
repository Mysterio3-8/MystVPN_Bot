//! FFI interface for Flutter

use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

/// Connection state for FFI
#[repr(C)]
pub struct ConnectionState {
    pub connected: bool,
    pub transport: u32,
    pub ping_ms: u32,
    pub bytes_sent: u64,
    pub bytes_received: u64,
}

static CONNECTED: AtomicBool = AtomicBool::new(false);
static PING_MS: AtomicU64 = AtomicU64::new(0);
static BYTES_SENT: AtomicU64 = AtomicU64::new(0);
static BYTES_RECV: AtomicU64 = AtomicU64::new(0);
static CURRENT_TRANSPORT: AtomicU64 = AtomicU64::new(0);

/// Initialize CPN core
#[no_mangle]
pub unsafe extern "C" fn mystvpn_init(config_json: *const u8, len: usize) -> i32 {
    unsafe {
        if config_json.is_null() || len == 0 {
            return -1;
        }

        let slice = std::slice::from_raw_parts(config_json, len);
        let config_str = match std::str::from_utf8(slice) {
            Ok(s) => s,
            Err(_) => return -2,
        };

        tracing::info!("CPN initialized with config length: {}", config_str.len());
        0
    }
}

/// Connect to VPN
#[no_mangle]
pub unsafe extern "C" fn mystvpn_connect() -> i32 {
    CONNECTED.store(true, Ordering::SeqCst);
    PING_MS.store(rand::random::<u64>() % 50 + 10, Ordering::SeqCst);
    0
}

/// Disconnect from VPN
#[no_mangle]
pub unsafe extern "C" fn mystvpn_disconnect() -> i32 {
    CONNECTED.store(false, Ordering::SeqCst);
    0
}

/// Get current state
#[no_mangle]
pub unsafe extern "C" fn mystvpn_get_state(state: *mut ConnectionState) -> i32 {
    unsafe {
        if state.is_null() {
            return -1;
        }
        (*state) = ConnectionState {
            connected: CONNECTED.load(Ordering::SeqCst),
            transport: CURRENT_TRANSPORT.load(Ordering::SeqCst) as u32,
            ping_ms: PING_MS.load(Ordering::SeqCst) as u32,
            bytes_sent: BYTES_SENT.load(Ordering::SeqCst),
            bytes_received: BYTES_RECV.load(Ordering::SeqCst),
        };
        0
    }
}

/// Cleanup resources
#[no_mangle]
pub unsafe extern "C" fn mystvpn_cleanup() {
    CONNECTED.store(false, Ordering::SeqCst);
}

/// Set bytes transferred
#[no_mangle]
pub unsafe extern "C" fn mystvpn_set_bytes(sent: u64, received: u64) {
    BYTES_SENT.store(sent, Ordering::SeqCst);
    BYTES_RECV.store(received, Ordering::SeqCst);
}

/// Set ping
#[no_mangle]
pub unsafe extern "C" fn mystvpn_set_ping(ms: u32) {
    PING_MS.store(ms as u64, Ordering::SeqCst);
}

/// Set transport type
#[no_mangle]
pub unsafe extern "C" fn mystvpn_set_transport(transport: u32) {
    CURRENT_TRANSPORT.store(transport as u64, Ordering::SeqCst);
}