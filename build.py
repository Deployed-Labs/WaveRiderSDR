"""
WaveRider SDR Build Script
Creates standalone executables for Windows, macOS, and Linux using PyInstaller
"""

import sys
import os
import platform
import subprocess
import shutil
from pathlib import Path

# Color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def supports_utf8():
    """Check if the current console supports UTF-8 encoding"""
    try:
        # Try to encode Unicode characters
        '▶✓⚠✗'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, AttributeError):
        return False

# Determine which symbols to use based on UTF-8 support
USE_UTF8 = supports_utf8()
SYMBOLS = {
    'step': '▶' if USE_UTF8 else '>',
    'success': '✓' if USE_UTF8 else 'OK',
    'warning': '⚠' if USE_UTF8 else '!',
    'error': '✗' if USE_UTF8 else 'X'
}

def print_banner():
    """Print build script banner"""
    print(f"{Colors.CYAN}")
    print("╔═══════════════════════════════════════════════════╗")
    print("║                                                   ║")
    print("║            WAVERIDER SDR                          ║")
    print("║                                                   ║")
    print("║            Build Script                          ║")
    print("║                                                   ║")
    print(f"║   Platform: {platform.system():<37}║")
    print("║                                                   ║")
    print("╚═══════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}")

def print_step(message):
    """Print step message"""
    print(f"{Colors.BLUE}{SYMBOLS['step']}{Colors.RESET} {message}")

def print_success(message):
    """Print success message"""
    print(f"{Colors.GREEN}{SYMBOLS['success']}{Colors.RESET} {message}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.YELLOW}{SYMBOLS['warning']}{Colors.RESET} {message}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.RED}{SYMBOLS['error']}{Colors.RESET} {message}")

def check_pyinstaller():
    """Check if PyInstaller is installed"""
    print_step("Checking PyInstaller installation...")
    try:
        import PyInstaller
        print_success(f"PyInstaller {PyInstaller.__version__} found")
        return True
    except ImportError:
        print_warning("PyInstaller not found")
        return False

def install_pyinstaller():
    """Install PyInstaller"""
    print_step("Installing PyInstaller...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        print_success("PyInstaller installed successfully")
        return True
    except subprocess.CalledProcessError:
        print_error("Failed to install PyInstaller")
        return False

def clean_build_dirs():
    """Clean previous build directories"""
    print_step("Cleaning previous build directories...")
    dirs_to_clean = ['build', 'dist', '__pycache__']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"  Removed: {dir_name}")
    
    # Remove spec files
    for spec_file in Path('.').glob('*.spec'):
        spec_file.unlink()
        print(f"  Removed: {spec_file}")
    
    print_success("Build directories cleaned")

def create_spec_file():
    """Create PyInstaller spec file"""
    print_step("Creating PyInstaller spec file...")
    
    system = platform.system()
    
    # Determine icon file (if available)
    icon_option = ""
    # We'll add icon files later if needed
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates', 'templates'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'numpy',
        'scipy',
        'scipy.fft',
        'scipy.signal',
        'matplotlib',
        'matplotlib.pyplot',
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtWidgets',
        'PyQt5.QtGui',
        'flask',
        'flask_socketio',
        'socketio',
        'pyserial',
        'serial',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WaveRiderSDR',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console={True if system != 'Windows' else False},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WaveRiderSDR',
)

"""
    
    # Add macOS app bundle if on macOS
    if system == 'Darwin':
        spec_content += """
app = BUNDLE(
    coll,
    name='WaveRiderSDR.app',
    icon=None,
    bundle_identifier='com.waverider.sdr',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
    },
)
"""
    
    with open('waverider.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print_success("Spec file created: waverider.spec")

def build_executable():
    """Build the executable using PyInstaller"""
    print_step("Building executable with PyInstaller...")
    print()
    
    try:
        cmd = [
            sys.executable,
            '-m',
            'PyInstaller',
            'waverider.spec',
            '--clean',
            '--noconfirm',
        ]
        
        subprocess.check_call(cmd)
        print()
        print_success("Build completed successfully")
        return True
    except subprocess.CalledProcessError:
        print()
        print_error("Build failed")
        return False

def create_readme_for_dist():
    """Create a README for the distribution"""
    print_step("Creating distribution README...")
    
    system = platform.system()
    
    readme_content = """# WaveRider SDR - Standalone Distribution

## Quick Start

"""
    
    if system == 'Windows':
        readme_content += """### Windows

1. Extract the ZIP file to a folder
2. Run `WaveRiderSDR.exe`
3. The application will automatically detect your platform and launch

### Running Different Modes

- **Auto-detect**: Double-click `WaveRiderSDR.exe`
- **Web version**: Run `WaveRiderSDR.exe --web` from Command Prompt
- **Desktop version**: Run `WaveRiderSDR.exe --desktop` from Command Prompt

"""
    elif system == 'Darwin':
        readme_content += """### macOS

1. Extract the ZIP file
2. Run `WaveRiderSDR.app` or the `WaveRiderSDR` binary in the folder
3. The application will automatically detect your platform and launch

### Running Different Modes

From Terminal:
- **Auto-detect**: `./WaveRiderSDR`
- **Web version**: `./WaveRiderSDR --web`
- **Desktop version**: `./WaveRiderSDR --desktop`

