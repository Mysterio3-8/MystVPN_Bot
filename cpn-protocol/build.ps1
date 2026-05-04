#!/usr/bin/env pwsh
# Build script for CPN protocol
# Requires: Rust 1.78+, OpenSSL

Write-Host "Building CPN Protocol..." -ForegroundColor Green

# Set up environment
$env:OPENSSL_DIR = "C:\OpenSSL-Win64"
$env:OPENSSL_LIB_DIR = "$env:OPENSSL_DIR\lib"
$env:OPENSSL_INCLUDE_DIR = "$env:OPENSSL_DIR\include"

# Build in release mode
Write-Host "Building in release mode..." -ForegroundColor Yellow
cargo build --release

if ($LASTEXITCODE -eq 0) {
    Write-Host "Build successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Executables:" -ForegroundColor Cyan
    Write-Host "  - target/release/cpn-client.exe"
    Write-Host "  - target/release/cpn-entry-server.exe"
    Write-Host "  - target/release/cpn-exit-server.exe"
    Write-Host "  - target/release/cpn-control-server.exe"
} else {
    Write-Host "Build failed!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure you have:" -ForegroundColor Yellow
    Write-Host "  1. Visual Studio 2017+ with C++ tools"
    Write-Host "  2. OpenSSL installed"
    Write-Host "  3. Rust toolchain installed"
    exit 1
}
