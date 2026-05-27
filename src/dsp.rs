use num_complex::Complex32;
use rand::Rng;
use rand_distr::{Distribution, Normal};
use rustfft::FftPlanner;

#[derive(Debug, Clone)]
pub struct SignalGenerator {
    pub sample_rate: f32,
    pub center_freq: f32,
    time: f32,
}

impl SignalGenerator {
    pub fn new(sample_rate: f32, center_freq: f32) -> Self {
        Self {
            sample_rate,
            center_freq,
            time: 0.0,
        }
    }

    pub fn generate_samples(&mut self, count: usize) -> Vec<Complex32> {
        let mut out = Vec::with_capacity(count);
        let dt = 1.0 / self.sample_rate;
        let noise = Normal::new(0.0, 0.1).expect("normal distribution");
        let mut rng = rand::thread_rng();

        for i in 0..count {
            let t = self.time + (i as f32) * dt;

            let c0 = Complex32::from_polar(1.0, 2.0 * std::f32::consts::PI * 0.0 * t);
            let c1 = Complex32::from_polar(
                0.3,
                2.0 * std::f32::consts::PI * (self.sample_rate * 0.15) * t,
            );
            let c2 = Complex32::from_polar(
                0.2,
                2.0 * std::f32::consts::PI * (self.sample_rate * -0.2) * t,
            );
            let modulation = 0.05 * (2.0 * std::f32::consts::PI * 1000.0 * t).sin();
            let c3 = Complex32::from_polar(
                0.4,
                2.0 * std::f32::consts::PI * (self.sample_rate * 0.3) * t + modulation,
            );

            let n = Complex32::new(noise.sample(&mut rng) as f32, noise.sample(&mut rng) as f32);
            out.push(c0 + c1 + c2 + c3 + n);
        }

        self.time += (count as f32) * dt;
        out
    }
}

pub fn compute_fft_db(samples: &[Complex32], fft_size: usize) -> Vec<f32> {
    let mut planner = FftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(fft_size);

    let mut buffer = vec![Complex32::new(0.0, 0.0); fft_size];
    for (i, sample) in samples.iter().take(fft_size).enumerate() {
        let w = 0.54
            - 0.46
                * ((2.0 * std::f32::consts::PI * i as f32) / ((samples.len().max(1) - 1) as f32)).cos();
        buffer[i] = *sample * w;
    }

    fft.process(&mut buffer);

    let half = fft_size / 2;
    let mut shifted = vec![0.0f32; fft_size];
    for i in 0..fft_size {
        let src_idx = (i + half) % fft_size;
        let mag = buffer[src_idx].norm();
        shifted[i] = 20.0 * (mag + 1e-10).log10();
    }
    shifted
}

#[derive(Debug, Clone)]
pub struct Demodulator {
    sample_rate: f32,
    pub squelch_db: f32,
}

impl Demodulator {
    pub fn new(sample_rate: f32) -> Self {
        Self {
            sample_rate,
            squelch_db: -50.0,
        }
    }

    pub fn set_squelch(&mut self, value_db: f32) {
        self.squelch_db = value_db;
    }

    pub fn detect_signal(&self, samples: &[Complex32]) -> bool {
        self.signal_strength_db(samples) >= self.squelch_db
    }

    pub fn signal_strength_db(&self, samples: &[Complex32]) -> f32 {
        if samples.is_empty() {
            return -120.0;
        }
        let sum: f32 = samples.iter().map(|s| s.norm_sqr()).sum();
        let rms = (sum / samples.len() as f32).sqrt();
        20.0 * (rms + 1e-10).log10()
    }

    pub fn demodulate_cw(&self, samples: &[Complex32]) -> Vec<f32> {
        samples.iter().map(|s| s.norm()).collect()
    }

    pub fn _sample_rate(&self) -> f32 {
        self.sample_rate
    }
}
