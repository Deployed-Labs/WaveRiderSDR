use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct MorseDecoder {
    pub sample_rate: f32,
    pub wpm: f32,
    pub threshold: f32,
    pub decoded_text: String,
    current_symbol: String,
    last_state: bool,
    state_duration_s: f32,
    map: HashMap<&'static str, &'static str>,
}

impl MorseDecoder {
    pub fn new(sample_rate: f32, wpm: f32) -> Self {
        let mut map = HashMap::new();
        map.insert(".-", "A");
        map.insert("-...", "B");
        map.insert("-.-.", "C");
        map.insert("-..", "D");
        map.insert(".", "E");
        map.insert("..-.", "F");
        map.insert("--.", "G");
        map.insert("....", "H");
        map.insert("..", "I");
        map.insert(".---", "J");
        map.insert("-.-", "K");
        map.insert(".-..", "L");
        map.insert("--", "M");
        map.insert("-.", "N");
        map.insert("---", "O");
        map.insert(".--.", "P");
        map.insert("--.-", "Q");
        map.insert(".-.", "R");
        map.insert("...", "S");
        map.insert("-", "T");
        map.insert("..-", "U");
        map.insert("...-", "V");
        map.insert(".--", "W");
        map.insert("-..-", "X");
        map.insert("-.--", "Y");
        map.insert("--..", "Z");
        map.insert(".----", "1");
        map.insert("..---", "2");
        map.insert("...--", "3");
        map.insert("....-", "4");
        map.insert(".....", "5");
        map.insert("-....", "6");
        map.insert("--...", "7");
        map.insert("---..", "8");
        map.insert("----.", "9");
        map.insert("-----", "0");

        Self {
            sample_rate,
            wpm,
            threshold: 0.3,
            decoded_text: String::new(),
            current_symbol: String::new(),
            last_state: false,
            state_duration_s: 0.0,
            map,
        }
    }

    pub fn reset(&mut self) {
        self.decoded_text.clear();
        self.current_symbol.clear();
        self.last_state = false;
        self.state_duration_s = 0.0;
    }

    pub fn process_samples(&mut self, envelope: &[f32]) -> Option<String> {
        if envelope.is_empty() {
            return None;
        }

        let avg = envelope.iter().sum::<f32>() / envelope.len() as f32;
        let current_state = avg > self.threshold;
        let duration_s = envelope.len() as f32 / self.sample_rate;

        let dot = 1.2 / self.wpm.max(1.0);
        let dash = 3.0 * dot;
        let char_gap = 3.0 * dot;
        let word_gap = 7.0 * dot;

        let mut new_text = String::new();

        if current_state != self.last_state {
            if self.last_state {
                if self.state_duration_s >= dash * 0.7 {
                    self.current_symbol.push('-');
                } else if self.state_duration_s >= dot * 0.5 {
                    self.current_symbol.push('.');
                }
            } else if self.state_duration_s >= word_gap * 0.7 {
                if !self.current_symbol.is_empty() {
                    let ch = self.map.get(self.current_symbol.as_str()).copied().unwrap_or("?");
                    new_text.push_str(ch);
                    new_text.push(' ');
                    self.current_symbol.clear();
                }
            } else if self.state_duration_s >= char_gap * 0.7 && !self.current_symbol.is_empty() {
                let ch = self.map.get(self.current_symbol.as_str()).copied().unwrap_or("?");
                new_text.push_str(ch);
                self.current_symbol.clear();
            }

            self.state_duration_s = 0.0;
        }

        self.state_duration_s += duration_s;
        self.last_state = current_state;

        if new_text.is_empty() {
            None
        } else {
            self.decoded_text.push_str(&new_text);
            Some(new_text)
        }
    }
}
