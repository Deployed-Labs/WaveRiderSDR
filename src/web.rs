use std::path::PathBuf;
use std::sync::Arc;
use std::time::Duration;

use anyhow::Result;
use axum::extract::State;
use axum::response::IntoResponse;
use axum::routing::{get, post};
use axum::{Json, Router};
use serde::{Deserialize, Serialize};
use tokio::net::TcpListener;
use tokio::sync::RwLock;
use tower_http::services::ServeDir;

use crate::band_plan::{get_band, BANDS};
use crate::common::{MeshtasticDeviceInfo, SdrDeviceInfo};
use crate::state::AppState;

pub type SharedState = Arc<RwLock<AppState>>;

#[derive(Debug, Serialize)]
struct StatusResponse {
    running: bool,
    sample_rate: f32,
    center_freq: f32,
    fft_size: usize,
    sdr_connected: bool,
    meshtastic_detected: bool,
    meshtastic_devices: Vec<MeshtasticDeviceInfo>,
    sdr_devices: Vec<SdrDeviceInfo>,
    connected_sdr_id: Option<String>,
    modulation_mode: String,
    morse_enabled: bool,
    morse_text: String,
    signal_strength_db: f32,
    signal_detected: bool,
    source: String,
}

#[derive(Debug, Serialize)]
struct FrameResponse {
    waveform: Vec<f32>,
    waterfall: Vec<Vec<f32>>,
    min_db: f32,
    max_db: f32,
    freq_start_mhz: f32,
    freq_end_mhz: f32,
}

#[derive(Debug, Deserialize)]
pub struct ConfigRequest {
    pub frequency_mhz: Option<f32>,
    pub sample_rate_hz: Option<f32>,
    pub fft_size: Option<usize>,
    pub modulation_mode: Option<String>,
    pub morse_enabled: Option<bool>,
    pub min_db: Option<f32>,
    pub max_db: Option<f32>,
    pub peak_hold: Option<bool>,
    pub squelch_db: Option<f32>,
}

#[derive(Debug, Deserialize)]
pub struct SetBandRequest {
    pub band: String,
}

#[derive(Debug, Deserialize)]
pub struct ConnectSdrRequest {
    pub device_id: String,
}

#[derive(Debug, Serialize)]
pub struct SdrDevicesResponse {
    pub devices: Vec<SdrDeviceInfo>,
    pub connected_sdr_id: Option<String>,
}

pub async fn run_web(host: &str, port: u16) -> Result<()> {
    let state: SharedState = Arc::new(RwLock::new(AppState::default()));
    spawn_update_loop(state.clone());

    let templates_dir = PathBuf::from("templates");

    let app = Router::new()
        .route("/api/status", get(get_status))
        .route("/api/sdr_devices", get(get_sdr_devices))
        .route("/api/connect_sdr", post(connect_sdr))
        .route("/api/disconnect_sdr", post(disconnect_sdr))
        .route("/api/frame", get(get_frame))
        .route("/api/start", post(start))
        .route("/api/stop", post(stop))
        .route("/api/config", post(set_config))
        .route("/api/bands", get(get_bands))
        .route("/api/set_band", post(set_band))
        .nest_service("/", ServeDir::new(templates_dir))
        .with_state(state);

    let addr = format!("{}:{}", host, port);
    let listener = TcpListener::bind(&addr).await?;
    println!("WaveRider SDR web interface on http://{}", addr);
    axum::serve(listener, app).await?;
    Ok(())
}

fn spawn_update_loop(state: SharedState) {
    tokio::spawn(async move {
        let mut ticker = tokio::time::interval(Duration::from_millis(50));
        loop {
            ticker.tick().await;
            let mut guard = state.write().await;
            if guard.running {
                guard.tick();
            }
        }
    });
}

async fn get_status(State(state): State<SharedState>) -> impl IntoResponse {
    let guard = state.read().await;
    let meshtastic_devices = guard.detector.detect_devices();
    let sdr_devices = guard.sdr.detect_devices();
    let connected_sdr_id = guard.sdr.connected_device.as_ref().map(|d| d.id.clone());

    Json(StatusResponse {
        running: guard.running,
        sample_rate: guard.sample_rate,
        center_freq: guard.center_freq,
        fft_size: guard.fft_size,
        sdr_connected: guard.sdr.is_connected,
        meshtastic_detected: !meshtastic_devices.is_empty(),
        meshtastic_devices,
        sdr_devices,
        connected_sdr_id,
        modulation_mode: guard.modulation_mode.clone(),
        morse_enabled: guard.morse_enabled,
        morse_text: guard.morse_decoder.decoded_text.clone(),
        signal_strength_db: guard.signal_strength_db,
        signal_detected: guard.signal_detected,
        source: guard.sdr.source_label(),
    })
}

