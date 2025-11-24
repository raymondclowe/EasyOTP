# EasyOTP - Quick Start Guide

## Installation

### Option 1: Using uv (Recommended)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone and run
git clone https://github.com/raymondclowe/EasyOTP.git
cd EasyOTP
uv sync
uv run easyotp
```

### Option 2: Using pip

```bash
git clone https://github.com/raymondclowe/EasyOTP.git
cd EasyOTP
pip install -e .
easyotp
```

### Option 3: Windows Executable (Coming Soon)

Download `EasyOTP.exe` from the [Releases](https://github.com/raymondclowe/EasyOTP/releases) page and run it directly. No installation required!

## First Launch

When you first launch EasyOTP, you'll see an empty list with a search bar at the top.

## Adding Your First OTP

1. Click the **+** button in the top right
2. Fill in the details:
   - **Name**: e.g., "GitHub", "Google", "AWS"
   - **Secret Key**: The base32 secret provided by the service
   - **Issuer** (optional): e.g., "github.com", "Google"
3. Click **Add**

### Adding from QR Code

1. Click the **+** button
2. Click **Scan QR Code**
3. Select an image file containing the QR code
4. The fields will be automatically filled
5. Click **Add**

## Using EasyOTP

### Copying a Code

**Method 1: Click**
- Simply click on any item to copy its code

**Method 2: Keyboard**
1. Use **Up/Down arrows** to select an item (it will highlight in blue)
2. Press **Enter** to copy the selected code

Both methods show a green notification confirming the copy.

### Searching

- Click in the search box (or just start typing - it has initial focus)
- Type any part of the account name or issuer
- The list filters in real-time

### Editing an Item

1. Right-click (or long-press) on an item
2. Select **Edit**
3. Modify the details
4. Click **Save**

### Deleting an Item

1. Right-click (or long-press) on an item
2. Select **Delete**
3. Confirm the deletion

### Export/Import

**Export** (Backup):
1. Click the menu button (⋮) in the top right
2. Select **Export**
3. Choose where to save the JSON file

**Import** (Restore):
1. Click the menu button (⋮) in the top right
2. Select **Import**
3. Select a previously exported JSON file
4. Items are merged with existing ones (no duplicates)

## Understanding the Display

Each OTP item shows:
- **Top Left**: Account name
- **Bottom Left**: Issuer (if provided)
- **Top Right**: Current 6-digit code (large monospace font)
- **Bottom Right**: Seconds remaining (countdown from 30 to 0)

The codes automatically regenerate every 30 seconds.

## Data Security

Your OTP secrets are stored in:
- **Windows**: `C:\Users\YourName\.easyotp\secrets.enc`
- **Linux**: `/home/yourname/.easyotp/secrets.enc`
- **macOS**: `/Users/yourname/.easyotp/secrets.enc`

The file is encrypted using:
- Your computer's hardware ID
- Your username
- PBKDF2 with 100,000 iterations
- AES encryption via Fernet

**Important**: If you move to a new computer, you must:
1. Export your items before migrating
2. Import them on the new computer

The encrypted file will NOT work on a different machine or user account.

## Troubleshooting

### QR Code Scanning Not Working

QR code scanning requires the `zbar` library:

**Ubuntu/Debian:**
```bash
sudo apt-get install libzbar0
```

**macOS:**
```bash
brew install zbar
```

**Windows:**
Download from [zbar project](http://zbar.sourceforge.net/) or use manual secret entry.

### Application Won't Start

Ensure all dependencies are installed:
```bash
uv sync
# or
pip install -e .
```

### Can't Copy to Clipboard

The application uses `pyperclip`. On Linux, you may need:
```bash
sudo apt-get install xclip  # or xsel
```

## Tips

- **Keep it running**: Leave EasyOTP open for quick access to codes
- **Export regularly**: Back up your items periodically
- **Unique names**: Use descriptive names to find items quickly
- **Search shortcut**: Just start typing to filter items
- **Keyboard navigation**: Use arrow keys for hands-free operation

## Getting Help

- Report issues: [GitHub Issues](https://github.com/raymondclowe/EasyOTP/issues)
- Read the docs: [README.md](README.md)
- UI design: [UI_DESIGN.md](UI_DESIGN.md)

## Building from Source

See [README.md](README.md) for detailed build instructions including creating Windows executables with PyInstaller.
