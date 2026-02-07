# WaveRiderSDR
The only SDR with full features, rolling updates, and **universal cross-platform compatibility**.

## 🎯 Features

- **Real SDR Hardware Support**: Connect to RTL-SDR and other SDR devices for real-time signal acquisition
- **Automatic Device Detection**: Scans and displays available SDR devices
- **Device Selection**: Choose which SDR device to use from detected devices
- **Start/Stop Controls**: Start and stop signal acquisition with a single button
- **Real-Time Display**: Live waterfall and waveform visualization from SDR hardware
- **Graceful Fallback**: Works with simulated signals when no SDR hardware is present
- **Universal Cross-Platform**: Works on Windows, macOS, Linux, iOS, Android, and any device with a web browser
- **Automatic Platform Detection**: Intelligently chooses the best interface for your device
- **Responsive Design**: Adapts to any screen size - from phones to desktop monitors
- **Optimized Codebase**: Refactored with shared modules for better maintainability and performance
- **Waterfall Display (Spectrogram)**: Real-time visualization of frequency spectrum over time
- **Interactive Controls**: Adjust center frequency, sample rate, FFT size, and update rate
- **Signal Processing**: Optimized FFT-based frequency analysis with windowing
- **Flexible Display**: Colormap-based visualization for easy signal identification
- **Mobile-Optimized**: Touch-friendly controls and optimized layouts for phones and tablets
- **Meshtastic Device Detection**: Automatic detection of Meshtastic devices via USB
- **LoRa Communication**: Enables LoRa communication when Meshtastic device is detected

## 🚀 Quick Start

### One Command - Any Platform

```bash
# Install dependencies
pip install -r requirements.txt

# Run (automatically detects your platform)
python run.py
```

That's it! WaveRider SDR will:
- ✅ Detect if you're on desktop or need web version
- ✅ Check for required dependencies  
- ✅ Launch the appropriate interface
- ✅ Work on Windows, macOS, Linux, iOS, and Android
- ✅ Automatically detect connected SDR devices
- ✅ Fall back to simulated signals if no SDR hardware present

### Using with Real SDR Hardware

To use real SDR devices (like RTL-SDR):

```bash
# Install SDR hardware support
pip install pyrtlsdr

# Run the application
python run.py

# The application will:
# 1. Automatically scan for connected SDR devices
# 2. Display detected devices in the UI
# 3. Allow you to select which device to use
# 4. Click "Start" to begin real-time signal acquisition
```

**For mobile devices**: Start the web version on your computer, then access from your phone's browser at `http://<your-ip>:5000`

📖 **Detailed platform-specific instructions**: See [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)

## 🌍 Cross-Platform Support

WaveRider SDR works on **every type of computer and phone**:

### Desktop Platforms
- ✅ **Windows** (7, 8, 10, 11)
- ✅ **macOS** (10.14+)
- ✅ **Linux** (Ubuntu, Debian, Fedora, Arch, etc.)

### Mobile Platforms
- ✅ **iOS** (iPhone, iPad via web browser)
- ✅ **Android** (phones and tablets via web browser)

### How It Works
WaveRider SDR provides **two versions**:
1. **Desktop Application** - Native PyQt5 GUI for desktop computers
2. **Web Interface** - Browser-based interface for phones, tablets, and any device

The universal launcher (`run.py`) automatically detects your platform and starts the appropriate version!

## 📡 SDR Hardware Support

WaveRider SDR supports real SDR hardware for live signal acquisition:

### Supported Devices
- **RTL-SDR** (RTL2832U-based dongles)
- More devices coming soon (HackRF, Airspy, etc.)

### Features
- **Automatic Device Detection**: Scans for connected SDR devices on startup
- **Device Selection**: Choose which SDR to use if multiple devices are connected
- **Real-Time Acquisition**: Live signal processing and display
- **Start/Stop Control**: Start and stop signal acquisition as needed
- **Graceful Fallback**: Automatically uses simulated signals if no hardware is detected

### Setup
1. Install SDR driver for your device (e.g., RTL-SDR driver)
2. Install Python SDR library: `pip install pyrtlsdr`
3. Connect your SDR device
4. Run WaveRider SDR - it will automatically detect your device
5. Select your device from the dropdown menu
6. Click "Start" to begin signal acquisition

