# WaveRider SDR - Installation & Build Summary

## 📦 Available Installation Methods

WaveRider SDR offers multiple installation methods to suit different user needs:

### 1. Automated Installation Scripts (Recommended for Most Users)

**Linux/macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Windows (Batch):**
```cmd
install.bat
```

**Windows (PowerShell - Recommended):**
```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

**Features:**
- Automatic Python and pip detection
- Dependency installation with user confirmation
- Optional SDR hardware support installation
- Launcher script creation (waverider, waverider-web.sh, etc.)
- Desktop shortcut creation (optional)
- Firewall configuration (optional, restricted to local subnet)
- Installation verification

**What Gets Created:**
- `waverider` / `waverider.bat` - Main launcher
- `waverider-web.sh` / `waverider-web.bat` - Web version launcher
- `waverider-desktop.sh` / `waverider-desktop.bat` - Desktop version launcher
- Desktop shortcut (if selected)
- Firewall rules (if selected, Windows only)

### 2. Pre-Built Executables (No Python Required)

Download from [Releases](https://github.com/1090mb/WaveRiderSDR/releases):

- **Windows**: `WaveRiderSDR-Windows.zip` → Extract → Run `WaveRiderSDR.exe`
- **macOS**: `WaveRiderSDR-macOS.zip` → Extract → Open `WaveRiderSDR.app`
- **Linux**: `WaveRiderSDR-Linux.tar.gz` → Extract → Run `./WaveRiderSDR`

**Advantages:**
- No Python installation needed
- Portable (can run from USB)
- Single executable
- Instant startup

**Disadvantages:**
- Larger file size (~100-200 MB)
- Can't easily modify code
- May trigger antivirus false positives

### 3. Python Package Installation

**Standard pip install:**
```bash
pip install -r requirements.txt
python run.py
```

**Development install:**
```bash
pip install -e ".[all]"
waverider
```

**Advantages:**
- Easy updates via git pull
- Can modify source code
- Standard Python workflow
- Small download size

### 4. Building Executables (For Developers)

Create standalone executables for distribution:

```bash
# Install PyInstaller
pip install pyinstaller

# Build for current platform
python build.py
```

**Output locations:**
- Windows: `dist/WaveRiderSDR/WaveRiderSDR.exe`
- macOS: `dist/WaveRiderSDR.app` and `dist/WaveRiderSDR/WaveRiderSDR`
- Linux: `dist/WaveRiderSDR/WaveRiderSDR`

**Build process includes:**
- Dependency bundling
- Asset inclusion (templates, documentation)
- Platform-specific optimizations
- Launcher script creation
- Distribution README generation

## 🔧 System Requirements

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| **OS** | Windows 7+ / macOS 10.14+ / Linux (any modern distro) |
| **Python** | 3.8 or higher (not needed for executables) |
| **RAM** | 2 GB minimum, 4 GB recommended |
| **Disk Space** | 500 MB for source, 200 MB for executable |
| **Display** | 1024x768 minimum resolution |
| **Network** | Internet for initial install only |

### Recommended for SDR Use

| Component | Recommendation |
|-----------|----------------|
| **CPU** | Multi-core processor (2+ cores) |
| **RAM** | 4 GB or more |
| **USB** | USB 2.0 or higher for SDR devices |
| **OS** | Windows 10/11, macOS 12+, Ubuntu 20.04+ |

## 📡 SDR Hardware Setup

### RTL-SDR Support

**Installation:**
```bash
pip install pyrtlsdr
```

**Drivers:**
- **Windows**: Use [Zadig](https://zadig.akeo.ie/) to install WinUSB driver
- **Linux**: `sudo apt-get install rtl-sdr librtlsdr-dev`
- **macOS**: `brew install librtlsdr`

**Verification:**
```bash
rtl_test
# Should display: "Found 1 device(s)"
```

### HackRF Support

**Installation:**

Ubuntu/Debian:
```bash
sudo apt-get install python3-soapysdr soapysdr-module-hackrf
```

macOS:
```bash
brew install soapysdr hackrf
```

Windows:
- Download SoapySDR from [GitHub](https://github.com/pothosware/SoapySDR/wiki)
- Download HackRF drivers from [GitHub](https://github.com/greatscottgadgets/hackrf)

**Verification:**
```bash
SoapySDRUtil --find
# Should list HackRF device
```

## 🚀 Post-Installation

### Running WaveRider SDR

**Method 1: Universal Launcher**
```bash
python run.py              # Auto-detect
python run.py --web        # Force web version
python run.py --desktop    # Force desktop GUI
```

**Method 2: Launcher Scripts** (created by installer)
```bash
./waverider                # Auto-detect (Linux/macOS)
waverider.bat              # Auto-detect (Windows)
./waverider-web.sh         # Web version (Linux/macOS)
waverider-web.bat          # Web version (Windows)
```

**Method 3: Direct Module** (development)
```bash
python waverider_sdr.py    # Desktop GUI
python waverider_web.py    # Web interface
```

### First Run Checklist

- [ ] Application launches without errors
- [ ] Interface loads correctly
- [ ] SDR device appears in dropdown (if connected)
- [ ] Can select device and click "Start"
- [ ] Waterfall display shows signals
- [ ] Controls respond to changes
- [ ] Can access web interface from mobile (if using web version)

### Troubleshooting Installation

**Python not found:**
- Verify Python is in PATH: `python --version`
- Try `python3` instead of `python`
- Reinstall Python with "Add to PATH" checked

**Dependencies fail to install:**
```bash
# Update pip first
python -m pip install --upgrade pip

