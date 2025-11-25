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

### Using uv (recommended)

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

## Building Windows Executable

The repository includes a GitHub Actions workflow that automatically builds a Windows executable using PyInstaller.

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

