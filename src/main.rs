mod band_plan;
mod common;
mod desktop;
mod dsp;
mod morse;
mod state;
mod web;
mod rtlsdr_capture;
mod hackrf_capture;

use anyhow::Result;
use clap::{Parser, ValueEnum};

#[derive(Debug, Clone, Copy, ValueEnum)]
enum Mode {
    Auto,
    Web,
    Desktop,
}

#[derive(Debug, Parser)]
#[command(name = "waverider_sdr")]
#[command(about = "WaveRider SDR Rust launcher")]
struct Cli {
    #[arg(long, value_enum, default_value_t = Mode::Auto)]
    mode: Mode,

    #[arg(long, default_value = "0.0.0.0")]
    host: String,

    #[arg(long, default_value_t = 5000)]
    port: u16,
}

#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter("info")
        .without_time()
        .init();

    let cli = Cli::parse();
    print_banner();

    let mode = match cli.mode {
        Mode::Auto => detect_mode(),
        Mode::Web => Mode::Web,
        Mode::Desktop => Mode::Desktop,
    };

    match mode {
        Mode::Web => web::run_web(&cli.host, cli.port).await?,
        Mode::Desktop => desktop::run_desktop()?,
        Mode::Auto => unreachable!("auto should be resolved"),
    }

    Ok(())
}

fn detect_mode() -> Mode {
    #[cfg(target_os = "linux")]
    {
        if std::env::var("DISPLAY").is_ok() {
            return Mode::Web;
        }
        return Mode::Web;
    }

    #[cfg(any(target_os = "windows", target_os = "macos"))]
    {
        Mode::Web
    }

    #[cfg(not(any(target_os = "linux", target_os = "windows", target_os = "macos")))]
    {
        Mode::Web
    }
}

fn print_banner() {
    println!(
        "\n============================================================\n  WAVERIDER SDR (RUST)\n  Universal Cross-Platform Launcher\n============================================================\n"
    );
}