"""
    else:  # Linux
        readme_content += """### Linux

1. Extract the archive
2. Make the binary executable: `chmod +x WaveRiderSDR`
3. Run: `./WaveRiderSDR`

### Running Different Modes

- **Auto-detect**: `./WaveRiderSDR`
- **Web version**: `./WaveRiderSDR --web`
- **Desktop version**: `./WaveRiderSDR --desktop`

"""
    
    readme_content += """
## Features

- **Real SDR Hardware Support**: Connect to RTL-SDR and HackRF devices
- **Automatic Device Detection**: Scans for available SDR devices
- **Multiple Modulation Modes**: AM, FM, USB, LSB, CW (Morse)
- **Morse Code Decoder**: Real-time CW decoding
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Dual Interface**: Desktop GUI and web-based access

## SDR Hardware Setup

### RTL-SDR
Install RTL-SDR drivers for your device, then connect and run WaveRider SDR.

### HackRF
Install SoapySDR and HackRF drivers for your platform.

## Documentation

For full documentation, visit:
https://github.com/Deployed-Labs/WaveRiderSDR

## License

See LICENSE file for details.
"""
    
    dist_dir = Path('dist') / 'WaveRiderSDR'
    if dist_dir.exists():
        with open(dist_dir / 'README.txt', 'w', encoding='utf-8') as f:
            f.write(readme_content)
        print_success("Distribution README created")

def create_launcher_scripts():
    """Create convenient launcher scripts"""
    print_step("Creating launcher scripts...")
    
    system = platform.system()
    dist_dir = Path('dist') / 'WaveRiderSDR'
    
    if not dist_dir.exists():
        print_warning("Distribution directory not found")
        return
    
    if system == 'Windows':
        # Create batch files
        launchers = {
            'waverider-web.bat': '@echo off\nWaveRiderSDR.exe --web\npause',
            'waverider-desktop.bat': '@echo off\nWaveRiderSDR.exe --desktop\npause',
        }
        
        for filename, content in launchers.items():
            with open(dist_dir / filename, 'w', encoding='utf-8') as f:
                f.write(content)
    
    elif system in ['Linux', 'Darwin']:
        # Create shell scripts
        launchers = {
            'waverider-web.sh': '#!/bin/bash\ncd "$(dirname "$0")"\n./WaveRiderSDR --web',
            'waverider-desktop.sh': '#!/bin/bash\ncd "$(dirname "$0")"\n./WaveRiderSDR --desktop',
        }
        
        for filename, content in launchers.items():
            script_path = dist_dir / filename
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            script_path.chmod(0o755)  # Make executable
    
    print_success("Launcher scripts created")

def print_completion():
    """Print build completion message"""
    system = platform.system()
    dist_dir = Path('dist') / 'WaveRiderSDR'
    
    print()
    print(f"{Colors.GREEN}╔═══════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.GREEN}║                                                   ║{Colors.RESET}")
    print(f"{Colors.GREEN}║      {SYMBOLS['success']} Build completed successfully!             ║{Colors.RESET}")
    print(f"{Colors.GREEN}║                                                   ║{Colors.RESET}")
    print(f"{Colors.GREEN}╚═══════════════════════════════════════════════════╝{Colors.RESET}")
    print()
    print(f"{Colors.CYAN}Build Output:{Colors.RESET}")
    print(f"  Location: {dist_dir}")
    print()
    
    if system == 'Windows':
        print(f"{Colors.CYAN}Files Created:{Colors.RESET}")
        print("  • WaveRiderSDR.exe - Main executable")
        print("  • waverider-web.bat - Launch web version")
        print("  • waverider-desktop.bat - Launch desktop version")
    elif system == 'Darwin':
        print(f"{Colors.CYAN}Files Created:{Colors.RESET}")
        print("  • WaveRiderSDR.app - macOS application bundle")
        print("  • WaveRiderSDR - Command-line executable")
        print("  • waverider-web.sh - Launch web version")
        print("  • waverider-desktop.sh - Launch desktop version")
    else:  # Linux
        print(f"{Colors.CYAN}Files Created:{Colors.RESET}")
        print("  • WaveRiderSDR - Executable")
        print("  • waverider-web.sh - Launch web version")
        print("  • waverider-desktop.sh - Launch desktop version")
    
    print()
    print(f"{Colors.CYAN}Next Steps:{Colors.RESET}")
    print("  1. Test the executable")
    print(f"  2. Create an archive: {dist_dir}.zip")
    print("  3. Distribute to users")
    print()

def main():
    """Main build process"""
    print_banner()
    
    # Check PyInstaller
    if not check_pyinstaller():
        response = input("\nWould you like to install PyInstaller now? (y/n): ")
        if response.lower() in ['y', 'yes']:
            if not install_pyinstaller():
                sys.exit(1)
        else:
            print_error("PyInstaller is required to build executables")
            sys.exit(1)
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create spec file
    create_spec_file()
    
    # Build executable
    if not build_executable():
        sys.exit(1)
    
    # Create distribution README
    create_readme_for_dist()
    
    # Create launcher scripts
    create_launcher_scripts()
    
    # Print completion message
    print_completion()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Build failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
