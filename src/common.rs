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

#[derive(Debug, Clone)]
pub struct MeshtasticDetector;

impl MeshtasticDetector {
    pub fn detect_devices(&self) -> Vec<String> {
        Vec::new()
    }
}

#[derive(Debug, Clone)]
pub struct SdrDevice {
    pub is_connected: bool,
}

impl Default for SdrDevice {
    fn default() -> Self {
        Self { is_connected: false }
    }
}
