# WaveRider SDR Installation Script for Windows PowerShell
# This script automates the installation process for WaveRider SDR

# Requires PowerShell 5.0 or higher
#Requires -Version 5.0

# Color scheme
$Colors = @{
    Title = 'Cyan'
    Success = 'Green'
    Warning = 'Yellow'
    Error = 'Red'
    Info = 'Blue'
}

function Write-Banner {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Colors.Title
    Write-Host ""
    Write-Host "          WAVERIDER SDR - Windows Installation" -ForegroundColor $Colors.Title
    Write-Host ""
    Write-Host "          Platform: Windows PowerShell" -ForegroundColor $Colors.Title
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Colors.Title
    Write-Host ""
}

function Write-Step {
    param([string]$Message)
    Write-Host "[*] $Message" -ForegroundColor $Colors.Info
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor $Colors.Success
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Colors.Warning
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Colors.Error
}

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Find-PythonCommand {
    Write-Step "Checking Python installation..."
    
    # Try different Python commands
    $pythonCommands = @('python3', 'python', 'py')
    
    foreach ($cmd in $pythonCommands) {
        try {
            $version = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $version -match 'Python 3') {
                Write-Success "$version found"
                return $cmd
            }
        } catch {
            continue
        }
    }
    
    return $null
}

function Install-PythonDependencies {
    param([string]$PythonCmd)
    
    Write-Step "Installing Python dependencies..."
    
    if (-not (Test-Path "requirements.txt")) {
        Write-Error "requirements.txt not found"
        exit 1
    }
    
    try {
        & $PythonCmd -m pip install --upgrade pip
        & $PythonCmd -m pip install -r requirements.txt
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Dependencies installed successfully"
            return $true
        } else {
            Write-Error "Failed to install dependencies"
            return $false
        }
    } catch {
        Write-Error "Error installing dependencies: $_"
        return $false
    }
}

function Install-SDRSupport {
    param([string]$PythonCmd)
    
    $response = Read-Host "`nWould you like to install SDR hardware support? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Step "Installing SDR hardware libraries..."
        
        & $PythonCmd -m pip install pyrtlsdr
        
        Write-Host ""
        Write-Warning "For HackRF support, install SoapySDR:"
        Write-Host "  1. Download from: https://github.com/pothosware/SoapySDR/wiki"
        Write-Host "  2. Install HackRF drivers: https://github.com/greatscottgadgets/hackrf"
        Write-Host ""
    }
}

function New-LauncherScripts {
    Write-Step "Creating launcher scripts..."
    
    $scriptDir = $PSScriptRoot
    $pythonCmd = $global:PythonCommand
    
    # Main launcher
    $mainContent = @"
@echo off
cd /d "%~dp0"
$pythonCmd run.py %*
"@
    Set-Content -Path "waverider.bat" -Value $mainContent
    
    # Web launcher
    $webContent = @"
@echo off
cd /d "%~dp0"
$pythonCmd run.py --web
"@
    Set-Content -Path "waverider-web.bat" -Value $webContent
    
    # Desktop launcher
    $desktopContent = @"
@echo off
cd /d "%~dp0"
$pythonCmd run.py --desktop
"@
    Set-Content -Path "waverider-desktop.bat" -Value $desktopContent
    
    # PowerShell launcher
    $psContent = @"
Set-Location -Path `$PSScriptRoot
& $pythonCmd run.py `$args
"@
    Set-Content -Path "waverider.ps1" -Value $psContent
    
    Write-Success "Launcher scripts created"
}

function New-DesktopShortcut {
    $response = Read-Host "`nWould you like to create a desktop shortcut? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Step "Creating desktop shortcut..."
        
        $desktopPath = [Environment]::GetFolderPath("Desktop")
        $shortcutPath = Join-Path $desktopPath "WaveRider SDR.lnk"
        $targetPath = Join-Path $PSScriptRoot "waverider.bat"
        $workingDir = $PSScriptRoot
        
        $WScriptShell = New-Object -ComObject WScript.Shell
        $shortcut = $WScriptShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $targetPath
        $shortcut.WorkingDirectory = $workingDir
        $shortcut.Description = "WaveRider SDR - Universal Cross-Platform Application"
        $shortcut.Save()
        
        Write-Success "Desktop shortcut created"
    }
}

