# Installation (Rust)

## Windows

### Release install (recommended)

1. Download the latest MSI:
	https://github.com/Deployed-Labs/WaveRiderSDR/releases/latest/download/WaveRiderSDR-windows-x64.msi
2. Run the MSI.
3. Use the created desktop shortcut: WaveRiderSDR.

### Build MSI locally (PowerShell)

```powershell
.\install.ps1
```

### Build MSI locally (Command Prompt)

```cmd
install.bat
```

After building locally, install with:

```powershell
msiexec /i .\dist\waverider_sdr.msi
```

## Linux / macOS

```bash
chmod +x install.sh
./install.sh
```

## Manual

1. Install rustup from https://rustup.rs/
2. Build:

```bash
cargo build --release
```

3. Run:

```bash
cargo run --release -- --mode web
```

4. Open http://localhost:5000

