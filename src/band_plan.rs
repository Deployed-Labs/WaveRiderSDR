use serde::Serialize;

#[derive(Debug, Clone, Serialize)]
pub struct BandInfo {
    pub name: &'static str,
    pub start_hz: f64,
    pub end_hz: f64,
    pub center_hz: f64,
    pub mode: &'static str,
    pub description: &'static str,
}

pub const BANDS: &[BandInfo] = &[
    BandInfo {
        name: "FM Broadcast",
        start_hz: 88_000_000.0,
        end_hz: 108_000_000.0,
        center_hz: 98_000_000.0,
        mode: "FM",
        description: "Broadcast FM radio",
    },
    BandInfo {
        name: "Airband",
        start_hz: 118_000_000.0,
        end_hz: 137_000_000.0,
        center_hz: 127_500_000.0,
        mode: "AM",
        description: "Aircraft voice communications",
    },
    BandInfo {
        name: "2m Amateur",
        start_hz: 144_000_000.0,
        end_hz: 148_000_000.0,
        center_hz: 146_000_000.0,
        mode: "FM",
        description: "2 meter amateur radio",
    },
    BandInfo {
        name: "70cm Amateur",
        start_hz: 420_000_000.0,
        end_hz: 450_000_000.0,
        center_hz: 435_000_000.0,
        mode: "FM",
        description: "70 centimeter amateur radio",
    },
    BandInfo {
        name: "NOAA Weather",
        start_hz: 162_400_000.0,
        end_hz: 162_550_000.0,
        center_hz: 162_475_000.0,
        mode: "FM",
        description: "NOAA weather radio",
    },
    BandInfo {
        name: "20m Amateur",
        start_hz: 14_000_000.0,
        end_hz: 14_350_000.0,
        center_hz: 14_175_000.0,
        mode: "USB",
        description: "20 meter amateur HF band",
    },
];

pub fn get_band(name: &str) -> Option<&'static BandInfo> {
    BANDS.iter().find(|b| b.name.eq_ignore_ascii_case(name))
}
