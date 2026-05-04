//! CPN HUB - Universal VPN Client

mod commands;

use clap::{Parser, Subcommand};
use commands::{connect, import, run_service, show_status, generate_config};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "cpn-hub")]
#[command(about = "CPN Universal VPN Client", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Connect with a configuration file
    Connect {
        /// Path to .cpn configuration file
        #[arg(short, long)]
        config: PathBuf,
        
        /// Enable debug logging
        #[arg(short, long)]
        debug: bool,
    },
    /// Import key bundle from URI or file
    Import {
        /// Key URI (mystvpn://...) or path to file
        #[arg(short, long)]
        source: String,
    },
    /// Run as system service
    Service {
        /// Config directory
        #[arg(short, long, default_value = "config")]
        config_dir: PathBuf,
    },
    /// Show status
    Status,
    /// Generate a test configuration
    GenConfig {
        /// Output file path
        #[arg(short, long)]
        output: PathBuf,
    },
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Connect { config, debug } => connect(config, debug).await,
        Commands::Import { source } => import(source).await,
        Commands::Service { config_dir: _ } => run_service().await,
        Commands::Status => show_status().await,
        Commands::GenConfig { output } => generate_config(output).await,
    }
}