## Installation

### Requirements

- Python 3.7 or higher
- pip package manager
- Internet connection (for initial dependency installation)

### Quick Start (Recommended)

The easiest way to run WaveRider SDR on **any platform**:

```bash
# Install core dependencies
pip install -r requirements.txt

# Run the universal launcher (auto-detects your platform)
python run.py
```

The launcher will:
1. Detect your operating system and capabilities
2. Check for required dependencies
3. Offer to install any missing dependencies
4. Launch the appropriate version for your device

### Manual Installation

If you prefer to manually choose which version to install:

#### For Desktop (Windows, macOS, Linux with GUI):

```bash
# Install desktop dependencies
pip install numpy matplotlib scipy PyQt5 pyserial

# Run desktop version
python waverider_sdr.py
```

#### For Web/Mobile (Any device with a browser):

```bash
# Install web dependencies  
pip install numpy matplotlib scipy flask flask-socketio pyserial

# Run web version
python waverider_web.py
```

Then open your web browser and navigate to:
- On the same device: `http://localhost:5000`
- From other devices (phones, tablets): `http://<your-ip-address>:5000`

### Finding Your IP Address

**Windows**: `ipconfig` in Command Prompt  
**macOS/Linux**: `ifconfig` or `ip addr` in Terminal  
**Look for**: IPv4 address (usually starts with 192.168.x.x or 10.x.x.x)

## Usage

### Running with Universal Launcher (Recommended)

```bash
python run.py
```

The launcher supports optional flags:
- `python run.py --web` or `python run.py -w` - Force web version
- `python run.py --desktop` or `python run.py -d` - Force desktop version
- `python run.py --help` or `python run.py -h` - Show help

### Running Specific Versions

#### Desktop Application:

```bash
python waverider_sdr.py
```

#### Web Interface:

```bash
python waverider_web.py
```

### Accessing on Mobile Devices

1. Start the web version on your computer:
   ```bash
   python waverider_web.py
   ```

2. Find your computer's IP address (e.g., 192.168.1.100)

3. On your phone/tablet browser, navigate to:
   ```
   http://192.168.1.100:5000
   ```

4. Bookmark the page for easy access!

### Controls

The application provides the following controls:

- **Center Frequency**: Adjust the center frequency of the display (in MHz)
- **Sample Rate**: Select the sample rate (2.4 MHz, 2.048 MHz, or 1.024 MHz)
- **FFT Size**: Choose the FFT size for frequency resolution (512, 1024, 2048, 4096)
- **Update Rate**: Set the display refresh rate in milliseconds
- **Start/Stop**: Toggle signal acquisition on and off

### Meshtastic Device Status

The application displays real-time status information about Meshtastic devices:

- **Meshtastic Device**: Shows whether a Meshtastic device is detected and connected
- **LoRa Status**: Indicates if LoRa communication is enabled
  - When a Meshtastic device is detected, LoRa communication is automatically enabled at 915 MHz
  - Supported devices include RAK4631, T-Echo, Heltec Tracker, T-Beam, T-Lora, and more

### Waterfall Display

The waterfall display shows:
- **X-axis**: Frequency (in MHz)
- **Y-axis**: Time (newest data at the top)
- **Color**: Signal power in dB (darker = weaker, brighter = stronger)

The color scale ranges from -80 dB (dark) to 0 dB (bright), using the viridis colormap.

## Features in Detail

### Real-time Signal Visualization

The waterfall display updates in real-time, showing how the frequency spectrum changes over time. This is essential for:
- Identifying signal patterns
- Monitoring frequency activity
- Detecting intermittent signals
- Analyzing signal characteristics

### Signal Processing

The application performs the following signal processing:
1. Captures IQ samples from the signal source
2. Applies Hamming window to reduce spectral leakage
3. Computes FFT to convert to frequency domain
4. Converts magnitude to dB scale
5. Updates waterfall display with new data

### Demonstration Mode

Currently, the application uses a simulated signal generator that creates:
- Multiple carrier signals at different frequencies
- FM-like modulated signals
- Background noise

This allows you to see the waterfall visualization in action without requiring actual SDR hardware.

## Platform Compatibility Matrix

