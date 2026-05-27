use std::process::Command;
use std::sync::{Arc, Mutex};

use num_complex::Complex32;
use serde::Serialize;
use serialport::SerialPortType;
use crate::rtlsdr_capture::RtlSdrCapture;
use crate::hackrf_capture::HackRfCapture;

#[derive(Debug, Clone)]
pub struct WaterfallSettings {
    pub min_db: f32,
    pub max_db: f32,
    pub peak_hold: bool,
    pub peak_buffer: Option<Vec<f32>>,
}

impl Default for WaterfallSettings {
    fn default() -> Self {
        Self {
            min_db: -80.0,
            max_db: 0.0,
            peak_hold: false,
            peak_buffer: None,
        }
    }
}

impl WaterfallSettings {
    pub fn apply_processing(&mut self, spectrum: &[f32]) -> Vec<f32> {
        let mut out = spectrum.to_vec();

        if self.peak_hold {
            match &mut self.peak_buffer {
                Some(peak) if peak.len() == out.len() => {
                    for (p, v) in peak.iter_mut().zip(out.iter()) {
                        *p = p.max(*v);
                    }
                    out.clone_from(peak);
                }
                _ => {
                    self.peak_buffer = Some(out.clone());
                }
            }
        } else {
            self.peak_buffer = None;
        }

        for v in &mut out {
            *v = v.clamp(self.min_db, self.max_db);
        }

        out
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct MeshtasticDeviceInfo {
    pub port: String,
    pub vid: Option<u16>,
    pub pid: Option<u16>,
    pub manufacturer: Option<String>,
    pub product: Option<String>,
}

#[derive(Debug, Clone)]
pub struct MeshtasticDetector;

impl MeshtasticDetector {
    pub fn detect_devices(&self) -> Vec<MeshtasticDeviceInfo> {
        const MESHTASTIC_VIDS: [u16; 4] = [0x239A, 0x303A, 0x10C4, 0x1A86];

        let ports = match serialport::available_ports() {
            Ok(p) => p,
            Err(_) => return Vec::new(),
        };

        ports
            .into_iter()
            .filter_map(|p| match p.port_type {
                SerialPortType::UsbPort(info)
                    if MESHTASTIC_VIDS.contains(&info.vid)
                        || info
                            .product
                            .as_deref()
                            .unwrap_or_default()
                            .to_ascii_lowercase()
                            .contains("meshtastic") =>
                {
                    Some(MeshtasticDeviceInfo {
                        port: p.port_name,
                        vid: Some(info.vid),
                        pid: Some(info.pid),
                        manufacturer: info.manufacturer,
                        product: info.product,
                    })
                }
                _ => None,
            })
            .collect()
    }
}

#[derive(Debug, Clone, Serialize)]
pub struct SdrDeviceInfo {
    pub id: String,
    pub device_type: String,
    pub backend: String,
    pub name: String,
    pub description: String,
}

#[derive(Clone)]
pub struct SdrDevice {
    pub is_connected: bool,
    pub connected_device: Option<SdrDeviceInfo>,
    rtlsdr_capture: Arc<Mutex<Option<Box<RtlSdrCapture>>>>,
    hackrf_capture: Arc<Mutex<Option<Box<HackRfCapture>>>>,
}

impl std::fmt::Debug for SdrDevice {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("SdrDevice")
            .field("is_connected", &self.is_connected)
            .field("connected_device", &self.connected_device)
            .finish()
    }
}

impl Default for SdrDevice {
    fn default() -> Self {
        Self {
            is_connected: false,
            connected_device: None,
            rtlsdr_capture: Arc::new(Mutex::new(None)),
            hackrf_capture: Arc::new(Mutex::new(None)),
        }
    }
}

impl SdrDevice {
    pub fn detect_devices(&self) -> Vec<SdrDeviceInfo> {
        let mut devices = Vec::new();

        if command_exists("rtl_test") {
            devices.push(SdrDeviceInfo {
                id: "rtl_sdr_0".to_string(),
                device_type: "RTL-SDR".to_string(),
                backend: "rtlsdr".to_string(),
                name: "RTL-SDR (rtl_test detected)".to_string(),
                description: "RTL-SDR tooling found on system PATH".to_string(),
            });
        }

        if command_exists("SoapySDRUtil") {
            devices.push(SdrDeviceInfo {
                id: "hackrf_0".to_string(),
                device_type: "HackRF".to_string(),
                backend: "hackrf".to_string(),
                name: "HackRF (SoapySDR detected)".to_string(),
                description: "SoapySDR tooling found on system PATH".to_string(),
            });
        }

        devices
    }

