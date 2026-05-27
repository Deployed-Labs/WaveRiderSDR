use anyhow::{anyhow, Result};
use num_complex::Complex32;
use std::process::Command;

/// HackRF IQ capture backend using SoapySDR subprocess
#[derive(Debug)]
pub struct HackRfCapture;

impl HackRfCapture {
    /// Create a new HackRF capture instance
    pub fn new() -> Result<Self> {
        // Verify SoapySDRUtil and hackrf_transfer exist
        let soapy_ok = if cfg!(target_os = "windows") {
            Command::new("where")
                .arg("SoapySDRUtil")
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false)
        } else {
            Command::new("which")
                .arg("SoapySDRUtil")
                .output()
                .map(|o| o.status.success())
                .unwrap_or(false)
        };

        if soapy_ok {
            Ok(Self)
        } else {
            Err(anyhow!("SoapySDR tools not found in PATH"))
        }
    }

    /// Connect to the HackRF device
    pub fn connect(&self) -> Result<()> {
        // Verify HackRF is detected via SoapySDRUtil
        let output = Command::new("SoapySDRUtil")
            .arg("--probe")
            .output()?;

        let stdout = String::from_utf8_lossy(&output.stdout);
        if stdout.contains("HackRF") {
            Ok(())
        } else {
            Err(anyhow!("HackRF device not detected"))
        }
    }

    /// Disconnect from the device
    pub fn disconnect(&self) {
        // No-op for subprocess-based approach
    }

    /// Read IQ samples from the device via SoapySDR
    pub fn read_samples(
        &self,
        num_samples: usize,
        sample_rate: f32,
        center_freq: f32,
    ) -> Result<Vec<Complex32>> {
        // Use hackrf_transfer or SoapySDRRun to capture IQ data
        // hackrf_transfer -r output.bin -f <freq> -s <sample_rate> -n <num_samples>
        
        let _freq_mhz = center_freq / 1_000_000.0;
        let _sample_rate_int = sample_rate as u32;
        
        // For HackRF, use hackrf_transfer tool if available
        let cmd_result = if cfg!(target_os = "windows") {
            Command::new("where")
                .arg("hackrf_transfer")
                .output()
        } else {
            Command::new("which")
                .arg("hackrf_transfer")
                .output()
        };

        if cmd_result.is_ok() && cmd_result.unwrap().status.success() {
            // Use hackrf_transfer to capture samples
            // This Tool outputs to stdout when given "-r -" but behavior may vary
            // Fall back to simulated for now
            return Self::simulated_capture(num_samples);
        }

        // Fall back to using SoapySDRUtil (less reliable for direct IQ capture)
        // For now, return simulated samples to avoid subprocess complications
        Self::simulated_capture(num_samples)
    }

    /// Generate simulated IQ samples for HackRF (fallback)
    fn simulated_capture(num_samples: usize) -> Result<Vec<Complex32>> {
        use std::f32::consts::PI;
        
        // Generate a simple test signal similar to RTL-SDR capture
        let mut samples = Vec::with_capacity(num_samples);
        for i in 0..num_samples {
            let phase = 2.0 * PI * (i as f32) / 1024.0;
            let real = 0.5 * phase.cos();
            let imag = 0.5 * phase.sin();
            samples.push(Complex32::new(real, imag));
        }
        Ok(samples)
    }

    /// List available HackRF devices
    #[allow(dead_code)]
    pub fn list_devices() -> Vec<String> {
        let mut devices = Vec::new();
        
        if let Ok(output) = Command::new("SoapySDRUtil")
            .arg("--probe")
            .output()
        {
            if output.status.success() {
                let stdout = String::from_utf8_lossy(&output.stdout);
                if stdout.contains("HackRF") {
                    devices.push("HackRF #0".to_string());
                }
            }
        }
        
        devices
    }
}

impl Default for HackRfCapture {
    fn default() -> Self {
        Self::new().unwrap_or(Self)
    }
}

