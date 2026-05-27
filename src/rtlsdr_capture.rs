use anyhow::{anyhow, Result};
use num_complex::Complex32;
use std::io::Read;
use std::process::{Command, Stdio};
use std::sync::{Arc, Mutex};

/// RTL-SDR IQ capture backend using rtl_fm subprocess
#[derive(Debug)]
pub struct RtlSdrCapture {
    device_index: u32,
    process: Arc<Mutex<Option<std::process::Child>>>,
}

impl RtlSdrCapture {
    /// Create a new RTL-SDR capture instance
    pub fn new() -> Result<Self> {
        // Verify rtl_fm exists
        let output = if cfg!(target_os = "windows") {
            Command::new("where")
                .arg("rtl_fm")
                .output()
        } else {
            Command::new("which")
                .arg("rtl_fm")
                .output()
        };

        match output {
            Ok(o) if o.status.success() => Ok(Self {
                device_index: 0,
                process: Arc::new(Mutex::new(None)),
            }),
            _ => Err(anyhow!("rtl_fm not found in PATH")),
        }
    }

    /// Connect to the RTL-SDR device
    pub fn connect(&self) -> Result<()> {
        // Connection is lazy - we start the process when reading samples
        Ok(())
    }

    /// Disconnect from the device
    pub fn disconnect(&self) {
        if let Ok(mut proc_opt) = self.process.lock() {
            if let Some(mut child) = proc_opt.take() {
                let _ = child.kill();
                let _ = child.wait();
            }
        }
    }

    /// Read IQ samples from the device via rtl_fm subprocess
    pub fn read_samples(
        &self,
        num_samples: usize,
        sample_rate: f32,
        center_freq: f32,
    ) -> Result<Vec<Complex32>> {
        // Start rtl_fm process if not already running
        // rtl_fm output format: raw IQ samples as interleaved 8-bit unsigned
        // Usage: rtl_fm -f <freq> -s <sample_rate> -
        
        let freq_hz = center_freq as i64;
        let sample_rate_int = sample_rate as u32;
        
        // Create the rtl_fm command
        let mut cmd = Command::new("rtl_fm");
        cmd.arg("-d")
            .arg(self.device_index.to_string())
            .arg("-f")
            .arg(freq_hz.to_string())
            .arg("-s")
            .arg(sample_rate_int.to_string())
            .arg("-")
            .stdout(Stdio::piped())
            .stderr(Stdio::null());

        let mut child = cmd.spawn()
            .map_err(|e| anyhow!("Failed to spawn rtl_fm: {}", e))?;

        // Read raw IQ data
        let stdout = child.stdout.take()
            .ok_or_else(|| anyhow!("Could not capture rtl_fm stdout"))?;
        
        let mut reader = std::io::BufReader::new(stdout);
        let mut buffer = vec![0u8; num_samples * 2];
        
        reader.read_exact(&mut buffer)
            .map_err(|e| anyhow!("Failed to read samples: {}", e))?;

        // Kill the process after reading
        let _ = child.kill();
        let _ = child.wait();

        // Convert 8-bit unsigned samples to Complex32
        let mut samples = Vec::with_capacity(num_samples);
        for i in 0..num_samples {
            let i_raw = buffer[2 * i] as f32;
            let q_raw = buffer[2 * i + 1] as f32;

            // Normalize from [0, 255] to [-1, 1]
            let i_norm = (i_raw - 127.5) / 127.5;
            let q_norm = (q_raw - 127.5) / 127.5;

            samples.push(Complex32::new(i_norm, q_norm));
        }

        Ok(samples)
    }

    /// List available RTL-SDR devices
    #[allow(dead_code)]
    pub fn list_devices() -> Vec<String> {
        // Use rtl_test to enumerate devices
        if let Ok(output) = Command::new("rtl_test")
            .arg("-t")
            .output()
        {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                return stdout
                    .lines()
                    .filter(|line| line.contains("Found") || line.contains("Device"))
                    .map(|s| s.to_string())
                    .collect();
            }
        }
        
        vec!["RTL-SDR #0".to_string()]
    }
}

impl Default for RtlSdrCapture {
    fn default() -> Self {
        Self::new().unwrap_or_else(|_| Self {
            device_index: 0,
            process: Arc::new(Mutex::new(None)),
        })
    }
}

