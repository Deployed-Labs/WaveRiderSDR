use std::process::Command;

use serde::Serialize;
use serialport::SerialPortType;

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
    pub name: String,
    pub description: String,
}

#[derive(Debug, Clone)]
pub struct SdrDevice {
    pub is_connected: bool,
    pub connected_device: Option<SdrDeviceInfo>,
}

impl Default for SdrDevice {
    fn default() -> Self {
        Self {
            is_connected: false,
            connected_device: None,
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
                name: "RTL-SDR (rtl_test detected)".to_string(),
                description: "RTL-SDR tooling found on system PATH".to_string(),
            });
        }

        if command_exists("SoapySDRUtil") {
            devices.push(SdrDeviceInfo {
                id: "hackrf_0".to_string(),
                device_type: "HackRF".to_string(),
                name: "HackRF (SoapySDR detected)".to_string(),
                description: "SoapySDR tooling found on system PATH".to_string(),
            });
        }

        devices
    }

    pub fn connect(&mut self, device_id: &str) -> bool {
        let devices = self.detect_devices();
        if let Some(device) = devices.into_iter().find(|d| d.id == device_id) {
            self.is_connected = true;
            self.connected_device = Some(device);
            true
        } else {
            self.is_connected = false;
            self.connected_device = None;
            false
        }
    }

    pub fn disconnect(&mut self) {
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
}

fn command_exists(command: &str) -> bool {
    #[cfg(target_os = "windows")]
    let output = Command::new("where").arg(command).output();

    #[cfg(not(target_os = "windows"))]
    let output = Command::new("which").arg(command).output();

    output.map(|o| o.status.success()).unwrap_or(false)
}
