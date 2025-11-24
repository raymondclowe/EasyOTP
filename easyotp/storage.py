"""Storage module for encrypted OTP secrets."""
import json
import os
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class OTPItem:
    """Represents an OTP item."""
    
    def __init__(self, name: str, secret: str, issuer: str = ""):
        self.name = name
        self.secret = secret
        self.issuer = issuer
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "secret": self.secret,
            "issuer": self.issuer
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "OTPItem":
        return cls(
            name=data["name"],
            secret=data["secret"],
            issuer=data.get("issuer", "")
        )


class Storage:
    """Manages encrypted storage of OTP items."""
    
    def __init__(self):
        self.storage_path = Path.home() / ".easyotp" / "secrets.enc"
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._encryption_key = self._get_encryption_key()
        self._fernet = Fernet(self._encryption_key)
    
    def _get_hwid(self) -> str:
        """Get hardware ID based on the operating system."""
        system = platform.system()
        
        try:
            if system == "Windows":
                # Use wmic to get the machine GUID
                result = subprocess.run(
                    ["wmic", "csproduct", "get", "UUID"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    return lines[1].strip()
            elif system == "Linux":
                # Try to read machine-id
                machine_id_path = Path("/etc/machine-id")
                if machine_id_path.exists():
                    return machine_id_path.read_text().strip()
                # Fallback to dbus machine-id
                dbus_id_path = Path("/var/lib/dbus/machine-id")
                if dbus_id_path.exists():
                    return dbus_id_path.read_text().strip()
            elif system == "Darwin":  # macOS
                result = subprocess.run(
                    ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        return line.split('"')[3]
        except Exception:
            pass
        
        # Fallback: use hostname
        return platform.node()
    
    def _get_username(self) -> str:
        """Get the current username."""
        try:
            if hasattr(os, 'getlogin'):
                return os.getlogin()
        except (FileNotFoundError, OSError):
            pass
        return os.environ.get('USER', os.environ.get('USERNAME', 'default'))
    
    def _get_encryption_key(self) -> bytes:
        """Generate encryption key based on HWID and username."""
        hwid = self._get_hwid()
        username = self._get_username()
        
        # Combine HWID and username as the basis for the key
        password = f"{hwid}:{username}".encode()
        
        # Use a fixed salt (this is acceptable since the password itself is machine+user specific)
        salt = b"easyotp_salt_v1"
        
        # Derive a key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password)
        
        # Convert to Fernet-compatible format
        import base64
        return base64.urlsafe_b64encode(key)
    
    def load_items(self) -> List[OTPItem]:
        """Load OTP items from encrypted storage."""
        if not self.storage_path.exists():
            return []
        
        try:
            encrypted_data = self.storage_path.read_bytes()
            decrypted_data = self._fernet.decrypt(encrypted_data)
            items_data = json.loads(decrypted_data.decode())
            return [OTPItem.from_dict(item) for item in items_data]
        except Exception as e:
            # If decryption fails (wrong machine/user), return empty list
            print(f"Failed to load items: {e}")
            return []
    
    def save_items(self, items: List[OTPItem]):
        """Save OTP items to encrypted storage."""
        items_data = [item.to_dict() for item in items]
        json_data = json.dumps(items_data, indent=2)
        encrypted_data = self._fernet.encrypt(json_data.encode())
        self.storage_path.write_bytes(encrypted_data)
    
    def add_item(self, item: OTPItem):
        """Add a new OTP item."""
        items = self.load_items()
        items.append(item)
        self.save_items(items)
    
    def delete_item(self, name: str):
        """Delete an OTP item by name."""
        items = self.load_items()
        items = [item for item in items if item.name != name]
        self.save_items(items)
    
    def update_item(self, old_name: str, new_item: OTPItem):
        """Update an existing OTP item."""
        items = self.load_items()
        for i, item in enumerate(items):
            if item.name == old_name:
                items[i] = new_item
                break
        self.save_items(items)
    
    def export_to_json(self, filepath: str):
        """Export items to unencrypted JSON file."""
        items = self.load_items()
        items_data = [item.to_dict() for item in items]
        with open(filepath, 'w') as f:
            json.dump(items_data, f, indent=2)
    
    def import_from_json(self, filepath: str):
        """Import items from unencrypted JSON file."""
        with open(filepath, 'r') as f:
            items_data = json.load(f)
        new_items = [OTPItem.from_dict(item) for item in items_data]
        
        # Merge with existing items (avoid duplicates by name)
        existing_items = self.load_items()
        existing_names = {item.name for item in existing_items}
        
        for item in new_items:
            if item.name not in existing_names:
                existing_items.append(item)
        
        self.save_items(existing_items)
