# Installation (Rust)

## Windows

### PowerShell

```powershell
.\install.ps1
```

### Command Prompt

```cmd
install.bat
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

