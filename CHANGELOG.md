# Changelog

All notable changes to WaveRider SDR will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Automated installation scripts for Linux, macOS, and Windows
- PowerShell installer with enhanced features for Windows
- PyInstaller build script for creating standalone executables
- setup.py for proper Python package distribution
- Comprehensive documentation with FAQ and troubleshooting sections
- Contributing guidelines (CONTRIBUTING.md)
- Desktop launcher scripts for all platforms
- Firewall configuration in installation scripts
- Pre-built executable support structure

### Changed
- Completely rewritten README with professional formatting
- Enhanced Quick Start section with multiple installation methods
- Improved security documentation with detailed firewall rules
- Restructured documentation for better navigation

### Improved
- Installation process now one-command on all platforms
- Better platform detection and dependency handling
- More detailed usage instructions with examples
- Enhanced troubleshooting section

## [1.0.0] - Initial Release

### Added
- Real SDR hardware support for RTL-SDR devices
- HackRF device support via SoapySDR
- Automatic SDR device detection
- Desktop GUI application (PyQt5)
- Web-based interface (Flask + Socket.IO)
- Universal launcher with automatic platform detection
- Real-time waterfall display (spectrogram)
- Interactive frequency and sample rate controls
- Multiple demodulation modes (AM, FM, USB, LSB, CW)
- Morse code decoder for CW signals
- Meshtastic device detection
- LoRa communication support
- Simulated signal generator for testing without hardware
- Graceful fallback when no SDR hardware is present
- Mobile-optimized web interface
- Cross-platform compatibility (Windows, macOS, Linux, iOS, Android)
- Start/Stop controls for signal acquisition
- FFT-based frequency analysis with windowing
- Colormap-based visualization
- Touch-friendly controls for mobile devices
- Shared codebase with modular architecture

### Documentation
- README.md with comprehensive instructions
- PLATFORM_GUIDE.md with platform-specific details
- IMPLEMENTATION_SUMMARY.md with technical details
- OPTIMIZATION_SUMMARY.md with performance information
- BRANCH_MERGE_STATUS.md tracking development branches
- MIT License

### Core Components
- `run.py` - Universal launcher
- `waverider_sdr.py` - Desktop application
- `waverider_web.py` - Web interface
- `waverider_common.py` - Shared utilities and classes
- `templates/index.html` - Web UI template
- `requirements.txt` - Python dependencies

### Classes and Utilities
- `SDRDevice` - RTL-SDR and HackRF hardware interface
- `SignalGenerator` - Simulated RF signal generation
- `Demodulator` - AM/FM/SSB/CW demodulation
- `MorseDecoder` - Morse code decoding
- `MeshtasticDetector` - Meshtastic device detection
- `LoRaCommunication` - LoRa management
- `compute_fft_db()` - Optimized FFT computation

## Release Notes Format

### Categories
- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
- **Improved**: Performance or UX improvements

### Version Numbering
- **Major** (X.0.0): Breaking changes, major new features
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, small improvements

---

**Legend:**
- 🆕 New feature
- 🐛 Bug fix
- ⚡ Performance improvement
- 🔒 Security improvement
- 📖 Documentation
- 🎨 UI/UX improvement
- 🔧 Configuration change
- ⚠️ Breaking change
