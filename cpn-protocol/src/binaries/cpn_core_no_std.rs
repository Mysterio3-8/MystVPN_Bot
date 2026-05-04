//! CPN PROTOCOL - Simplified build without external C dependencies

#![no_std]
#![no_main]

use core::ffi::{c_char, c_int, c_uchar, c_ulong, c_void};
use core::panic::PanicInfo;

#[repr(C)]
pub struct ConnectionState {
    pub connected: bool,
    pub transport: u32,
    pub ping_ms: u32,
    pub bytes_sent: u64,
    pub bytes_received: u64,
}

static mut STATE: ConnectionState = ConnectionState {
    connected: false,
    transport: 0,
    ping_ms: 0,
    bytes_sent: 0,
    bytes_received: 0,
};

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}

#[no_mangle]
pub extern "C" fn mystvpn_init(_config_json: *const c_uchar, _len: usize) -> c_int {
    0
}

#[no_mangle]
pub extern "C" fn mystvpn_connect() -> c_int {
    unsafe { STATE.connected = true; }
    0
}

#[no_mangle]
pub extern "C" fn mystvpn_disconnect() -> c_int {
    unsafe { STATE.connected = false; }
    0
}

#[no_mangle]
pub extern "C" fn mystvpn_get_state(state: *mut ConnectionState) -> c_int {
    unsafe {
        if state.is_null() {
            return -1;
        }
        core::ptr::copy(&STATE, state, 1);
    }
    0
}

#[no_mangle]
pub extern "C" fn mystvpn_cleanup() {
    unsafe { STATE.connected = false; }
}