    pub fn connect(&mut self, device_id: &str) -> bool {
        let devices = self.detect_devices();
        if let Some(device) = devices.into_iter().find(|d| d.id == device_id) {
            // Initialize the appropriate capture backend
            match device.backend.as_str() {
                "rtlsdr" => {
                    if let Ok(capture) = RtlSdrCapture::new() {
                        if capture.connect().is_ok() {
                            *self.rtlsdr_capture.lock().unwrap() = Some(Box::new(capture));
                            self.is_connected = true;
                            self.connected_device = Some(device);
                            return true;
                        }
                    }
                }
                "hackrf" => {
                    if let Ok(capture) = HackRfCapture::new() {
                        if capture.connect().is_ok() {
                            *self.hackrf_capture.lock().unwrap() = Some(Box::new(capture));
                            self.is_connected = true;
                            self.connected_device = Some(device);
                            return true;
                        }
                    }
                }
                _ => {}
            }
            self.is_connected = false;
            self.connected_device = None;
            false
        } else {
            self.is_connected = false;
            self.connected_device = None;
            false
        }
    }

    pub fn disconnect(&mut self) {
        // Disconnect both backends
        if let Ok(ref mut capture) = self.rtlsdr_capture.lock() {
            if let Some(ref mut c) = capture.as_mut() {
                c.disconnect();
            }
        }
        if let Ok(ref mut capture) = self.hackrf_capture.lock() {
            if let Some(ref mut c) = capture.as_mut() {
                c.disconnect();
            }
        }
        
        *self.rtlsdr_capture.lock().unwrap() = None;
        *self.hackrf_capture.lock().unwrap() = None;
        
        self.is_connected = false;
        self.connected_device = None;
    }

    pub fn source_label(&self) -> String {
        if let Some(dev) = &self.connected_device {
            format!("{} ({})", dev.device_type, dev.name)
        } else {
            "Simulated".to_string()
        }
    }

    pub fn read_samples(
        &self,
        num_samples: usize,
        sample_rate: f32,
        center_freq: f32,
    ) -> Result<Vec<Complex32>, String> {
        let Some(device) = &self.connected_device else {
            return Err("No SDR device connected".to_string());
        };

        match device.backend.as_str() {
            "rtlsdr" => {
                let capture_lock = self.rtlsdr_capture.lock()
                    .map_err(|e| format!("Failed to lock RTL-SDR capture: {}", e))?;
                
                if let Some(capture) = capture_lock.as_ref() {
                    capture.read_samples(num_samples, sample_rate, center_freq)
                        .map_err(|e| format!("Failed to read samples from RTL-SDR: {}", e))
                } else {
                    Err("RTL-SDR device not connected".to_string())
                }
            }
            "hackrf" => {
                let capture_lock = self.hackrf_capture.lock()
                    .map_err(|e| format!("Failed to lock HackRF capture: {}", e))?;
                
                if let Some(capture) = capture_lock.as_ref() {
                    capture.read_samples(num_samples, sample_rate, center_freq)
                        .map_err(|e| format!("Failed to read samples from HackRF: {}", e))
                } else {
                    Err("HackRF device not connected".to_string())
                }
            }
            _ => Err("Unknown SDR backend".to_string()),
        }
    }
}

fn command_exists(command: &str) -> bool {
    #[cfg(target_os = "windows")]
    let output = Command::new("where").arg(command).output();

    #[cfg(not(target_os = "windows"))]
    let output = Command::new("which").arg(command).output();

    output.map(|o| o.status.success()).unwrap_or(false)
}
