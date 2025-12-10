# EasyOTP

A simple Timed OTP (TOTP) application in Python and Flet (Flutter-like UI) because I don't like any other ones I've found.

## Features

- ✨ **Clean, intuitive UI** - Built with Flet for a modern, responsive interface
- 🔐 **Secure storage** - Secrets encrypted using PC HWID + username (file only works on that specific PC/user)
- 📱 **Add items** - Support for manual secret entry or QR code scanning
- 🔍 **Real-time search** - Instant filtering with search box (initial focus)
- ⌨️ **Keyboard navigation** - Use arrow keys to navigate, Enter to copy
- 🖱️ **Click to copy** - One-click copying of OTP codes
- ✏️ **Edit items** - Right-click context menu for editing
- 📤 **Export/Import** - Backup and restore your OTP items
- ⏱️ **Live countdown** - See remaining time for each code

## Installation

## Windows Executable

### Downloading Pre-built Releases (recommended)

Pre-built Windows executables are available from the [Releases](https://github.com/raymondclowe/EasyOTP/releases) page. The executable is self-signed with a certificate specific to this project.

> **Note:** macOS, Linux `.deb`, and Raspberry Pi (arm64) archives are now published alongside the Windows build. These additional binaries are produced automatically and have **not** been manually tested on real hardware; treat them as experimental and prefer building from source if you need a verified release on those platforms.

#### Security Options

Since the executable is self-signed (not from a commercial Certificate Authority), Windows SmartScreen will show a warning.

### Using uv (for development or you don't trust the prebuilt releases)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/raymondclowe/EasyOTP.git
cd EasyOTP

# Install dependencies
uv sync

# Run the application
uv run easyotp
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/raymondclowe/EasyOTP.git
cd EasyOTP

# Install the package
pip install -e .

# Run the application
easyotp
```

## Usage

### Adding an OTP Item

1. Click the **+** button
2. Enter the account name and secret key
3. Optionally add an issuer name
4. Or click "Scan QR Code" to import from an image

### Copying a Code

- **Click** on any item to copy its code
- **Arrow keys** to navigate + **Enter** to copy
- **Search box** filters items in real-time

### Editing an Item

- **Right-click** (or long-press) on an item
- Select "Edit" from the menu
- Update the details and save

### Export/Import

- Click the **menu button** (⋮) in the top bar
- Select "Export" to save items to a JSON file
- Select "Import" to restore items from a backup

## Windows Executable

### Downloading Pre-built Releases

Pre-built Windows executables are available from the [Releases](https://github.com/raymondclowe/EasyOTP/releases) page. The executable is self-signed with a certificate specific to this project.

> **Note:** macOS, Linux `.deb`, and Raspberry Pi (arm64) archives are now published alongside the Windows build. These additional binaries are produced automatically and have **not** been manually tested on real hardware; treat them as experimental and prefer building from source if you need a verified release on those platforms.

#### Security Options

Since the executable is self-signed (not from a commercial Certificate Authority), Windows SmartScreen will show a warning. You have several options:

1. **Run as Python** (Most Secure)
   - Follow the installation instructions above to run from source
   - You can review all the code before running

2. **Build It Yourself**
   - Follow the manual build instructions below
   - Ensures you're running exactly what you compiled

3. **Trust the Certificate** (Recommended if you trust this project)
   - Download and install [EasyOTP.cer](EasyOTP.cer)
   - Right-click the file → "Install Certificate"
   - Choose "Local Machine" → "Place all certificates in the following store"
   - Select "Trusted Root Certification Authorities"
   - This tells Windows to trust executables signed with this certificate
   - **Note**: Only do this if you trust this project and its maintainer

4. **Click "Run Anyway"**
   - When Windows SmartScreen blocks the app, click "More info" → "Run anyway"
   - You'll need to do this each time you download a new version

#### Verifying the Signature

To verify the executable is properly signed:
1. Right-click `EasyOTP.exe` → Properties → Digital Signatures
2. You should see a signature from "EasyOTP" with details:
   - Organization: Raymond Clowe
   - Organizational Unit: Github: raymondclowe
   - Location: Hong Kong
3. The certificate thumbprint should be: `F81508B5807D93C1C278B5A35D73D1F381D5F3D0`

### Manual Build (Windows)

1. **Activate your virtual environment** (if not already active):
	```powershell
	.venv\Scripts\Activate.ps1
	```
2. **Install PyInstaller** (if not already installed):
	```powershell
	pip install pyinstaller
	```
3. **Build the executable**:
	```powershell
	python -m PyInstaller --name=EasyOTP --onefile --windowed easyotp/main.py
	```
4. **Find the executable** in:
	```
	dist/EasyOTP.exe
	```

You can now distribute or run `EasyOTP.exe` on Windows without requiring Python to be installed.

## Security

- Secrets are stored in `~/.easyotp/secrets.enc`
- Encryption uses **PBKDF2** with 100,000 iterations
- Key derived from **PC Hardware ID + Username**
- Encrypted files are **machine and user specific**
- If you move to a new PC, you'll need to export/import your items

## Requirements

- Python 3.8+
- flet >= 0.24.0
- pyotp >= 2.9.0
- cryptography >= 42.0.0
- pyperclip >= 1.9.0
- pillow >= 10.0.0
- pyzbar >= 0.1.9 (optional, for QR code scanning)

## Development

```bash
# Run tests
python test_basic.py

# Run with uv
uv run easyotp

# Format code (if using ruff)
ruff format .
```

## License

MIT License - See LICENSE file for details

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

