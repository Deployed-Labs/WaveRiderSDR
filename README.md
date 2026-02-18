<div align="center">

# 🌊 WaveRider SDR 🌊

### Universal Cross-Platform Software Defined Radio

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/Deployed-Labs/WaveRiderSDR)
[![Build and Release](https://github.com/Deployed-Labs/WaveRiderSDR/actions/workflows/release.yml/badge.svg)](https://github.com/Deployed-Labs/WaveRiderSDR/actions/workflows/release.yml)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/Deployed-Labs/WaveRiderSDR/pulls)

**The only SDR with full features, rolling updates, and universal cross-platform compatibility.**

[Quick Start](#-quick-start) • [Features](#-features) • [Installation](#-installation) • [Documentation](#-documentation) • [Support](#-support)

</div>

---

## ✨ What Makes WaveRider Special

WaveRider SDR is designed to be **the easiest and most fun SDR software** to use, with installation simplified to just one command and executables available for all platforms.

### 🎯 Core Features

<table>
<tr>
<td width="50%">

#### 📡 Hardware Support
- ✅ **RTL-SDR** (RTL2832U dongles)
- ✅ **HackRF One** (via SoapySDR)
- ✅ **Automatic device detection**
- ✅ **Multi-device support**
- ✅ **Graceful simulation fallback**

#### 🎚️ Signal Processing
- ✅ **AM/FM demodulation**
- ✅ **SSB (USB/LSB) support**
- ✅ **CW (Morse code) decoder**
- ✅ **Real-time FFT analysis**
- ✅ **Waterfall visualization**

</td>
<td width="50%">

#### 💻 Cross-Platform
- ✅ **Windows** (7, 8, 10, 11)
- ✅ **macOS** (10.14+)
- ✅ **Linux** (All major distros)
- ✅ **iOS/Android** (Web interface)
- ✅ **Automatic platform detection**

#### 🎨 User Interface
- ✅ **Desktop GUI** (PyQt5)
- ✅ **Web interface** (Flask)
- ✅ **Mobile-optimized** design
- ✅ **Touch-friendly** controls
- ✅ **Responsive** layouts

</td>
</tr>
</table>

### 🆕 Advanced Features

- **Multiple Modulation Modes**: Support for AM, FM, USB, LSB, and CW (Morse code) demodulation
- **Morse Code Decoder**: Real-time Morse code (CW) detection and text display with International Morse Code support
- **Meshtastic Integration**: Automatic detection of Meshtastic devices via USB with LoRa communication
- **Interactive Controls**: Adjust center frequency, sample rate, FFT size, and update rate in real-time
- **Start/Stop Controls**: Simple one-button control for signal acquisition

## 🚀 Quick Start

### One-Command Installation

Choose your platform and run the appropriate installation script:

#### 🐧 Linux / 🍎 macOS
```bash
curl -fsSL https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.sh | bash
```
or download and run:
```bash
chmod +x install.sh
./install.sh
```

#### 🪟 Windows

**PowerShell (Recommended):**
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Command Prompt:**
```cmd
install.bat
```

### Manual Installation

If you prefer to install manually:

```bash
# 1. Clone the repository
git clone https://github.com/Deployed-Labs/WaveRiderSDR.git
cd WaveRiderSDR

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run WaveRider SDR
python run.py
```

### Using Pre-Built Executables

Download the latest release for your platform:

1. Go to [Releases](https://github.com/Deployed-Labs/WaveRiderSDR/releases)
2. Download the appropriate file:
   - **Windows**: `WaveRiderSDR-Windows.zip`
   - **macOS**: `WaveRiderSDR-macOS.zip`
   - **Linux**: `WaveRiderSDR-Linux.tar.gz`
3. Extract and run:
   - **Windows**: Double-click `WaveRiderSDR.exe`
   - **macOS**: Open `WaveRiderSDR.app` or run `./WaveRiderSDR`
   - **Linux**: Run `./WaveRiderSDR`

That's it! WaveRider SDR will:
- ✅ Automatically detect if you're on desktop or need web version
- ✅ Check for required dependencies
- ✅ Launch the appropriate interface
- ✅ Work on Windows, macOS, Linux, iOS, and Android
- ✅ Automatically detect connected SDR devices
- ✅ Fall back to simulated signals if no SDR hardware present

## 📋 Installation Methods Comparison

| Method | Pros | Best For |
|--------|------|----------|
| **Installation Scripts** | Automatic setup, creates shortcuts, configures firewall | First-time users, recommended |
| **Pre-built Executables** | No Python required, instant use, portable | Users without Python, quick testing |
| **Manual Installation** | Full control, easy updates via git | Developers, contributors |
| **pip install** | Standard Python package installation | Python developers |

---

## 🛠️ Installation

### Detailed Installation Instructions

#### Option 1: Automated Installation (Recommended) ⭐

The automated installers handle everything for you:

<details>
<summary><b>🐧 Linux Installation</b></summary>

```bash
# Download and run installer
wget https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.sh
chmod +x install.sh
./install.sh

# Or one-liner:
curl -fsSL https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.sh | bash
```

**What it does:**
- ✅ Checks Python 3 installation
- ✅ Installs all required dependencies
- ✅ Offers optional SDR hardware support
- ✅ Creates launcher scripts
- ✅ Creates desktop shortcuts (optional)
- ✅ Tests the installation

**Supported Distributions:**
- Ubuntu / Debian / Linux Mint
- Fedora / CentOS / RHEL
- Arch Linux / Manjaro
- openSUSE
- Any Linux with Python 3.7+

</details>

<details>
<summary><b>🍎 macOS Installation</b></summary>

```bash
# Download and run installer
curl -O https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.sh
chmod +x install.sh
./install.sh

# Or one-liner:
curl -fsSL https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.sh | bash
```

**What it does:**
- ✅ Checks Python 3 installation
- ✅ Installs all required dependencies
- ✅ Offers optional SDR hardware support
- ✅ Creates launcher scripts
- ✅ Tests the installation

**Requirements:**
- macOS 10.14 (Mojave) or later
- Python 3.8+ (Install via [python.org](https://www.python.org/downloads/) or `brew install python3`)

</details>

<details>
<summary><b>🪟 Windows Installation</b></summary>

**Method 1: PowerShell (Recommended)**
```powershell
# Download installer
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.ps1" -OutFile "install.ps1"

# Run installer
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Method 2: Batch File**
```cmd
# Download installer
curl -O https://raw.githubusercontent.com/Deployed-Labs/WaveRiderSDR/main/install.bat

# Run installer
install.bat
```

**What it does:**
- ✅ Checks Python 3 installation
- ✅ Upgrades pip to latest version
- ✅ Installs all required dependencies
- ✅ Offers optional SDR hardware support
- ✅ Creates launcher batch files
- ✅ Creates desktop shortcuts (optional)
- ✅ Configures Windows Firewall for mobile access (optional, requires admin)
- ✅ Tests the installation

**Requirements:**
- Windows 7 or later (Windows 10/11 recommended)
- Python 3.8+ (Install from [python.org](https://www.python.org/downloads/) - check "Add Python to PATH"!)

</details>

#### Option 2: Pre-Built Executables (No Python Required) 🎁

Download ready-to-use executables from the [Releases page](https://github.com/Deployed-Labs/WaveRiderSDR/releases):

| Platform | File | Instructions |
|----------|------|--------------|
| **Windows** | `WaveRiderSDR-Windows.zip` | Extract and double-click `WaveRiderSDR.exe` |
| **macOS** | `WaveRiderSDR-macOS.zip` | Extract and open `WaveRiderSDR.app` |
| **Linux** | `WaveRiderSDR-Linux.tar.gz` | Extract and run `./WaveRiderSDR` |

**Advantages:**
- No Python installation required
- Portable - run from USB drive
- Instant startup
- Self-contained

#### Option 3: Manual Installation (For Developers) 🔧

```bash
# 1. Clone the repository
git clone https://github.com/Deployed-Labs/WaveRiderSDR.git
cd WaveRiderSDR

# 2. Install core dependencies
pip install -r requirements.txt

# 3. (Optional) Install SDR hardware support
pip install pyrtlsdr

# 4. Run WaveRider SDR
python run.py
```

**For developers:**
```bash
# Install in development mode with all extras
pip install -e ".[all]"

# Or install specific feature sets:
pip install -e ".[desktop]"  # Desktop GUI only
pip install -e ".[web]"      # Web interface only
pip install -e ".[sdr]"      # SDR hardware support only
```

#### Option 4: Python Package Installation 📦

Install WaveRider SDR as a Python package (coming soon to PyPI):

```bash
# Install from PyPI (when available)
pip install waverider-sdr

# Install with all features
pip install waverider-sdr[all]

# Run from command line
waverider
```

---

## 🎮 Usage

### Basic Usage

#### Running WaveRider SDR

The universal launcher automatically detects your platform:

```bash
python run.py
```

**Command-line options:**
```bash
python run.py           # Auto-detect best interface
python run.py --web     # Force web interface
python run.py --desktop # Force desktop GUI
python run.py --help    # Show help message
```

**Using launcher scripts (after installation):**
```bash
# Linux/macOS
./waverider              # Auto-detect
./waverider-web.sh       # Web version
./waverider-desktop.sh   # Desktop version

# Windows
waverider.bat            # Auto-detect
waverider-web.bat        # Web version
waverider-desktop.bat    # Desktop version
```

#### First Run

1. **Launch the application** using any method above
2. **Select interface** (or let it auto-detect):
   - Desktop GUI launches automatically on Windows/macOS/Linux with display
   - Web interface launches on headless systems or mobile devices
3. **Connect SDR hardware** (optional):
   - Plug in your RTL-SDR or HackRF device
   - Application auto-detects devices
   - Select device from dropdown if multiple devices
4. **Click "Start"** to begin signal acquisition
5. **Adjust settings** as needed (frequency, sample rate, etc.)

### Using with SDR Hardware

<details>
<summary><b>📡 RTL-SDR Setup</b></summary>

**Step 1: Install RTL-SDR Software**

```bash
pip install pyrtlsdr
```

**Step 2: Install RTL-SDR Drivers**

- **Windows**: Use [Zadig](https://zadig.akeo.ie/) to install WinUSB driver
- **Linux**: Install `rtl-sdr` package
  ```bash
  # Ubuntu/Debian
  sudo apt-get install rtl-sdr librtlsdr-dev
  
  # Fedora
  sudo dnf install rtl-sdr
  ```
- **macOS**: Install via Homebrew
  ```bash
  brew install librtlsdr
  ```

**Step 3: Connect and Use**

1. Plug in your RTL-SDR device
2. Run WaveRider SDR
3. Device appears in dropdown automatically
4. Select device and click "Start"

**Supported RTL-SDR Devices:**
- RTL2832U-based USB dongles
- NooElec NESDR series
- RTL-SDR Blog V3/V4
- FlightAware ADS-B dongles
- Most generic DVB-T dongles with RTL2832U chip

</details>

<details>
<summary><b>📡 HackRF Setup</b></summary>

**Step 1: Install SoapySDR**

- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install python3-soapysdr soapysdr-module-hackrf
  ```

- **Fedora:**
  ```bash
  sudo dnf install python3-SoapySDR SoapySDR-module-hackrf
  ```

- **macOS:**
  ```bash
  brew install soapysdr hackrf
  ```

- **Windows:**
  1. Download SoapySDR from [GitHub](https://github.com/pothosware/SoapySDR/wiki)
  2. Download HackRF drivers from [GitHub](https://github.com/greatscottgadgets/hackrf)
  3. Install both packages

**Step 2: Connect and Use**

1. Plug in your HackRF device
2. Run WaveRider SDR
3. HackRF appears in dropdown automatically
4. Select device and click "Start"

**Supported HackRF Devices:**
- HackRF One
- HackRF-compatible devices

</details>

### Interface Controls

Both desktop and web interfaces provide the same controls:

| Control | Description | Range/Options |
|---------|-------------|---------------|
| **Center Frequency** | Tuning frequency | Device-dependent (typically 24 MHz - 1.7 GHz for RTL-SDR) |
| **Sample Rate** | ADC sample rate | 2.4 MHz, 2.048 MHz, 1.024 MHz |
| **FFT Size** | Frequency resolution | 512, 1024, 2048, 4096 bins |
| **Update Rate** | Display refresh | 50-1000 ms |
| **Modulation** | Demodulation mode | None, AM, FM, USB, LSB, CW |
| **Device Selection** | Choose SDR device | Auto-detected devices |
| **Start/Stop** | Control signal acquisition | Button toggle |
| **Morse Decoder** | Enable/disable CW decoding | Button toggle (CW mode only) |

### Demodulation Modes

WaveRider SDR supports multiple demodulation modes:

| Mode | Type | Best For | Typical Use Cases |
|------|------|----------|-------------------|
| **None** | Raw IQ | Spectrum analysis | General scanning, signal detection |
| **AM** | Amplitude Modulation | 530 kHz - 1.7 MHz | AM broadcast radio, aviation (108-137 MHz) |
| **FM** | Frequency Modulation | VHF/UHF | FM broadcast (88-108 MHz), NOAA weather, 2m ham |
| **USB** | Upper Sideband | HF bands | SSB ham radio, shortwave voice comms |
| **LSB** | Lower Sideband | HF bands | SSB ham radio, marine radio |
| **CW** | Continuous Wave | All bands | Morse code transmissions, ham radio CW |

**To use demodulation:**
1. Select modulation mode from dropdown
2. Signal is automatically demodulated
3. For CW mode, enable Morse decoder to see decoded text

### Morse Code Decoder

The integrated Morse code decoder translates CW transmissions in real-time:

**How to use:**
1. Select **"CW (Morse)"** from Modulation dropdown
2. Click **"Enable Morse Decoder"** button
3. Tune to a frequency with Morse code
4. Decoded text appears in real-time
5. Supports standard International Morse Code

**Supported characters:**
- Letters: A-Z
- Numbers: 0-9
- Punctuation: . , ? ' ! / ( ) & : ; = + - _ " $ @
- Prosigns: SK, AR, BT, etc.

### Mobile Access

Access WaveRider SDR from phones and tablets:

**Step 1: Start Web Server**
```bash
python run.py --web
# Or use: python waverider_web.py
```

**Step 2: Find Your IP Address**
- **Windows**: Run `ipconfig` in Command Prompt
- **macOS**: Run `ifconfig` in Terminal
- **Linux**: Run `ip addr` or `ifconfig`
- Look for IPv4 address (usually 192.168.x.x or 10.x.x.x)

**Step 3: Connect from Mobile**
1. Ensure mobile device is on **same WiFi network**
2. Open browser on phone/tablet
3. Navigate to: `http://<your-ip>:5000`
   - Example: `http://192.168.1.100:5000`
4. Bookmark for easy access!

**Supported Mobile Browsers:**
- iOS: Safari, Chrome
- Android: Chrome, Firefox, Samsung Internet, Edge

---

## 🌍 Platform Support

### Desktop Platforms

| Platform | Desktop GUI | Web Interface | Notes |
|----------|-------------|---------------|-------|
| **Windows 7** | ✅ | ✅ | Fully supported |
| **Windows 8/8.1** | ✅ | ✅ | Fully supported |
| **Windows 10** | ✅ | ✅ | Recommended |
| **Windows 11** | ✅ | ✅ | Recommended |
| **macOS 10.14+** | ✅ | ✅ | Mojave or later |
| **Ubuntu/Debian** | ✅ | ✅ | All recent versions |
| **Fedora/RHEL** | ✅ | ✅ | All recent versions |
| **Arch Linux** | ✅ | ✅ | Rolling release |
| **Raspberry Pi** | ⚠️ | ✅ | Web recommended |
| **Linux Server** | ❌ | ✅ | Headless only |

### Mobile Platforms

| Platform | Support | Method | Notes |
|----------|---------|--------|-------|
| **iOS (iPhone)** | ✅ | Web Browser | Safari, Chrome |
| **iOS (iPad)** | ✅ | Web Browser | Safari, Chrome |
| **Android Phone** | ✅ | Web Browser | Any modern browser |
| **Android Tablet** | ✅ | Web Browser | Any modern browser |

### Browser Compatibility

**Desktop Browsers:**
- ✅ Chrome/Chromium 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+
- ✅ Opera 76+

**Mobile Browsers:**
- ✅ Safari (iOS 14+)
- ✅ Chrome (iOS/Android)
- ✅ Firefox (Android)
- ✅ Samsung Internet
- ✅ Edge Mobile

**Requirements:**
- HTML5 support
- WebSocket support
- JavaScript enabled
- Canvas API support

---

## 🔒 Security Best Practices

WaveRider SDR takes security seriously:

### Built-in Security Features

- ✅ **Random secret keys** - Not hardcoded
- ✅ **SRI integrity** - CDN scripts verified
- ✅ **Local network binding** - Safe defaults
- ✅ **No telemetry** - Your data stays local
- ✅ **Open source** - Fully auditable code

### Network Security

**Default Configuration (Safe):**
- Server binds to `0.0.0.0:5000` (all interfaces)
- Allows local network access for mobile devices
- **Safe on trusted networks only**

**Recommended Firewall Rules:**

<details>
<summary><b>Windows Firewall</b></summary>

```powershell
# Restrict to local subnet (safe)
netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000 remoteip=localsubnet profile=private

# For specific IP range
netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000 remoteip=192.168.1.0/24
```

</details>

<details>
<summary><b>Linux Firewall (UFW)</b></summary>

```bash
# Allow from local networks
sudo ufw allow from 192.168.0.0/16 to any port 5000 proto tcp
sudo ufw allow from 10.0.0.0/8 to any port 5000 proto tcp

# Or specific subnet
sudo ufw allow from 192.168.1.0/24 to any port 5000 proto tcp
```

</details>

<details>
<summary><b>macOS Firewall</b></summary>

1. Open **System Preferences** → **Security & Privacy**
2. Click **Firewall** tab
3. Click **Firewall Options**
4. Add Python application
5. Set to "Allow incoming connections"

</details>

### Security Checklist

- ✅ **Use on trusted networks only** (home WiFi, not public WiFi)
- ✅ **Configure firewall** to restrict to local network
- ✅ **Don't expose port 5000 to internet** without authentication
- ✅ **Keep software updated** for security patches
- ❌ **Never run on public WiFi** without VPN
- ❌ **Don't port forward** to internet without HTTPS + auth

### Localhost-Only Mode

For maximum security (no mobile access):

Edit `waverider_web.py` line ~100:
```python
# Change from:
socketio.run(app, host='0.0.0.0', port=5000)

# To:
socketio.run(app, host='127.0.0.1', port=5000)
```

This prevents all network access except from the same computer.

---

## 📖 Documentation

**Complete Documentation:**
- **[README.md](README.md)** - This file (main documentation)
- **[PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)** - Detailed platform-specific instructions
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - Technical implementation details
- **[OPTIMIZATION_SUMMARY.md](OPTIMIZATION_SUMMARY.md)** - Performance optimizations

---

## 📁 Project Structure

```
WaveRiderSDR/
├── 📄 run.py                    # Universal launcher (auto-detects platform)
├── 📄 waverider_sdr.py          # Desktop GUI application (PyQt5)
├── 📄 waverider_web.py          # Web interface (Flask + SocketIO)
├── 📄 waverider_common.py       # Shared utilities and classes
│
├── 🛠️ Installation Scripts
│   ├── install.sh               # Linux/macOS automated installer
│   ├── install.bat              # Windows batch installer
│   └── install.ps1              # Windows PowerShell installer
│
├── 🏗️ Build Files
│   ├── build.py                 # PyInstaller build script
│   ├── setup.py                 # Python package configuration
│   └── requirements.txt         # Python dependencies
│
├── 📁 templates/
│   └── index.html               # Web interface HTML template
│
└── 📚 Documentation
    ├── README.md                # Main documentation (this file)
    ├── PLATFORM_GUIDE.md        # Platform-specific guides
    ├── IMPLEMENTATION_SUMMARY.md # Technical details
    ├── OPTIMIZATION_SUMMARY.md   # Performance info
    └── LICENSE                   # MIT License
```

### Key Components

**`waverider_common.py`** - Shared functionality:
- `SDRDevice` - RTL-SDR and HackRF hardware interface
- `SignalGenerator` - Simulated signal generation
- `Demodulator` - AM/FM/SSB/CW demodulation
- `MorseDecoder` - Morse code decoding
- `MeshtasticDetector` - Meshtastic device detection
- `LoRaCommunication` - LoRa management
- `compute_fft_db()` - Optimized FFT computation

**`waverider_sdr.py`** - Desktop GUI:
- PyQt5-based native interface
- Real-time waterfall display
- Interactive controls
- Windows/macOS/Linux support

**`waverider_web.py`** - Web Interface:
- Flask + SocketIO server
- HTML5 canvas waterfall
- Mobile-optimized responsive design
- Cross-platform browser support

---

## 🔧 Building Executables

Create standalone executables for distribution:

```bash
# Install PyInstaller
pip install pyinstaller

# Build for your platform
python build.py
```

**Output locations:**
- **Windows**: `dist/WaveRiderSDR/WaveRiderSDR.exe`
- **macOS**: `dist/WaveRiderSDR.app` and `dist/WaveRiderSDR/WaveRiderSDR`
- **Linux**: `dist/WaveRiderSDR/WaveRiderSDR`

**Distribution:**

Releases are automatically created via GitHub Actions when a new version tag is pushed:

```bash
# Create and push a new version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

This will trigger the build workflow which:
1. Builds executables for Windows, macOS, and Linux
2. Creates archives for each platform
3. Automatically creates a GitHub release with all artifacts attached

Alternatively, you can manually trigger the workflow from the Actions tab for testing.

For local builds:
1. Test the executable
2. Create archive (zip/tar.gz)
3. Use the automated release workflow as described above

---

## 🐛 Troubleshooting

### Common Issues

<details>
<summary><b>Python not found</b></summary>

**Symptoms:** `python: command not found` or `'python' is not recognized`

**Solutions:**
- **Windows**: Reinstall Python from [python.org](https://www.python.org/downloads/) and check "Add Python to PATH"
- **macOS**: Install Python via `brew install python3` or from python.org
- **Linux**: Install via package manager: `sudo apt install python3 python3-pip`

Try `python3` instead of `python` if standard command doesn't work.

</details>

<details>
<summary><b>Permission denied errors (Linux/macOS)</b></summary>

**Symptoms:** Cannot run install scripts

**Solutions:**
```bash
chmod +x install.sh
./install.sh

# Or for specific scripts:
chmod +x waverider
```

</details>

<details>
<summary><b>ImportError: No module named 'PyQt5'</b></summary>

**Symptoms:** Desktop version won't start

**Solutions:**
```bash
pip install PyQt5

# Or reinstall all dependencies:
pip install -r requirements.txt
```

**Alternative:** Use web version instead:
```bash
python run.py --web
```

</details>

<details>
<summary><b>RTL-SDR device not detected</b></summary>

**Symptoms:** No devices shown in dropdown

**Solutions:**
1. **Install pyrtlsdr:**
   ```bash
   pip install pyrtlsdr
   ```

2. **Install RTL-SDR drivers:**
   - **Windows**: Use [Zadig](https://zadig.akeo.ie/) to install WinUSB driver
   - **Linux**: `sudo apt-get install rtl-sdr`
   - **macOS**: `brew install librtlsdr`

3. **Check device connection:**
   ```bash
   # Linux/macOS
   rtl_test

   # Should show: "Found 1 device(s)"
   ```

4. **Unplug and replug** the device
5. **Restart** WaveRider SDR

</details>

<details>
<summary><b>HackRF device not detected</b></summary>

**Symptoms:** HackRF not shown in device list

**Solutions:**
1. **Install SoapySDR** (see [HackRF Setup](#-hackrf-setup))
2. **Verify installation:**
   ```bash
   SoapySDRUtil --find
   # Should list HackRF device
   ```
3. **Check USB connection**
4. **Update firmware** if needed
5. **Restart** WaveRider SDR

</details>

<details>
<summary><b>Cannot access web interface from mobile</b></summary>

**Symptoms:** Connection refused or timeout from phone/tablet

**Solutions:**
1. **Verify same WiFi network**: Both devices must be on same network
2. **Check IP address**: Use `ipconfig` (Windows) or `ifconfig` (macOS/Linux)
3. **Check firewall**: 
   - Windows: Run `netsh advfirewall firewall show rule name="WaveRider SDR"`
   - Linux: Run `sudo ufw status`
4. **Test locally first**: Try `http://localhost:5000` on the server computer
5. **Try different port**: Edit source to use port 8080 instead of 5000
6. **Disable firewall temporarily** to test (re-enable after!)

</details>

<details>
<summary><b>Web interface is slow or laggy</b></summary>

**Symptoms:** Delayed updates, freezing

**Solutions:**
1. **Reduce update rate**: Increase to 200-500ms
2. **Reduce FFT size**: Use 1024 or 512 instead of 4096
3. **Check CPU usage**: Close other applications
4. **Check network**: Ensure strong WiFi signal
5. **Use desktop version**: Native GUI is more efficient

</details>

<details>
<summary><b>Module 'numpy' has no attribute 'XXX'</b></summary>

**Symptoms:** NumPy-related errors

**Solutions:**
```bash
# Update NumPy
pip install --upgrade numpy

# Or reinstall
pip uninstall numpy
pip install numpy
```

</details>

<details>
<summary><b>PyQt5 ImportError on macOS</b></summary>

**Symptoms:** `ImportError: dlopen(...): Library not loaded`

**Solutions:**
```bash
# Reinstall PyQt5
pip uninstall PyQt5
pip install PyQt5

# Or use Homebrew version:
brew install pyqt5
```

</details>

### Getting Help

**Before asking for help:**
1. ✅ Check this troubleshooting section
2. ✅ Read relevant documentation
3. ✅ Search existing GitHub issues
4. ✅ Try both desktop and web versions

**When reporting issues:**
1. 📋 Include your platform (OS, version)
2. 📋 Python version: `python --version`
3. 📋 Error messages (full traceback)
4. 📋 Steps to reproduce
5. 📋 What you expected vs. what happened

**Where to get help:**
- 🐛 [GitHub Issues](https://github.com/Deployed-Labs/WaveRiderSDR/issues) - Bug reports
- 💬 [Discussions](https://github.com/Deployed-Labs/WaveRiderSDR/discussions) - Questions & ideas
- 📧 Email: Check GitHub profile for contact

---

## 🚀 Future Enhancements

**Planned Features:**
- [ ] Recording and playback functionality
- [ ] Frequency bookmarks and presets
- [ ] Adjustable colormap options
- [ ] Dynamic range control
- [ ] Advanced LoRa packet capture
- [ ] Meshtastic message monitoring
- [ ] Spectrum analyzer mode
- [ ] Signal strength meter (S-meter)
- [ ] Band scanning functionality
- [ ] Noise floor indication
- [ ] Peak hold display
- [ ] Signal identification tools

**Hardware Support:**
- [ ] Additional SDR devices (Airspy, LimeSDR, PlutoSDR)
- [ ] Audio input support (sound card as SDR)
- [ ] IQ file playback
- [ ] Network SDR support (RTSP, SpyServer)

**Want to contribute?** See [Contributing](#-contributing) section below!

---

## 🤝 Contributing

We welcome contributions from the community!

### Ways to Contribute

1. **🐛 Report bugs** - Open an issue with details
2. **💡 Suggest features** - Share your ideas in Discussions
3. **📝 Improve documentation** - Fix typos, add examples
4. **🔧 Submit code** - Fix bugs, add features
5. **🧪 Test** - Try on different platforms, report results
6. **🌍 Translate** - Help translate UI and docs
7. **⭐ Star the repo** - Show your support!

### Development Setup

```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/WaveRiderSDR.git
cd WaveRiderSDR

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install in development mode with all extras
pip install -e ".[all]"

# Create a feature branch
git checkout -b feature/your-feature-name

# Make changes, test, commit
git add .
git commit -m "Add: your feature description"
git push origin feature/your-feature-name

# Open Pull Request on GitHub
```

### Code Style

- **Python**: Follow PEP 8 style guide
- **Comments**: Clear and concise
- **Docstrings**: Use for all functions/classes
- **Type hints**: Encouraged for new code

### Pull Request Guidelines

✅ **Good PRs:**
- Clear description of changes
- One feature/fix per PR
- Tests pass (if applicable)
- Documentation updated
- Clean commit history

❌ **Avoid:**
- Mixing multiple features
- Breaking existing functionality
- Large reformatting changes
- Undocumented changes

---

## 📊 Performance Tips

### Optimizing for Speed

**Reduce CPU Usage:**
1. Increase update rate (200-500ms)
2. Reduce FFT size (512 or 1024)
3. Use lower sample rates
4. Disable features not in use

**Optimize for Raspberry Pi:**
```bash
# Use web interface (lighter than GUI)
python run.py --web

# Reduce settings in UI:
# - Sample Rate: 1.024 MHz
# - FFT Size: 512
# - Update Rate: 500ms
```

**Optimize for Battery (Laptops):**
- Use desktop version (more efficient than web + browser)
- Reduce update frequency
- Lower sample rate when not needed

---

## ❓ FAQ

<details>
<summary><b>Do I need an SDR to use WaveRider SDR?</b></summary>

No! WaveRider SDR works in demonstration mode with simulated signals if no hardware is detected. This lets you explore the interface and features before investing in hardware.

</details>

<details>
<summary><b>Which SDR should I buy?</b></summary>

For beginners:
- **RTL-SDR Blog V3** (~$30) - Great starter, excellent value
- **NooElec NESDR Smart v4** (~$25) - Good alternative

For advanced users:
- **HackRF One** (~$300) - Transmit + receive, wider range
- **Airspy** (~$200) - Better performance

</details>

<details>
<summary><b>Can I transmit with WaveRider SDR?</b></summary>

Currently, WaveRider SDR is receive-only. Transmission features may be added in future versions. (Transmitting requires proper licensing!)

</details>

<details>
<summary><b>Is WaveRider SDR free?</b></summary>

Yes! WaveRider SDR is open source under the MIT License. Free to use, modify, and distribute.

</details>

<details>
<summary><b>Can I use this for commercial purposes?</b></summary>

Yes, the MIT License permits commercial use. See [LICENSE](LICENSE) for details.

</details>

<details>
<summary><b>What frequencies can I receive?</b></summary>

Depends on your hardware:
- **RTL-SDR**: ~24 MHz to 1.7 GHz (coverage gaps vary by model)
- **HackRF One**: 1 MHz to 6 GHz (with gaps)

Note: Reception quality varies by frequency, antenna, and environment.

</details>

<details>
<summary><b>Is it legal to listen to radio signals?</b></summary>

In most countries, receiving radio signals is legal. However:
- ❌ Don't decode encrypted/scrambled communications
- ❌ Don't listen to cellular/mobile phone calls
- ❌ Don't disclose private communications
- ✅ Amateur radio, public safety, broadcast, aviation - typically OK

**Check your local laws!** Regulations vary by country.

</details>

<details>
<summary><b>Why is there no audio output?</b></summary>

Audio output is in development. Currently, demodulation is visual only. Future versions will add audio support.

</details>

<details>
<summary><b>Can I record signals?</b></summary>

Not yet - recording functionality is planned for future release. For now, use other tools like `rtl_sdr` for recording.

</details>

<details>
<summary><b>Does it work offline?</b></summary>

Yes! Once installed, WaveRider SDR works completely offline. No internet connection required.

</details>

---

## 📜 License

WaveRider SDR is licensed under the **MIT License**.

**What this means:**
- ✅ Free to use
- ✅ Free to modify
- ✅ Free to distribute
- ✅ Commercial use allowed
- ✅ Private use allowed
- ⚠️ No warranty provided
- ⚠️ Author not liable

See [LICENSE](LICENSE) file for full details.

---

## 👏 Acknowledgments

**Built with:**
- [Python](https://www.python.org/) - Programming language
- [NumPy](https://numpy.org/) - Numerical computing
- [SciPy](https://scipy.org/) - Scientific computing
- [Matplotlib](https://matplotlib.org/) - Plotting and visualization
- [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) - Desktop GUI
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Socket.IO](https://socket.io/) - Real-time communication
- [pyrtlsdr](https://github.com/roger-/pyrtlsdr) - RTL-SDR Python bindings
- [SoapySDR](https://github.com/pothosware/SoapySDR) - SDR abstraction layer

**Inspired by:**
- GQRX
- SDR#
- CubicSDR
- GNU Radio

**Special thanks to:**
- The open source SDR community
- RTL-SDR.com team
- HackRF project
- All contributors and testers

---

## 📞 Support

### Getting Help

1. **📖 Documentation**: Read this README and [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
2. **🐛 Bug Reports**: [GitHub Issues](https://github.com/Deployed-Labs/WaveRiderSDR/issues)
3. **💬 Discussions**: [GitHub Discussions](https://github.com/Deployed-Labs/WaveRiderSDR/discussions)
4. **⭐ Star the Project**: Show your support!

### Stay Updated

- **Watch** the repository for updates
- **Star** to bookmark
- **Fork** to contribute

---

<div align="center">

**Made with ❤️ by the WaveRider SDR Team**

[⬆ Back to Top](#-waverider-sdr-)

</div> 