# Try installing individually
pip install numpy
pip install scipy
pip install matplotlib
# etc.
```

**Permission errors (Linux/macOS):**
```bash
# Use pip with user flag
pip install --user -r requirements.txt

# Or create virtual environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**SDR device not detected:**
1. Verify device is plugged in
2. Check USB cable and port
3. Install/reinstall drivers
4. Try different USB port
5. Check device manager (Windows) / lsusb (Linux)

## 📊 Build Sizes (Approximate)

| Package Type | Windows | macOS | Linux | Notes |
|--------------|---------|-------|-------|-------|
| **Source** | 500 KB | 500 KB | 500 KB | Requires Python + deps |
| **Executable** | 180 MB | 150 MB | 160 MB | Standalone, no Python needed |
| **Dependencies** | 300 MB | 300 MB | 300 MB | When pip installed |
| **Total (Dev)** | 800 MB | 800 MB | 800 MB | Source + deps + venv |

## 🔐 Security Considerations

### Installation Scripts

- Scripts only install from PyPI (official Python repository)
- Firewall rules restricted to local subnet only
- No external downloads except Python packages
- All scripts are open source and auditable

### Network Security

**Default Configuration:**
- Web server binds to `0.0.0.0:5000` (all interfaces)
- Allows local network access
- No authentication by default

**Recommended Security Practices:**
1. Use firewall rules to restrict to local network
2. Don't expose to internet without VPN/HTTPS
3. Only use on trusted networks
4. Configure for localhost-only if no mobile access needed

**Firewall Rules (Automatically Created by Installers):**
```bash
# Windows (PowerShell - restricts to local subnet)
netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000 remoteip=localsubnet profile=private

# Linux (UFW - restricts to local networks)
sudo ufw allow from 192.168.0.0/16 to any port 5000 proto tcp
sudo ufw allow from 10.0.0.0/8 to any port 5000 proto tcp
```

## 📚 Additional Resources

- **Main Documentation**: [README.md](README.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Platform Guide**: [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)

## 🆘 Getting Help

If you encounter issues during installation:

1. **Check documentation** - Most common issues are covered
2. **Search existing issues** - Someone may have solved it
3. **Open new issue** - Include OS, Python version, error messages
4. **Join discussions** - Ask questions, share experiences

**Links:**
- [GitHub Issues](https://github.com/1090mb/WaveRiderSDR/issues)
- [GitHub Discussions](https://github.com/1090mb/WaveRiderSDR/discussions)
- [Documentation](https://github.com/1090mb/WaveRiderSDR)

---

**Installation completed successfully? Star the repository! ⭐**