async fn get_sdr_devices(State(state): State<SharedState>) -> impl IntoResponse {
    let guard = state.read().await;
    Json(SdrDevicesResponse {
        devices: guard.sdr.detect_devices(),
        connected_sdr_id: guard.sdr.connected_device.as_ref().map(|d| d.id.clone()),
    })
}

async fn connect_sdr(
    State(state): State<SharedState>,
    Json(req): Json<ConnectSdrRequest>,
) -> impl IntoResponse {
    let mut guard = state.write().await;
    let ok = guard.sdr.connect(&req.device_id);
    Json(if ok { "connected" } else { "device_not_found" })
}

async fn disconnect_sdr(State(state): State<SharedState>) -> impl IntoResponse {
    let mut guard = state.write().await;
    guard.sdr.disconnect();
    Json("disconnected")
}

async fn get_frame(State(state): State<SharedState>) -> impl IntoResponse {
    let guard = state.read().await;
    let freq_start = (guard.center_freq - guard.sample_rate / 2.0) / 1_000_000.0;
    let freq_end = (guard.center_freq + guard.sample_rate / 2.0) / 1_000_000.0;

    Json(FrameResponse {
        waveform: guard.waveform_data.clone(),
        waterfall: guard.waterfall_data.clone(),
        min_db: guard.waterfall_settings.min_db,
        max_db: guard.waterfall_settings.max_db,
        freq_start_mhz: freq_start,
        freq_end_mhz: freq_end,
    })
}

async fn start(State(state): State<SharedState>) -> impl IntoResponse {
    let mut guard = state.write().await;
    guard.running = true;
    Json("started")
}

async fn stop(State(state): State<SharedState>) -> impl IntoResponse {
    let mut guard = state.write().await;
    guard.running = false;
    Json("stopped")
}

async fn set_config(
    State(state): State<SharedState>,
    Json(req): Json<ConfigRequest>,
) -> impl IntoResponse {
    let mut guard = state.write().await;

    if let Some(freq_mhz) = req.frequency_mhz {
        guard.center_freq = freq_mhz * 1_000_000.0;
        guard.generator.center_freq = guard.center_freq;
    }

    if let Some(sample_rate_hz) = req.sample_rate_hz {
        guard.sample_rate = sample_rate_hz;
        guard.generator.sample_rate = sample_rate_hz;
        guard.demodulator = crate::dsp::Demodulator::new(sample_rate_hz);
        guard.morse_decoder = crate::morse::MorseDecoder::new(sample_rate_hz, 20.0);
    }

    if let Some(fft_size) = req.fft_size {
        guard.fft_size = fft_size.max(128);
        guard.waveform_data = vec![0.0; guard.fft_size];
        guard.waterfall_data = vec![vec![0.0; guard.fft_size]; guard.waterfall_height];
    }

    if let Some(mode) = req.modulation_mode {
        guard.modulation_mode = mode;
    }

    if let Some(enabled) = req.morse_enabled {
        let was_enabled = guard.morse_enabled;
        guard.morse_enabled = enabled;
        if enabled && !was_enabled {
            guard.morse_decoder.reset();
        }
        if enabled && !guard.modulation_mode.eq_ignore_ascii_case("CW") {
            guard.modulation_mode = "CW".to_string();
        }
    }

    if let Some(min_db) = req.min_db {
        guard.waterfall_settings.min_db = min_db;
    }
    if let Some(max_db) = req.max_db {
        guard.waterfall_settings.max_db = max_db;
    }
    if let Some(peak_hold) = req.peak_hold {
        guard.waterfall_settings.peak_hold = peak_hold;
        if !peak_hold {
            guard.waterfall_settings.peak_buffer = None;
        }
    }
    if let Some(squelch_db) = req.squelch_db {
        guard.demodulator.set_squelch(squelch_db);
    }

    Json("ok")
}

async fn get_bands() -> impl IntoResponse {
    Json(BANDS)
}

async fn set_band(
    State(state): State<SharedState>,
    Json(req): Json<SetBandRequest>,
) -> impl IntoResponse {
    let mut guard = state.write().await;

    if let Some(band) = get_band(&req.band) {
        guard.center_freq = band.center_hz as f32;
        guard.generator.center_freq = guard.center_freq;
        guard.modulation_mode = band.mode.to_string();
        Json("ok")
    } else {
        Json("unknown band")
    }
}