function Add-FirewallRule {
    if (-not (Test-Administrator)) {
        Write-Warning "Administrator privileges required for firewall configuration"
        Write-Host "  Re-run this script as Administrator to configure firewall"
        return
    }
    
    $response = Read-Host "`nWould you like to configure Windows Firewall for mobile access? (y/n)"
    
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Step "Configuring Windows Firewall..."
        
        try {
            # Remove old rule if exists
            $null = netsh advfirewall firewall delete rule name="WaveRider SDR" 2>&1
            
            # Add new rule restricted to local subnet
            $result = netsh advfirewall firewall add rule `
                name="WaveRider SDR" `
                dir=in `
                action=allow `
                protocol=TCP `
                localport=5000 `
                remoteip=localsubnet `
                profile=private 2>&1
            
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Firewall rule added (restricted to local network)"
            } else {
                Write-Warning "Failed to add firewall rule"
            }
        } catch {
            Write-Warning "Error configuring firewall: $_"
        }
    }
}

function Test-Installation {
    param([string]$PythonCmd)
    
    Write-Step "Testing installation..."
    
    try {
        & $PythonCmd -c "import numpy, scipy, matplotlib" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Core dependencies verified"
            return $true
        } else {
            Write-Warning "Some dependencies may not be properly installed"
            return $false
        }
    } catch {
        Write-Warning "Error testing installation: $_"
        return $false
    }
}

function Write-CompletionMessage {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "      INSTALLATION COMPLETED SUCCESSFULLY!" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "Quick Start:" -ForegroundColor $Colors.Title
    Write-Host ""
    Write-Host "  1. Run WaveRider SDR:"
    Write-Host "     .\waverider.bat" -ForegroundColor $Colors.Success
    Write-Host "     or: $($global:PythonCommand) run.py" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "  2. For web version (access from mobile):"
    Write-Host "     .\waverider-web.bat" -ForegroundColor $Colors.Success
    Write-Host "     or: $($global:PythonCommand) run.py --web" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "  3. For desktop GUI version:"
    Write-Host "     .\waverider-desktop.bat" -ForegroundColor $Colors.Success
    Write-Host "     or: $($global:PythonCommand) run.py --desktop" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "  4. Using PowerShell:"
    Write-Host "     .\waverider.ps1" -ForegroundColor $Colors.Success
    Write-Host ""
    Write-Host "Documentation:" -ForegroundColor $Colors.Title
    Write-Host "  * README.md - Full documentation"
    Write-Host "  * PLATFORM_GUIDE.md - Platform-specific guides"
    Write-Host ""
    Write-Host "Need help?" -ForegroundColor $Colors.Title
    Write-Host "  * GitHub: https://github.com/1090mb/WaveRiderSDR"
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor $Colors.Title
    Write-Host ""
}

# Main installation process
function Main {
    Write-Banner
    
    # Find Python
    $pythonCmd = Find-PythonCommand
    if (-not $pythonCmd) {
        Write-Error "Python 3 is not installed or not in PATH"
        Write-Host ""
        Write-Host "Please install Python 3 from:"
        Write-Host "  https://www.python.org/downloads/"
        Write-Host ""
        Write-Host "Make sure to check 'Add Python to PATH' during installation!"
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    $global:PythonCommand = $pythonCmd
    
    # Install dependencies
    if (-not (Install-PythonDependencies $pythonCmd)) {
        Read-Host "Press Enter to exit"
        exit 1
    }
    
    # Optional SDR support
    Install-SDRSupport $pythonCmd
    
    # Create launcher scripts
    New-LauncherScripts
    
    # Create desktop shortcut
    New-DesktopShortcut
    
    # Configure firewall
    Add-FirewallRule
    
    # Test installation
    Test-Installation $pythonCmd
    
    # Show completion message
    Write-CompletionMessage
    
    Read-Host "Press Enter to exit"
}

# Run main
Main
