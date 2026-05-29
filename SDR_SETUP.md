# WaveRider SDR - Hardware Setup Guide

This guide explains how to set up RTL-SDR and HackRF devices with WaveRider SDR.

## Quick Setup for Windows

### RTL-SDR Setup

1. **Install the pyrtlsdr Python module:**
   ```bash
   pip install pyrtlsdr
   ```

2. **Install USB drivers (Windows):**
   - Download and run Zadig from: https://zadig.akeo.ie/
   - Plug in your RTL-SDR dongle
   - In Zadig, find your RTL device and install the WinUSB driver
     - Do NOT replace the FTDI or CDC drivers - ensure your device is marked as RTL2832 or similar

3. **Verify installation:**
   - Plug in the RTL-SDR device
   - Launch WaveRider: `launch_gui.bat`
   - Open Device Status drawer
   - You should see "RTL-SDR" in the available devices list
   - Click "Connect" to connect

### HackRF Setup

1. **Install SoapySDR and HackRF module:**
   ```bash
   pip install SoapySDR SoapyHackRF
   ```

2. **Install USB drivers (Windows):**
   - Download the HackRF One driver from: https://github.com/greatscottgadgets/hackrf/releases
   - OR use Zadig:
     - Run Zadig
     - Plug in your HackRF
     - Select the HackRF device and install the WinUSB driver

3. **Verify installation:**
   - Plug in the HackRF device
   - Launch WaveRider: `launch_gui.bat`
   - Open Device Status drawer
   - You should see "HackRF" in the available devices list
   - Click "Connect" to connect

## Troubleshooting

### Device not detected

If your device is not appearing in the "Available devices" list:

1. **Check Python module installation:**
   ```bash
   python -c "import rtlsdr; print('RTL-SDR OK')"
   python -c "import SoapySDR; print('SoapySDR OK')"
   ```

2. **Check USB connection:**
   - Is the device plugged in and powered?
   - Does it appear in Device Manager?

3. **Check device drivers:**
   - Open Device Manager
   - Look for your device under "Universal Serial Bus controllers" or "Libusb-win32 devices"
   - If it has a yellow warning, the driver is not installed correctly

4. **Try a different USB port** - ideally USB 3.0

### "Connection failed" message

If the device is detected but connection fails:

1. **Check for process conflicts:**
   - Close any other SDR software (GQRX, SDR#, CubicSDR, etc.)
   - These may be holding the device open

2. **Check for driver conflicts:**
   - In Device Manager, uninstall the device
   - Unplug it, wait 5 seconds, plug it back in
   - Let Windows reinstall drivers, or manually install with Zadig

3. **Check device firmware:**
   - HackRF: Ensure firmware is up-to-date
   - RTL-SDR: Some clones may need firmware flashing

### Connection timeout

If WaveRider connects but gets no data:

1. Add more time for initialization:
   - The background signal thread may not have started
   - Wait 5-10 seconds and click "Start" to begin capture

2. Check sample rate compatibility:
   - RTL-SDR: best at 2.4 MHz or 1.8 MHz
   - HackRF: supports 2-20 MHz with good results at 4-10 MHz
   - Try different sample rates in the control panel

## Supported Hardware

### RTL-SDR Dongles
- **RTL-SDR v3** (recommended)
- RTL-SDR v2
- RTL-SDR.com Blue
- Generic RTL2832U-based dongles (Realtek chipset)

### HackRF One
- **HackRF One** (recommended)
- HackRF Blue

## Advanced: Building from Source

If the pip packages don't work, you can build drivers from source:

### RTL-SDR (Windows + MSVC/MinGW)
```bash
git clone https://github.com/osmocom/rtl-sdr.git
cd rtl-sdr
mkdir build && cd build
cmake .. -G "Unix Makefiles"
make
make install
```

### HackRF (Windows + MSVC/MinGW)
```bash
git clone https://github.com/greatscottgadgets/hackrf.git
cd hackrf/host
mkdir build && cd build
cmake .. -G "Unix Makefiles"
make
make install
```

## Performance Tips

1. **Use USB 3.0 ports** for HackRF - USB 2.0 may cause sample loss
2. **Reduce FFT size** if the waterfall lags (try 512  or 1024 instead of 4096)
3. **Enable Peak Hold** to see maximum signal levels without jitter
4. **Close other USB devices** to reduce interference
5. **Use shielded USB cables** to reduce noise

## See Also

- [WaveRider GitHub](https://github.com/yourusername/waverider-sdr)
- [RTL-SDR Documentation](https://osmodev.osmocom.org/trac/wiki/rtl-sdr)
- [HackRF Documentation](https://github.com/greatscottgadgets/hackrf/wiki)