| Platform | Desktop Version | Web Version | Notes |
|----------|----------------|-------------|-------|
| **Windows 7+** | ✅ Full Support | ✅ Full Support | Both Qt and web versions work |
| **macOS 10.14+** | ✅ Full Support | ✅ Full Support | Both Qt and web versions work |
| **Linux (Ubuntu, Debian, etc.)** | ✅ Full Support | ✅ Full Support | Both versions supported |
| **Linux (Server/Headless)** | ❌ No Display | ✅ Full Support | Web version recommended |
| **iOS (iPhone/iPad)** | ❌ No Qt Support | ✅ Full Support | Use web version via Safari/Chrome |
| **Android (Phones/Tablets)** | ❌ No Qt Support | ✅ Full Support | Use web version via any browser |
| **Raspberry Pi** | ⚠️ Limited | ✅ Full Support | Web version recommended |
| **Chromebook** | ❌ No Qt Support | ✅ Full Support | Web version only |

### Browser Compatibility (Web Version)

The web interface works with modern browsers on any device:
- ✅ Chrome/Chromium (Desktop & Mobile)
- ✅ Firefox (Desktop & Mobile)  
- ✅ Safari (macOS & iOS)
- ✅ Edge (Windows)
- ✅ Samsung Internet (Android)
- ✅ Opera (All platforms)

**Minimum Requirements:**
- HTML5 support
- WebSocket support
- JavaScript enabled

### Network Configuration for Mobile Access

To access WaveRider SDR from mobile devices:

1. **Same WiFi Network**: Ensure both the computer running the server and your mobile device are on the same WiFi network

2. **Firewall Configuration**: Allow port 5000 through your firewall (restrict to local network for security)
   
   **Windows** (restrict to local network):
   ```powershell
   netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000 remoteip=localsubnet
   ```
   
   **macOS**: System Preferences → Security & Privacy → Firewall → Firewall Options → Add Python application
   
   **Linux** (UFW - restrict to local network):
   ```bash
   sudo ufw allow from 192.168.0.0/16 to any port 5000 proto tcp
   sudo ufw allow from 10.0.0.0/8 to any port 5000 proto tcp
   ```

3. **Router**: Keep the service on your local network only. Do not expose port 5000 to the internet without proper authentication and HTTPS.

### 🔒 Security Best Practices

- **Local Network Only**: By default, the web server binds to all interfaces (0.0.0.0) to allow mobile access. This is safe on trusted local networks.
- **Firewall Rules**: Use the firewall rules above that restrict access to local network ranges (192.168.x.x, 10.x.x.x)
- **No Public Exposure**: Do not forward port 5000 through your router unless you add authentication and HTTPS
- **Trusted Networks**: Only run on trusted WiFi networks, not public WiFi
- **Local-Only Mode**: For localhost-only access (no mobile), edit `waverider_web.py` to use `host='127.0.0.1'`

## 📁 Project Structure

WaveRider SDR is built with a modular architecture for maintainability and code reuse:

```
WaveRiderSDR/
├── run.py                    # Universal launcher (auto-detects platform)
├── waverider_sdr.py          # Desktop GUI application (PyQt5)
├── waverider_web.py          # Web interface (Flask + SocketIO)
├── waverider_common.py       # Shared utilities and classes
│   ├── MeshtasticDetector    # USB device detection
│   ├── LoRaCommunication     # LoRa communication management
│   ├── SignalGenerator       # Simulated RF signal generation
│   └── compute_fft_db()      # Optimized FFT computation
├── templates/
│   └── index.html            # Web interface template
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── PLATFORM_GUIDE.md         # Detailed platform instructions
└── IMPLEMENTATION_SUMMARY.md # Technical implementation details
```

### Key Optimizations

- **Shared Code Module**: Common classes moved to `waverider_common.py` to eliminate duplication
- **Optimized FFT Processing**: Centralized FFT computation with Hamming windowing
- **Efficient Signal Generation**: Reusable signal generator for both interfaces
- **Graceful Dependency Handling**: Optional imports with informative error messages

## Future Enhancements

- Support for real SDR hardware (RTL-SDR, HackRF, etc.)
- Recording and playback functionality
- Signal demodulation
- Frequency bookmarks
- Adjustable colormap and dynamic range
- Advanced LoRa packet capture and analysis
- Meshtastic message monitoring and transmission

## License

See LICENSE file for details. 
