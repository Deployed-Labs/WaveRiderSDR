#!/bin/bash
#
# WaveRider SDR Installation Script for Linux and macOS
# This script automates the installation process for WaveRider SDR
#

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="Unknown";;
esac

print_banner() {
    echo -e "${CYAN}"
    echo "╔═══════════════════════════════════════════════════╗"
    echo "║                                                   ║"
    echo "║          🌊  WAVERIDER SDR  🌊                   ║"
    echo "║                                                   ║"
    echo "║            Installation Script                   ║"
    echo "║                                                   ║"
    echo "║   Platform: ${PLATFORM}                          ║"
    echo "║                                                   ║"
    echo "╚═══════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${BLUE}▶${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_python() {
    print_step "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        print_success "Python ${PYTHON_VERSION} found"
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
        # Check if it's Python 3
        if [[ "$PYTHON_VERSION" == 3* ]]; then
            print_success "Python ${PYTHON_VERSION} found"
            return 0
        else
            print_error "Python 3 is required, but Python ${PYTHON_VERSION} was found"
            return 1
        fi
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

install_python() {
    print_step "Python 3 is required but not found."
    
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "Please install Python 3 using one of these methods:"
        echo "  1. Download from: https://www.python.org/downloads/"
        echo "  2. Install with Homebrew: brew install python3"
    elif [[ "$PLATFORM" == "Linux" ]]; then
        echo "Please install Python 3 using your package manager:"
        echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
        echo "  Fedora: sudo dnf install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
    fi
    
    exit 1
}

check_pip() {
    print_step "Checking pip installation..."
    
    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
        print_success "pip3 found"
        return 0
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
        print_success "pip found"
        return 0
    else
        print_error "pip is not installed"
        return 1
    fi
}

install_dependencies() {
    print_step "Installing Python dependencies..."
    
    if [[ -f "requirements.txt" ]]; then
        $PIP_CMD install -r requirements.txt
        print_success "Dependencies installed successfully"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

install_sdr_support() {
    print_step "Would you like to install SDR hardware support? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_step "Installing SDR hardware libraries..."
        
        # Install pyrtlsdr for RTL-SDR support
        $PIP_CMD install pyrtlsdr
        
        # Platform-specific SoapySDR installation instructions
        if [[ "$PLATFORM" == "macOS" ]]; then
            print_warning "For HackRF support, install SoapySDR with:"
            echo "  brew install soapysdr hackrf"
        elif [[ "$PLATFORM" == "Linux" ]]; then
            print_warning "For HackRF support, install SoapySDR with:"
            if command -v apt-get &> /dev/null; then
                echo "  sudo apt-get install python3-soapysdr soapysdr-module-hackrf"
            elif command -v dnf &> /dev/null; then
                echo "  sudo dnf install python3-SoapySDR SoapySDR-module-hackrf"
            else
                echo "  Check your distribution's package manager for SoapySDR"
            fi
        fi
        
        print_success "SDR support installed"
    fi
}

create_launcher() {
    print_step "Creating launcher script..."
    
    # Create a simple launcher script
    cat > waverider << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 run.py "$@"
EOF
    
    chmod +x waverider
    print_success "Launcher script created: ./waverider"
}

create_desktop_entry() {
    if [[ "$PLATFORM" != "Linux" ]]; then
        return
    fi
    
    print_step "Would you like to create a desktop shortcut? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        INSTALL_DIR="$(pwd)"
        DESKTOP_FILE="$HOME/.local/share/applications/waverider-sdr.desktop"
        
        mkdir -p "$HOME/.local/share/applications"
        
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=WaveRider SDR
Comment=Universal Cross-Platform SDR Application
Exec=$PYTHON_CMD $INSTALL_DIR/run.py
Path=$INSTALL_DIR
Icon=radio
Terminal=false
Categories=HamRadio;AudioVideo;Audio;
Keywords=SDR;Radio;HAM;RTL-SDR;HackRF;
EOF
        
        chmod +x "$DESKTOP_FILE"
        print_success "Desktop entry created"
        
        # Update desktop database if available
        if command -v update-desktop-database &> /dev/null; then
            update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
        fi
    fi
}

test_installation() {
    print_step "Testing installation..."
    
    if $PYTHON_CMD -c "import numpy, scipy, matplotlib" 2>/dev/null; then
        print_success "Core dependencies verified"
    else
        print_error "Core dependencies test failed"
        exit 1
    fi
}

print_completion() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║                                                   ║${NC}"
    echo -e "${GREEN}║      ✓ Installation completed successfully!      ║${NC}"
    echo -e "${GREEN}║                                                   ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${CYAN}Quick Start:${NC}"
    echo ""
    echo -e "  ${YELLOW}1.${NC} Run WaveRider SDR:"
    echo -e "     ${GREEN}$PYTHON_CMD run.py${NC}"
    echo -e "     or use the launcher: ${GREEN}./waverider${NC}"
    echo ""
    echo -e "  ${YELLOW}2.${NC} For web version (access from mobile):"
    echo -e "     ${GREEN}$PYTHON_CMD run.py --web${NC}"
    echo ""
    echo -e "  ${YELLOW}3.${NC} For desktop GUI version:"
    echo -e "     ${GREEN}$PYTHON_CMD run.py --desktop${NC}"
    echo ""
    echo -e "${CYAN}Documentation:${NC}"
    echo "  • README.md - Full documentation"
    echo "  • PLATFORM_GUIDE.md - Platform-specific guides"
    echo ""
    echo -e "${CYAN}Need help?${NC}"
    echo "  • GitHub: https://github.com/1090mb/WaveRiderSDR"
    echo ""
}

main() {
    print_banner
    
    # Check Python installation
    if ! check_python; then
        install_python
    fi
    
    # Check pip installation
    if ! check_pip; then
        print_error "Please install pip for Python 3"
        exit 1
    fi
    
    # Install dependencies
    install_dependencies
    
    # Optional SDR hardware support
    install_sdr_support
    
    # Create launcher script
    create_launcher
    
    # Create desktop entry (Linux only)
    create_desktop_entry
    
    # Test installation
    test_installation
    
    # Print completion message
    print_completion
}

# Run main function
main
