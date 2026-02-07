# WaveRider SDR - Quick Start Guide

Get up and running with WaveRider SDR in under 5 minutes!

## 🚀 Installation

### Option 1: One-Line Install (Easiest)

**Linux/macOS:**
```bash
curl -fsSL https://raw.githubusercontent.com/1090mb/WaveRiderSDR/main/install.sh | bash
```

**Windows PowerShell:**
```powershell
iwr https://raw.githubusercontent.com/1090mb/WaveRiderSDR/main/install.ps1 -UseBasicParsing | iex
```

### Option 2: Quick Manual Install

```bash
# Clone repository
git clone https://github.com/1090mb/WaveRiderSDR.git
cd WaveRiderSDR

# Install dependencies
pip install -r requirements.txt

# Run!
python run.py
```

## 🎮 First Steps

### 1. Launch WaveRider SDR

```bash
python run.py
```

The app will automatically:
- ✅ Detect your platform
- ✅ Choose the best interface
- ✅ Check for SDR hardware
- ✅ Start the application

### 2. Explore Without Hardware

Don't have an SDR yet? No problem!

WaveRider SDR runs in **demo mode** with simulated signals:
- View the waterfall display
- Try different frequencies
- Test all the controls
- Learn the interface

### 3. Connect SDR Hardware (Optional)

Have an RTL-SDR or HackRF?

**For RTL-SDR:**
```bash
pip install pyrtlsdr
```

**Then:**
1. Plug in your device
2. Restart WaveRider SDR
3. Select device from dropdown
4. Click "Start"

## 🎯 Quick Tips

### Essential Controls

| Control | What It Does |
|---------|--------------|
| **Center Frequency** | What frequency to tune to (e.g., 100 MHz for FM radio) |
| **Sample Rate** | How much bandwidth to capture |
| **FFT Size** | Trade-off between frequency resolution and speed |
| **Start/Stop** | Begin/end signal capture |

### Popular Frequencies to Try

| Service | Frequency | Modulation |
|---------|-----------|------------|
| FM Radio | 88-108 MHz | FM |
| NOAA Weather | 162.400-162.550 MHz | FM |
| Aircraft | 118-137 MHz | AM |
| Amateur 2m | 144-148 MHz | FM |
| ISM Band | 433.92 MHz | Various |

### Keyboard Shortcuts (Desktop)

- `Space` - Start/Stop
- `↑/↓` - Adjust frequency
- `Ctrl+Q` - Quit

## 📱 Mobile Access

Want to use your phone/tablet?

**Step 1: Start web server**
```bash
python run.py --web
```

**Step 2: Find your IP**
- Windows: `ipconfig`
- Mac/Linux: `ifconfig`

**Step 3: Open browser on phone**
```
http://YOUR_IP:5000
```

Example: `http://192.168.1.100:5000`

## 🆘 Quick Troubleshooting

### "Python not found"
- **Windows**: Reinstall Python, check "Add to PATH"
- **Mac**: `brew install python3`
- **Linux**: `sudo apt install python3`

### "No module named..."
```bash
pip install -r requirements.txt
```

### Device not detected
```bash
# Install SDR support
pip install pyrtlsdr

# Linux: May need driver
sudo apt install rtl-sdr
```

### Can't connect from phone
- Check same WiFi network
- Check firewall (port 5000)
- Try `http://localhost:5000` on server first

## 📚 Learn More

- **Full Documentation**: [README.md](README.md)
- **Platform Guide**: [PLATFORM_GUIDE.md](PLATFORM_GUIDE.md)
- **Contribute**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Report Issues**: [GitHub Issues](https://github.com/1090mb/WaveRiderSDR/issues)

## 💡 Next Steps

1. ✅ Install and run
2. ✅ Explore demo mode
3. ✅ Try mobile access
4. 🎯 Get an RTL-SDR (~$25)
5. 🎯 Tune to interesting frequencies
6. 🎯 Try different modulation modes
7. 🎯 Join the community!

---

**Got questions?** Open a [Discussion](https://github.com/1090mb/WaveRiderSDR/discussions)

**Found a bug?** File an [Issue](https://github.com/1090mb/WaveRiderSDR/issues)

**Want to help?** Read [CONTRIBUTING.md](CONTRIBUTING.md)

---

**Happy SDR-ing! 🌊📡**
