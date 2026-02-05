# WaveRiderSDR

The only SDR with full features and rolling updates.

## Features

### 1. Recording and Playback
- **Record IQ Streams**: Capture incoming IQ data streams for offline analysis
- **HDF5 Storage**: Efficient storage format with metadata support
- **Playback Capability**: Review previously recorded data seamlessly
- **Recording Controls**: Easy-to-use interface for starting, stopping, and managing recordings

### 2. Configurable Workspaces
- **Customizable Layouts**: Organize the application interface to match your workflow
- **Save/Load Workspaces**: Store multiple workspace configurations
- **Auto-save**: Automatically save workspace on exit
- **Quick Switching**: Easily switch between different workspace layouts

### 3. Customizable User Interface
- **Multiple Themes**: Choose from Dark, Light, and High Contrast themes
- **Font Scaling**: Adjust text size from 0.5x to 2.0x for better readability
- **Accessible Design**: High-contrast mode and scalable fonts for accessibility
- **Dockable Panels**: Rearrange panels to suit your preferences

### 4. Device Compatibility Database
- **Pre-configured Devices**: Database of known SDR devices with optimal settings
- **Device Information**: Frequency ranges, sample rates, gain settings, and features
- **Search Functionality**: Quickly find devices by name, manufacturer, or type
- **Supported Devices**:
  - RTL-SDR dongles
  - HackRF One
  - Airspy Mini/R2
  - SDRplay RSP1A
  - bladeRF x40
  - And more...

## Installation

### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install from source

```bash
git clone https://github.com/1090mb/WaveRiderSDR.git
cd WaveRiderSDR
pip install -r requirements.txt
```

Or install in development mode:

```bash
pip install -e .
```

## Usage

### Running the Application

```bash
python -m waverider.main
```

Or if installed:

```bash
waverider
```

### Recording IQ Data

1. Click the "Start Recording" button in the Recording panel
2. Recording will begin with default settings (2.048 MHz sample rate, 100 MHz center frequency)
3. Click "Stop Recording" to finish
4. Recordings are saved in the `recordings/` directory as HDF5 files

### Playing Back Recordings

1. Click "Load" in the Playback section
2. Select a recording file (.h5)
3. Use Play/Pause/Stop controls to navigate the recording
4. Progress bar shows current position

### Managing Workspaces

1. Go to **Workspace** → **Manage Workspaces**
2. Select a workspace to load, or create a new one
3. Workspace configurations include:
   - Window size and position
   - Panel visibility and arrangement
   - Toolbar settings

### Customizing the Theme

1. Go to **View** → **Theme Settings**
2. Choose from available themes:
   - **Dark**: Easy on the eyes with blue accents
   - **Light**: Professional light appearance
   - **High Contrast**: Enhanced visibility for accessibility
3. Adjust font scale for better readability
4. Click Apply or OK to save changes

### Browsing Device Database

1. Open the Devices panel (View → Devices)
2. Browse the list of supported SDR devices
3. Use the search box to find specific devices
4. Filter by device type
5. Click on a device to see detailed specifications

## Project Structure

```
WaveRiderSDR/
├── waverider/
│   ├── core/              # Core functionality
│   │   ├── recorder.py    # IQ recording
│   │   ├── player.py      # IQ playback
│   │   └── workspace.py   # Workspace management
│   ├── ui/                # User interface
│   │   ├── main_window.py
│   │   ├── recording_panel.py
│   │   ├── device_panel.py
│   │   ├── workspace_dialog.py
│   │   └── theme_dialog.py
│   ├── config/            # Configuration
│   │   └── theme.py       # Theme management
│   ├── database/          # Device database
│   │   └── devices.py
│   └── main.py           # Application entry point
├── recordings/            # Recorded IQ data (created on first run)
├── workspaces/           # Workspace configurations
├── config/               # User configuration files
├── requirements.txt      # Python dependencies
├── setup.py             # Installation script
└── README.md            # This file
```

## File Formats

### Recording Files (.h5)
Recordings are stored in HDF5 format with the following structure:
- **iq_data**: Complex64 dataset containing IQ samples
- **Attributes**: Metadata including sample rate, center frequency, timestamps

### Workspace Files (.yaml)
Workspace configurations are stored in YAML format with:
- Window geometry
- Panel visibility and positions
- Toolbar settings
- User preferences

### Device Database (devices.json)
JSON format containing device specifications:
- Device identification
- Frequency ranges
- Sample rates
- Gain settings
- Feature flags

## Development

### Adding New Devices

Edit `waverider/database/devices.py` and add device specifications to the `DEFAULT_DEVICES` list.

### Creating Custom Themes

Edit `waverider/config/theme.py` and add new theme definitions to the `THEMES` dictionary.

## License

See LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests. 
