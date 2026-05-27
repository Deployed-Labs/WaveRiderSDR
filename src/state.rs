use crate::common::{MeshtasticDetector, SdrDevice, WaterfallSettings};
use crate::dsp::{compute_fft_db, Demodulator, SignalGenerator};
use crate::morse::MorseDecoder;

#[derive(Debug, Clone)]
pub struct AppState {
    pub running: bool,
    pub sample_rate: f32,
    pub center_freq: f32,
    pub fft_size: usize,
    pub waterfall_height: usize,
    pub waterfall_data: Vec<Vec<f32>>,
    pub waveform_data: Vec<f32>,
    pub generator: SignalGenerator,
    pub detector: MeshtasticDetector,
    pub sdr: SdrDevice,
    pub demodulator: Demodulator,
    pub morse_decoder: MorseDecoder,
    pub modulation_mode: String,
    pub morse_enabled: bool,
    pub signal_strength_db: f32,
    pub signal_detected: bool,
    pub waterfall_settings: WaterfallSettings,
}

impl Default for AppState {
    fn default() -> Self {
        let sample_rate = 2_400_000.0;
        let center_freq = 100_000_000.0;
        let fft_size = 1024;
        let waterfall_height = 100;

        Self {
            running: false,
            sample_rate,
            center_freq,
            fft_size,
            waterfall_height,
            waterfall_data: vec![vec![0.0; fft_size]; waterfall_height],
            waveform_data: vec![0.0; fft_size],
            generator: SignalGenerator::new(sample_rate, center_freq),
            detector: MeshtasticDetector,
            sdr: SdrDevice::default(),
            demodulator: Demodulator::new(sample_rate),
            morse_decoder: MorseDecoder::new(sample_rate, 20.0),
            modulation_mode: "None".to_string(),
            morse_enabled: false,
            signal_strength_db: -120.0,
            signal_detected: false,
            waterfall_settings: WaterfallSettings::default(),
        }
    }
}

impl AppState {
    pub fn tick(&mut self) {
        let samples = self.generator.generate_samples(self.fft_size);
        self.signal_strength_db = self.demodulator.signal_strength_db(&samples);
        self.signal_detected = self.demodulator.detect_signal(&samples);

        if self.morse_enabled && self.modulation_mode.eq_ignore_ascii_case("CW") {
            let env = self.demodulator.demodulate_cw(&samples);
            let _ = self.morse_decoder.process_samples(&env);
        }

        let fft_db = compute_fft_db(&samples, self.fft_size);
        let processed = self.waterfall_settings.apply_processing(&fft_db);

        self.waveform_data = processed.clone();
        self.waterfall_data.rotate_right(1);
        self.waterfall_data[0] = processed;
    }
}
