"""
WaveRider SDR Universal Launcher
Automatically detects the platform and starts the appropriate version
"""

import sys
import os
import platform
import subprocess


def detect_environment():
    """Detect the running environment and capabilities"""
    env_info = {
        'os': platform.system(),
        'os_version': platform.version(),
        'python_version': sys.version,
        'architecture': platform.machine(),
        'has_display': False,
        'is_desktop': False,
        'is_server': False,
    }
    
    # Check if running on desktop environment
    if env_info['os'] in ['Windows', 'Darwin', 'Linux']:
        env_info['is_desktop'] = True
        
        # Check for display capability
        if env_info['os'] == 'Windows':
            env_info['has_display'] = True
        elif env_info['os'] == 'Darwin':  # macOS
            env_info['has_display'] = True
        elif env_info['os'] == 'Linux':
            # Check for DISPLAY environment variable
            env_info['has_display'] = 'DISPLAY' in os.environ
    
    # Check if this is a server environment (no display)
    if not env_info['has_display']:
        env_info['is_server'] = True
    
    return env_info


def check_dependencies(mode='desktop'):
    """Check if required dependencies are installed"""
    missing = []
    
    # Common dependencies
    try:
        import numpy
    except ImportError:
        missing.append('numpy')
    
    try:
        import scipy
    except ImportError:
        missing.append('scipy')
    
    try:
        import matplotlib
    except ImportError:
        missing.append('matplotlib')
    
    # Mode-specific dependencies
    if mode == 'desktop':
        try:
            import PyQt5
        except ImportError:
            missing.append('PyQt5')
    elif mode == 'web':
        try:
            import flask
        except ImportError:
            missing.append('flask')
        
        try:
            import flask_socketio
        except ImportError:
            missing.append('flask-socketio')
    
    return missing


def install_dependencies(packages):
    """Install missing dependencies"""
    print(f"\nInstalling missing dependencies: {', '.join(packages)}")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + packages)
        return True
    except subprocess.CalledProcessError:
        return False


def launch_desktop_version():
    """Launch the desktop PyQt5 version"""
    print("Launching WaveRider SDR Desktop Version...")
    print("Platform: Desktop with GUI support")
    
    try:
        import waverider_sdr
        waverider_sdr.main()
    except Exception as e:
        print(f"Error launching desktop version: {e}")
        print("\nFalling back to web version...")
        launch_web_version()


def launch_web_version():
    """Launch the web-based version"""
    print("Launching WaveRider SDR Web Version...")
    print("Platform: Cross-platform web interface")
    print("Access from any device at: http://localhost:5000")
    print("Or from other devices at: http://<your-ip>:5000")
    
    try:
        import waverider_web
        waverider_web.main()
    except Exception as e:
        print(f"Error launching web version: {e}")
        sys.exit(1)


def print_banner():
    """Print welcome banner"""
    banner = """
    ╔═══════════════════════════════════════════════════╗
    ║                                                   ║
    ║          🌊  WAVERIDER SDR  🌊                   ║
    ║                                                   ║
    ║       Universal Cross-Platform Launcher          ║
    ║                                                   ║
    ║   Works on: Windows, macOS, Linux, iOS, Android  ║
    ║                                                   ║
    ╚═══════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main launcher function"""
    print_banner()
    
    # Detect environment
    print("Detecting platform and capabilities...")
    env = detect_environment()
    
    print(f"\nPlatform Information:")
    print(f"  OS: {env['os']}")
    print(f"  Architecture: {env['architecture']}")
    print(f"  Python: {sys.version.split()[0]}")
    print(f"  Display Available: {env['has_display']}")
    print(f"  Desktop Environment: {env['is_desktop']}")
    
    # Determine which version to launch
    launch_mode = None
    
    # Check command line arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg in ['--web', '-w']:
            launch_mode = 'web'
            print("\nForce launching web version (specified via command line)")
        elif arg in ['--desktop', '-d']:
            launch_mode = 'desktop'
            print("\nForce launching desktop version (specified via command line)")
        elif arg in ['--help', '-h']:
            print("\nUsage: python run.py [OPTIONS]")
            print("\nOptions:")
            print("  --web, -w          Force web version")
            print("  --desktop, -d      Force desktop version")
            print("  --auto-install     Automatically install missing dependencies (no prompt)")
            print("  --help, -h         Show this help message")
            sys.exit(0)
    
    # Auto-detect if not specified
    if not launch_mode:
        if env['is_desktop'] and env['has_display']:
            # Desktop with display - try desktop version first
            print("\nDesktop environment detected with display support")
            missing = check_dependencies('desktop')
            if not missing:
                launch_mode = 'desktop'
            else:
                print(f"Desktop dependencies missing: {', '.join(missing)}")
                print("Will use web version instead")
                launch_mode = 'web'
        else:
            # No display or server environment - use web version
            print("\nNo display detected or server environment")
            print("Using web version for maximum compatibility")
            launch_mode = 'web'
    
    # Check and install dependencies for chosen mode
    print(f"\nChecking dependencies for {launch_mode} version...")
    missing = check_dependencies(launch_mode)
    
    if missing:
        print(f"\nMissing dependencies: {', '.join(missing)}")
        
        # Check if running in non-interactive environment
        if not sys.stdin.isatty() or '--auto-install' in sys.argv:
            print("Auto-installing dependencies...")
            if install_dependencies(missing):
                print("Dependencies installed successfully!")
            else:
                print("Failed to install dependencies.")
                print("Please install manually: pip install " + " ".join(missing))
                sys.exit(1)
        else:
            response = input("Would you like to install them now? (y/n): ")
            if response.lower() in ['y', 'yes']:
                if install_dependencies(missing):
                    print("Dependencies installed successfully!")
                else:
                    print("Failed to install dependencies.")
                    print("Please install manually: pip install " + " ".join(missing))
                    sys.exit(1)
            else:
                print("Cannot continue without required dependencies.")
                sys.exit(1)
    else:
        print("All dependencies satisfied!")
    
    # Launch appropriate version
    print()
    if launch_mode == 'desktop':
        launch_desktop_version()
    else:
        launch_web_version()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nShutdown requested... exiting")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
