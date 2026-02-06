# WaveRider SDR - Platform-Specific Usage Examples

This guide provides detailed examples for running WaveRider SDR on different platforms.

## 🖥️ Desktop Platforms

### Windows

```powershell
# Open Command Prompt or PowerShell

# Install Python (if not already installed)
# Download from: https://www.python.org/downloads/

# Install dependencies
pip install -r requirements.txt

# Run universal launcher (recommended)
python run.py

# Or run specific version:
python waverider_sdr.py  # Desktop GUI
python waverider_web.py  # Web interface
```

**Opening firewall for mobile access:**
```powershell
# Run as Administrator
netsh advfirewall firewall add rule name="WaveRider SDR" dir=in action=allow protocol=TCP localport=5000
```

### macOS

```bash
# Open Terminal

# Install Python (if not already installed)
brew install python3

# Install dependencies
pip3 install -r requirements.txt

# Run universal launcher (recommended)
python3 run.py

# Or run specific version:
python3 waverider_sdr.py  # Desktop GUI
python3 waverider_web.py  # Web interface
```

**Opening firewall for mobile access:**
1. System Preferences → Security & Privacy → Firewall
2. Click "Firewall Options"
3. Add Python to allowed applications

### Linux (Ubuntu/Debian)

```bash
# Open Terminal

# Install Python and pip (if not already installed)
sudo apt update
sudo apt install python3 python3-pip

# Install dependencies
pip3 install -r requirements.txt

# Run universal launcher (recommended)
python3 run.py

# Or run specific version:
python3 waverider_sdr.py  # Desktop GUI
python3 waverider_web.py  # Web interface
```

**Opening firewall for mobile access:**
```bash
# For UFW (Ubuntu)
sudo ufw allow 5000/tcp

# For firewalld (Fedora/CentOS)
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

### Linux (Headless Server/Raspberry Pi)

```bash
# For servers without display

# Install dependencies (web version only)
pip3 install numpy matplotlib scipy flask flask-socketio pyserial

# Run web version
python3 waverider_web.py

# Access from browser at http://<server-ip>:5000
```

## 📱 Mobile Platforms

### iOS (iPhone/iPad)

1. **On your computer:**
   ```bash
   # Start the web server
   python3 waverider_web.py
   
   # Find your computer's IP address
   # macOS: System Preferences → Network
   # Windows: ipconfig in Command Prompt
   # Linux: ip addr or ifconfig
   ```

2. **On your iPhone/iPad:**
   - Open Safari (or any browser)
   - Navigate to: `http://<your-computer-ip>:5000`
   - Example: `http://192.168.1.100:5000`
   - Tap the Share button → "Add to Home Screen" for easy access

**Tips:**
- Works best in landscape mode for full visualization
- Use pinch-to-zoom for detailed inspection
- Compatible with iPad split-view multitasking

### Android (Phone/Tablet)

1. **On your computer:**
   ```bash
   # Start the web server
   python3 waverider_web.py
   
   # Find your computer's IP address
   # Windows: ipconfig
   # macOS/Linux: ifconfig or ip addr
   ```

2. **On your Android device:**
   - Open Chrome (or any browser)
   - Navigate to: `http://<your-computer-ip>:5000`
   - Example: `http://192.168.1.100:5000`
   - Tap the menu (⋮) → "Add to Home screen" for easy access

**Tips:**
- Works on all Android browsers (Chrome, Firefox, Samsung Internet, etc.)
- Supports dark mode if your browser uses it
- Responsive design adapts to any screen size

## 🌐 Network Configuration

### Same WiFi Network (Easiest)

Both your computer and mobile device must be on the same WiFi network:

1. Start WaveRider SDR web version on computer
2. Note your computer's local IP (usually 192.168.x.x or 10.x.x.x)
3. Access from mobile device using `http://<ip>:5000`

### Remote Access (Advanced)

For access from outside your local network:

1. **Port Forwarding:**
   - Configure your router to forward port 5000 to your computer
   - Access using your public IP: `http://<public-ip>:5000`

2. **VPN/Tunnel:**
   - Use a VPN to access your home network remotely
   - Or use a tunnel service like ngrok:
     ```bash
     ngrok http 5000
     # Use the provided URL from any device
     ```

**Security Warning:** When exposing to the internet, consider:
- Using HTTPS (configure reverse proxy with SSL)
- Adding authentication
- Restricting access by IP
- Using a VPN instead of port forwarding

## 🔧 Troubleshooting

### "Module not found" errors

```bash
# Install missing dependencies
pip3 install numpy matplotlib scipy flask flask-socketio pyserial

# Or install everything
pip3 install -r requirements.txt
```

### Desktop GUI won't start

```bash
# Install PyQt5
pip3 install PyQt5

# Or use web version instead
python3 run.py --web
```

### Can't connect from mobile device

1. Verify both devices are on same WiFi network
2. Check firewall allows port 5000
3. Try accessing from computer browser first: `http://localhost:5000`
4. Use computer's local IP, not "localhost" from mobile device
5. Ensure web server shows "Running on all addresses (0.0.0.0)"

### Python version issues

```bash
# WaveRider SDR requires Python 3.7+
python3 --version

# If too old, install newer Python version
```

## 📊 Usage Scenarios

### Scenario 1: Desktop User (Windows/macOS/Linux)

Best for: Full-featured desktop experience with native GUI

```bash
python3 run.py  # Auto-detects and launches desktop version
```

### Scenario 2: Mobile User (Phone/Tablet)

Best for: On-the-go monitoring from mobile devices

```bash
# On computer:
python3 waverider_web.py

# On phone:
# Open browser → http://<computer-ip>:5000
```

### Scenario 3: Server Deployment

Best for: Always-on monitoring accessible from anywhere

```bash
# On server:
python3 waverider_web.py

# From any device:
# Open browser → http://<server-ip>:5000
```

### Scenario 4: Multi-Device Monitoring

Best for: Multiple people monitoring the same SDR

```bash
# One computer runs the server:
python3 waverider_web.py

# Multiple devices can connect simultaneously:
# Desktop browsers: http://<server-ip>:5000
# Mobile devices: http://<server-ip>:5000
# Tablets: http://<server-ip>:5000
```

## 🎯 Quick Reference

| Platform | Command | Requirements |
|----------|---------|--------------|
| **Auto-detect** | `python3 run.py` | All dependencies |
| **Desktop GUI** | `python3 waverider_sdr.py` | PyQt5 + core deps |
| **Web (Desktop)** | `python3 waverider_web.py` | Flask + core deps |
| **Web (Access from phone)** | Browser → `http://<ip>:5000` | Computer running web version |

## 💡 Pro Tips

1. **Bookmark on Mobile**: Add to home screen for app-like experience
2. **Multiple Connections**: Multiple devices can connect to one server
3. **Low Bandwidth**: Web version optimizes images for mobile networks
4. **Offline Desktop**: Desktop version works completely offline
5. **Raspberry Pi**: Works great on Pi 3/4 for portable SDR monitoring
6. **Auto-start**: Use systemd (Linux) or Task Scheduler (Windows) to auto-start
7. **Screen Recording**: Use browser tools to record waterfall displays
8. **Dark Mode**: Automatically adapts to your browser's theme

## 🚀 Getting Started Checklist

- [ ] Install Python 3.7 or higher
- [ ] Clone or download WaveRider SDR
- [ ] Install dependencies: `pip3 install -r requirements.txt`
- [ ] Run universal launcher: `python3 run.py`
- [ ] Verify it works on desktop
- [ ] Find your computer's IP address
- [ ] Open firewall port 5000 (if needed)
- [ ] Access from mobile device: `http://<ip>:5000`
- [ ] Bookmark on mobile for easy access
- [ ] Enjoy cross-platform SDR monitoring! 🎉
